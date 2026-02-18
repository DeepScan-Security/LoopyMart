<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import client from '@/api/client'

const loading = ref(true)
const error = ref('')
const success = ref('')
const redeeming = ref(false)
const purchasing = ref(false)

// Wallet data
const balance = ref(0)
const pendingCashback = ref(0)

// Flag store
const flagStoreItems = ref([])
const purchasedFlag = ref(null)

// Active section
const activeSection = ref('balance')

async function loadWallet() {
  try {
    const res = await client.get('/wallet')
    balance.value = res.data.balance
    pendingCashback.value = res.data.pending_cashback
  } catch (e) {
    error.value = 'Failed to load wallet data'
  }
}

async function loadFlagStore() {
  try {
    const res = await client.get('/wallet/flag-store')
    flagStoreItems.value = res.data.items
  } catch (e) {
    console.error('Failed to load flag store:', e)
  }
}

onMounted(async () => {
  try {
    await Promise.all([loadWallet(), loadFlagStore()])
  } finally {
    loading.value = false
  }
})

async function redeemCashback() {
  if (redeeming.value || pendingCashback.value <= 0) return
  
  redeeming.value = true
  error.value = ''
  success.value = ''
  
  try {
    const res = await client.post('/wallet/redeem')
    balance.value = res.data.new_balance
    pendingCashback.value = 0
    success.value = `Successfully redeemed ₹${res.data.amount_redeemed.toFixed(2)} to your wallet!`
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to redeem cashback'
  } finally {
    redeeming.value = false
    await loadWallet()
  }
}

