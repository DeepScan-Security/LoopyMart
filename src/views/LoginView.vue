<script setup>
import { ref } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { auth } from '@/api'

const route = useRoute()
const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await auth.login({ email: email.value, password: password.value })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    try {
      const cartRes = await (await import('@/api')).cart.list()
      const count = cartRes.data.reduce((s, i) => s + i.quantity, 0)
      sessionStorage.setItem('cartCount', String(count))
    } catch (_) {
      sessionStorage.setItem('cartCount', '0')
    }
    const redirect = route.query.redirect || '/'
    window.location.href = redirect
  } catch (e) {
    error.value = e.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-loopymart-gray flex items-center justify-center py-8 px-4">
    <div class="w-full max-w-4xl bg-white shadow-card rounded-sm overflow-hidden flex">
      <!-- Left Panel - Blue Section -->
      <div class="hidden md:flex w-[40%] bg-loopymart-blue p-10 flex-col justify-between">
        <div>
          <h1 class="text-3xl font-bold text-white mb-4">Login</h1>
          <p class="text-white/80 text-lg leading-relaxed">
            Get access to your Orders, Wishlist and Recommendations
          </p>
        </div>
        <div class="mt-auto">
          <svg width="192" height="192" class="w-48 h-48 mx-auto text-white/20" viewBox="0 0 200 200" fill="currentColor">
            <circle cx="100" cy="70" r="45" />
            <path d="M30,200 Q30,130 100,130 Q170,130 170,200" />
          </svg>
        </div>
      </div>

      <!-- Right Panel - Form Section -->
      <div class="flex-1 p-8 md:p-10">
        <!-- Mobile Header -->
        <div class="md:hidden text-center mb-8">
          <h1 class="text-2xl font-bold text-loopymart-blue mb-2">Login</h1>
          <p class="text-text-secondary text-sm">
            Get access to your Orders, Wishlist and Recommendations
          </p>
        </div>

        <form @submit.prevent="submit" class="space-y-6">
          <!-- Email Field -->
          <div>
            <label for="email" class="block text-sm text-text-secondary mb-2">
              Enter Email
            </label>
            <input
              id="email"
              v-model="email"
              type="email"
              required
              class="w-full px-0 py-2 border-0 border-b-2 border-loopymart-gray-dark 
                     focus:border-loopymart-blue focus:ring-0 text-text-primary
                     placeholder:text-text-hint transition-colors"
              placeholder="Enter your email"
            />
          </div>

          <!-- Password Field -->
          <div>
            <label for="password" class="block text-sm text-text-secondary mb-2">
              Enter Password
            </label>
            <div class="relative">
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                class="w-full px-0 py-2 border-0 border-b-2 border-loopymart-gray-dark 
                       focus:border-loopymart-blue focus:ring-0 text-text-primary
                       placeholder:text-text-hint transition-colors pr-10"
                placeholder="Enter your password"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-0 top-1/2 -translate-y-1/2 text-text-secondary 
                       hover:text-loopymart-blue"
              >
                <svg v-if="showPassword" width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" 
                     viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
                <svg v-else width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Terms Text -->
          <p class="text-xs text-text-secondary">
            By continuing, you agree to LoopyMart's 
            <a href="#" class="text-loopymart-blue hover:underline">Terms of Use</a> and 
            <a href="#" class="text-loopymart-blue hover:underline">Privacy Policy</a>.
          </p>

          <!-- Error Message -->
          <div 
            v-if="error" 
            class="p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm"
          >
            {{ error }}
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3 bg-loopymart-orange text-white font-medium rounded-sm
                   hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {{ loading ? 'Logging in...' : 'Login' }}
          </button>

          <!-- OR Divider -->
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-loopymart-gray-dark"></div>
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-4 bg-white text-text-secondary">OR</span>
            </div>
          </div>

          <!-- OTP Login (Demo) -->
          <button
            type="button"
            class="w-full py-3 border border-loopymart-gray-dark text-loopymart-blue 
                   font-medium rounded-sm hover:bg-loopymart-gray transition-colors"
          >
            Request OTP
          </button>

          <!-- Forgot Password Link -->
          <div class="text-center">
            <RouterLink 
              to="/forgot-password" 
              class="text-sm text-loopymart-blue hover:underline"
            >
              Forgot Password?
            </RouterLink>
          </div>
        </form>

        <!-- Register Link -->
        <div class="mt-8 pt-6 border-t border-loopymart-gray-dark text-center">
          <p class="text-text-secondary">
            New to LoopyMart? 
            <RouterLink 
              to="/register" 
              class="text-loopymart-blue font-medium hover:underline"
            >
              Create an account
            </RouterLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
