#!/usr/bin/env node
/**
 * LoopyMart CTF — Puppeteer Cookie Exfiltration Solver
 *
 * Uses Puppeteer to:
 *   1. Log in as admin via POST /auth/login
 *   2. Call POST /ctf/mock-flag-cookie with the admin JWT
 *   3. Read the `mock_flag` cookie from the browser context
 *   4. Confirm it is also readable via document.cookie (not HttpOnly)
 *   5. Print the flag and exit 0
 *
 * Usage:
 *   npm install
 *   node solve.js --email admin@example.com --password secret
 *   node solve.js --email admin@example.com --password secret --url http://localhost:8001
 */

const puppeteer = require('puppeteer')

// ── CLI args ──────────────────────────────────────────────────────
const args = process.argv.slice(2)

function getArg(name, defaultValue = undefined) {
  const idx = args.indexOf(name)
  if (idx !== -1 && args[idx + 1]) return args[idx + 1]
  if (defaultValue !== undefined) return defaultValue
  console.error(`[-] Missing required argument: ${name}`)
  process.exit(1)
}

const BASE_URL = getArg('--url', 'http://localhost:8001')
const EMAIL    = getArg('--email')
const PASSWORD = getArg('--password')

// ── Main ──────────────────────────────────────────────────────────
;(async () => {
  let browser
  try {
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    })
    const page = await browser.newPage()

    // ── Step 1: Login via fetch inside browser context ──────────────
    console.log(`[*] Logging in as ${EMAIL} …`)
    const loginResult = await page.evaluate(async (baseUrl, email, password) => {
      const res = await fetch(`${baseUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      return { status: res.status, data }
    }, BASE_URL, EMAIL, PASSWORD)

    if (loginResult.status !== 200 || !loginResult.data.access_token) {
      console.error(`[-] Login failed (HTTP ${loginResult.status}):`, JSON.stringify(loginResult.data))
      process.exit(1)
    }

    const token = loginResult.data.access_token
    const isAdmin = loginResult.data.user?.is_admin
    console.log(`[+] Logged in successfully  (is_admin=${isAdmin})`)

    if (!isAdmin) {
      console.error('[-] User is not admin — endpoint will return 403.')
      console.error('    Use the admin account configured in config.local.yml / ADMIN_EMAIL env var.')
      process.exit(1)
    }

    // ── Step 2: Call POST /ctf/mock-flag-cookie ─────────────────────
    console.log('[*] Calling POST /ctf/mock-flag-cookie …')
    const ctfResult = await page.evaluate(async (baseUrl, bearerToken) => {
      const res = await fetch(`${baseUrl}/ctf/mock-flag-cookie`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${bearerToken}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',   // ensure cookies are stored in the browser context
      })
      const data = await res.json()
      return { status: res.status, data }
    }, BASE_URL, token)

    if (ctfResult.status !== 200) {
      console.error(`[-] Endpoint returned HTTP ${ctfResult.status}:`, JSON.stringify(ctfResult.data))
      process.exit(1)
    }

    const flagFromJson = ctfResult.data.flag
    console.log(`[+] JSON response flag  : ${flagFromJson}`)

    // ── Step 3: Read cookie from browser context ────────────────────
    // Navigate to the origin so page.cookies() picks up the domain cookies
    await page.goto(BASE_URL, { waitUntil: 'networkidle2' }).catch(() => {
      // 404/redirect is fine — we just need the browser to set origin
    })

    const cookies = await page.cookies(BASE_URL)
    const mockFlagCookie = cookies.find(c => c.name === 'mock_flag')

    if (!mockFlagCookie) {
      console.warn('[!] `mock_flag` cookie not found in Puppeteer page.cookies().')
      console.warn('    This can happen when the backend runs on a different origin.')
      console.warn('    Flag was already captured from JSON body above.')
    } else {
      console.log(`[+] Cookie `mock_flag` value : ${mockFlagCookie.value}`)
      console.log(`    httpOnly : ${mockFlagCookie.httpOnly}  (should be false — JS-readable)`)
      console.log(`    secure   : ${mockFlagCookie.secure}    (should be false — CTF demo)`)
    }

    // ── Step 4: Confirm JS-readable via document.cookie ────────────
    const docCookie = await page.evaluate(() => document.cookie)
    const jsCookies = Object.fromEntries(
      docCookie.split(';').map(s => s.trim().split('=').map(decodeURIComponent))
    )
    if (jsCookies.mock_flag) {
      console.log(`[+] document.cookie confirms JS-readable: mock_flag=${jsCookies.mock_flag}`)
    }

    // ── Done ────────────────────────────────────────────────────────
    const flag = mockFlagCookie?.value || jsCookies.mock_flag || flagFromJson
    if (flag) {
      console.log(`\n[+] Flag: ${flag}`)
      process.exit(0)
    } else {
      console.error('[-] Could not extract flag.')
      process.exit(1)
    }
  } catch (err) {
    console.error('[-] Unexpected error:', err.message)
    process.exit(1)
  } finally {
    if (browser) await browser.close()
  }
})()