async function purchaseItem(itemId) {
  if (purchasing.value) return
  
  purchasing.value = true
  error.value = ''
  success.value = ''
  purchasedFlag.value = null
  
  try {
    const res = await client.post('/wallet/purchase-flag', { item_id: itemId })
    
    if (res.data.success) {
      purchasedFlag.value = res.data.flag
      balance.value = res.data.new_balance
      success.value = 'Purchase successful! Check below for your reward.'
    } else {
      error.value = res.data.message
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Purchase failed'
  } finally {
    purchasing.value = false
  }
}

const sections = [
  { id: 'balance', label: 'Wallet Balance', icon: 'wallet' },
  { id: 'redeem', label: 'Redeem Cashback', icon: 'gift' },
  { id: 'store', label: 'Rewards Store', icon: 'store' },
]
</script>

<template>
  <div class="min-h-screen bg-loopymart-gray py-4">
    <div class="max-w-container mx-auto px-4">
      <!-- Loading -->
      <div v-if="loading" class="bg-white shadow-card rounded-sm p-12 text-center">
        <div class="inline-block w-8 h-8 border-4 border-loopymart-blue border-t-transparent 
                    rounded-full animate-spin"></div>
        <p class="mt-4 text-text-secondary">Loading wallet...</p>
      </div>

      <div v-else class="flex flex-col lg:flex-row gap-4">
        <!-- Left Sidebar -->
        <aside class="lg:w-72 flex-shrink-0">
          <!-- Wallet Summary Card -->
          <div class="bg-white shadow-card rounded-sm p-4 mb-4">
            <div class="flex items-center gap-4">
              <div class="w-14 h-14 flex-shrink-0 bg-loopymart-blue text-white rounded-full 
                          flex items-center justify-center">
                <svg width="24" height="24" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
                </svg>
              </div>
              <div>
                <p class="text-xs text-text-secondary">Wallet Balance</p>
                <p class="text-xl font-bold text-loopymart-blue">
                  ₹{{ balance.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </p>
              </div>
            </div>
            
            <!-- Pending Cashback -->
            <div class="mt-4 pt-4 border-t border-loopymart-gray-dark">
              <div class="flex items-center justify-between">
                <span class="text-sm text-text-secondary">Pending Cashback</span>
                <span class="text-sm font-medium text-loopymart-orange">
                  ₹{{ pendingCashback.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Navigation -->
          <nav class="bg-white shadow-card rounded-sm overflow-hidden">
            <button
              v-for="section in sections"
              :key="section.id"
              @click="activeSection = section.id"
              :class="[
                'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
                activeSection === section.id 
                  ? 'bg-loopymart-gray border-l-4 border-loopymart-blue text-loopymart-blue' 
                  : 'text-text-primary hover:bg-loopymart-gray border-l-4 border-transparent'
              ]"
            >
              <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="section.icon === 'wallet'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
                <path v-if="section.icon === 'gift'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"/>
                <path v-if="section.icon === 'store'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/>
              </svg>
              <span class="text-sm font-medium">{{ section.label }}</span>
            </button>
          </nav>

          <!-- Quick Links -->
          <div class="bg-white shadow-card rounded-sm mt-4 p-4">
            <h3 class="text-xs font-medium text-text-secondary uppercase mb-3">Quick Links</h3>
            <div class="space-y-2">
              <RouterLink to="/orders" class="flex items-center gap-2 text-sm text-text-primary hover:text-loopymart-blue">
                <svg width="16" height="16" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                </svg>
                My Orders
              </RouterLink>
              <RouterLink to="/products" class="flex items-center gap-2 text-sm text-text-primary hover:text-loopymart-blue">
                <svg width="16" height="16" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
                </svg>
                Shop Now
              </RouterLink>
            </div>
          </div>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 min-w-0">
          <!-- Messages -->
          <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm">
            {{ error }}
          </div>
          <div v-if="success" class="mb-4 p-3 bg-green-50 border border-loopymart-green rounded-sm text-loopymart-green text-sm">
            {{ success }}
          </div>

          <!-- Balance Section -->
          <div v-if="activeSection === 'balance'" class="bg-white shadow-card rounded-sm">
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h2 class="font-medium text-text-primary">Wallet Overview</h2>
            </div>
            <div class="p-6">
              <!-- Balance Cards -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div class="p-4 bg-loopymart-gray rounded-sm">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-loopymart-blue/10 rounded-full flex items-center justify-center">
                      <svg width="20" height="20" class="w-5 h-5 text-loopymart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                    </div>
                    <div>
                      <p class="text-sm text-text-secondary">Available Balance</p>
                      <p class="text-2xl font-bold text-text-primary">
                        ₹{{ balance.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                      </p>
                    </div>
                  </div>
                </div>

                <div class="p-4 bg-loopymart-gray rounded-sm">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-loopymart-orange/10 rounded-full flex items-center justify-center">
                      <svg width="20" height="20" class="w-5 h-5 text-loopymart-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"/>
                      </svg>
                    </div>
                    <div>
                      <p class="text-sm text-text-secondary">Pending Cashback</p>
                      <p class="text-2xl font-bold text-loopymart-orange">
                        ₹{{ pendingCashback.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Info -->
              <div class="p-4 bg-blue-50 border border-blue-100 rounded-sm">
                <h3 class="font-medium text-loopymart-blue mb-2">How to earn cashback</h3>
                <ul class="text-sm text-text-secondary space-y-1">
                  <li class="flex items-start gap-2">
                    <span class="text-loopymart-green mt-0.5">✓</span>
                    Place orders to earn 5% cashback (up to ₹50 per order)
                  </li>
                  <li class="flex items-start gap-2">
                    <span class="text-loopymart-green mt-0.5">✓</span>
                    Redeem pending cashback to add it to your wallet
                  </li>
                  <li class="flex items-start gap-2">
                    <span class="text-loopymart-green mt-0.5">✓</span>
                    Use wallet balance for purchases
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Redeem Section -->
          <div v-if="activeSection === 'redeem'" class="bg-white shadow-card rounded-sm">
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h2 class="font-medium text-text-primary">Redeem Cashback</h2>
            </div>
            <div class="p-6">
              <div class="max-w-md">
                <div class="p-4 bg-loopymart-gray rounded-sm mb-6">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm text-text-secondary">Available to Redeem</span>
                    <span class="text-lg font-bold text-loopymart-orange">
                      ₹{{ pendingCashback.toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                    </span>
                  </div>
                  <div class="w-full bg-loopymart-gray-dark rounded-full h-2">
                    <div 
                      class="bg-loopymart-orange h-2 rounded-full transition-all"
                      :style="{ width: pendingCashback > 0 ? '100%' : '0%' }"
                    ></div>
                  </div>
                </div>

                <p class="text-sm text-text-secondary mb-4">
                  Transfer your pending cashback to your wallet balance instantly. 
                  Your cashback will be added to your available balance and can be used for purchases.
                </p>

                <button
                  @click="redeemCashback"
                  :disabled="redeeming || pendingCashback <= 0"
                  class="btn btn-primary"
                >
                  <span v-if="redeeming" class="inline-block w-4 h-4 border-2 border-white border-t-transparent 
                              rounded-full animate-spin mr-2"></span>
                  {{ redeeming ? 'Redeeming...' : 'Redeem Now' }}
                </button>

                <p v-if="pendingCashback <= 0" class="mt-4 text-sm text-text-hint">
                  No pending cashback available. Place an order to earn cashback!
                </p>
              </div>
            </div>
          </div>

          <!-- Store Section -->
          <div v-if="activeSection === 'store'" class="bg-white shadow-card rounded-sm">
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h2 class="font-medium text-text-primary">Rewards Store</h2>
            </div>
            <div class="p-6">
              <p class="text-sm text-text-secondary mb-6">
                Use your wallet balance to purchase exclusive rewards.
              </p>

              <!-- Store Items -->
              <div class="space-y-4">
                <div 
                  v-for="item in flagStoreItems" 
                  :key="item.id"
                  class="flex items-center gap-4 p-4 border border-loopymart-gray-dark rounded-sm 
                         hover:border-loopymart-blue transition-colors"
                >
                  <div class="w-16 h-16 bg-loopymart-gray rounded-sm flex items-center justify-center flex-shrink-0">
                    <svg width="32" height="32" class="w-8 h-8 text-loopymart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"/>
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <h3 class="font-medium text-text-primary">{{ item.name }}</h3>
                    <p class="text-sm text-text-secondary mt-1">{{ item.description }}</p>
                    <div class="flex items-center gap-4 mt-2">
                      <span class="text-lg font-bold text-loopymart-blue">
                        ₹{{ item.price.toLocaleString('en-IN') }}
                      </span>
                      <span v-if="balance < item.price" class="text-xs text-red-500">
                        Need ₹{{ (item.price - balance).toLocaleString('en-IN') }} more
                      </span>
                    </div>
                  </div>
                  <button
                    @click="purchaseItem(item.id)"
                    :disabled="purchasing || balance < item.price"
                    :class="[
                      'btn whitespace-nowrap',
                      balance >= item.price ? 'btn-primary' : 'bg-loopymart-gray text-text-hint cursor-not-allowed'
                    ]"
                  >
                    {{ purchasing ? 'Processing...' : balance >= item.price ? 'Purchase' : 'Insufficient Balance' }}
                  </button>
                </div>
              </div>

              <!-- Purchased Flag Display -->
              <div v-if="purchasedFlag" class="mt-6 p-6 bg-green-50 border border-loopymart-green rounded-sm text-center">
                <div class="w-16 h-16 bg-loopymart-green/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg width="32" height="32" class="w-8 h-8 text-loopymart-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </div>
                <h3 class="text-lg font-bold text-loopymart-green mb-2">Congratulations!</h3>
                <p class="text-sm text-text-secondary mb-4">You've unlocked the secret reward!</p>
                <div class="inline-block px-6 py-3 bg-white border-2 border-dashed border-loopymart-green rounded-sm">
                  <code class="text-lg font-mono font-bold text-text-primary">{{ purchasedFlag }}</code>
                </div>
              </div>

              <!-- Hint -->
              <div class="mt-6 p-4 bg-loopymart-gray rounded-sm">
                <p class="text-xs text-text-hint">
                  <strong>Hint:</strong> The exclusive reward costs ₹200, but you start with only ₹100 + ₹50 cashback. 
                  Can you figure out how to get enough balance?
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>
