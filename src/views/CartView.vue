<script setup>
import { ref, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { cart } from '@/api'

const items = ref([])
const loading = ref(true)
const updating = ref(null)

onMounted(async () => {
  try {
    const res = await cart.list()
    items.value = res.data
  } catch (_) {
    items.value = []
  } finally {
    loading.value = false
  }
})

const subtotal = computed(() =>
  items.value.reduce((s, i) => s + i.product_price * i.quantity, 0)
)

const totalItems = computed(() =>
  items.value.reduce((s, i) => s + i.quantity, 0)
)

const discount = computed(() => Math.round(subtotal.value * 0.1))
const deliveryCharges = computed(() => subtotal.value > 499 ? 0 : 40)
const total = computed(() => subtotal.value - discount.value + deliveryCharges.value)

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  const staticUrl = import.meta.env.VITE_STATIC_URL || ''
  if (url.startsWith('/static/')) return staticUrl + url
  return url
}

async function updateQty(item, delta) {
  const newQty = Math.max(0, Math.min(item.product_stock, item.quantity + delta))
  if (newQty === item.quantity) return
  updating.value = item.id
  try {
    if (newQty === 0) {
      await cart.remove(item.id)
      items.value = items.value.filter((i) => i.id !== item.id)
    } else {
      const res = await cart.update(item.id, { quantity: newQty })
      const idx = items.value.findIndex((i) => i.id === item.id)
      if (idx !== -1) items.value[idx] = res.data
    }
    const count = items.value.reduce((s, i) => s + i.quantity, 0)
    sessionStorage.setItem('cartCount', String(count))
  } catch (_) {}
  finally {
    updating.value = null
  }
}

async function remove(item) {
  updating.value = item.id
  try {
    await cart.remove(item.id)
    items.value = items.value.filter((i) => i.id !== item.id)
    const count = items.value.reduce((s, i) => s + i.quantity, 0)
    sessionStorage.setItem('cartCount', String(count))
  } catch (_) {}
  finally {
    updating.value = null
  }
}
</script>

<template>
  <div class="min-h-screen bg-flipkart-gray py-4">
    <div class="max-w-container mx-auto px-4">
      <!-- Loading State -->
      <div v-if="loading" class="bg-white shadow-card rounded-sm p-12 text-center">
        <div class="inline-block w-8 h-8 border-4 border-flipkart-blue border-t-transparent 
                    rounded-full animate-spin"></div>
        <p class="mt-4 text-text-secondary">Loading your cart...</p>
      </div>

      <!-- Empty Cart -->
      <div v-else-if="!items.length" class="bg-white shadow-card rounded-sm p-12 text-center">
        <svg width="96" height="96" class="w-24 h-24 mx-auto text-text-hint mb-4" fill="none" stroke="currentColor" 
             viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" 
                d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
        </svg>
        <h2 class="text-xl font-medium text-text-primary mb-2">Your cart is empty!</h2>
        <p class="text-text-secondary mb-6">Add items to it now.</p>
        <RouterLink to="/products" class="btn btn-primary btn-lg">
          Shop Now
        </RouterLink>
      </div>

      <!-- Cart Content -->
      <div v-else class="flex flex-col lg:flex-row gap-4">
        <!-- Left Column - Cart Items -->
        <div class="flex-1 min-w-0">
          <!-- Cart Header -->
          <div class="bg-white shadow-card rounded-sm mb-2">
            <div class="p-4 border-b border-flipkart-gray-dark">
              <h1 class="text-lg font-medium text-text-primary">
                My Cart ({{ totalItems }} {{ totalItems === 1 ? 'item' : 'items' }})
              </h1>
            </div>

            <!-- Delivery Location -->
            <div class="p-4 flex items-center gap-3 border-b border-flipkart-gray-dark">
              <svg width="20" height="20" class="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" 
                   viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              <span class="text-sm text-text-primary">
                Deliver to: <span class="font-medium">Your Location</span>
              </span>
              <button class="ml-auto text-sm text-flipkart-blue font-medium hover:underline">
                Change
              </button>
            </div>
          </div>

          <!-- Cart Items List -->
          <div class="bg-white shadow-card rounded-sm">
            <div 
              v-for="(item, index) in items" 
              :key="item.id"
              :class="[
                'p-4',
                index !== items.length - 1 ? 'border-b border-flipkart-gray-dark' : ''
              ]"
            >
              <div class="flex gap-4">
                <!-- Product Image -->
                <RouterLink 
                  :to="{ name: 'ProductDetail', params: { id: item.product_id } }"
                  class="w-28 h-28 flex-shrink-0 bg-white border border-flipkart-gray-dark 
                         rounded-sm p-2"
                >
                  <img
                    :src="imageUrl(item.product_image_url)"
                    :alt="item.product_name"
                    class="w-full h-full object-contain"
                  />
                </RouterLink>

                <!-- Product Details -->
                <div class="flex-1 min-w-0">
                  <RouterLink 
                    :to="{ name: 'ProductDetail', params: { id: item.product_id } }"
                    class="text-text-primary hover:text-flipkart-blue transition-colors"
                  >
                    <h3 class="font-medium line-clamp-2">{{ item.product_name }}</h3>
                  </RouterLink>

                  <!-- Seller Info -->
                  <p class="text-xs text-text-secondary mt-1">
                    Seller: Clipkart
                    <span class="ml-1 inline-flex items-center">
                      <svg width="40" height="12" class="w-10 h-3" viewBox="0 0 40 12">
                        <rect width="40" height="12" rx="2" fill="#2874f0"/>
                        <text x="3" y="9" fill="white" font-size="7" font-weight="500">ASSURED</text>
                      </svg>
                    </span>
                  </p>

                  <!-- Price -->
                  <div class="flex items-center gap-2 mt-2">
                    <span class="text-lg font-medium text-text-primary">
                      ₹{{ item.product_price.toLocaleString('en-IN') }}
                    </span>
                    <span class="text-sm text-text-secondary line-through">
                      ₹{{ Math.round(item.product_price * 1.3).toLocaleString('en-IN') }}
                    </span>
                    <span class="text-sm text-flipkart-green font-medium">
                      23% off
                    </span>
                  </div>

                  <!-- Delivery Info -->
                  <p class="text-xs text-text-secondary mt-2">
                    Delivery by Tomorrow | 
                    <span class="text-flipkart-green">Free</span>
                  </p>
                </div>
              </div>

              <!-- Actions Row -->
              <div class="flex items-center gap-4 mt-4 ml-32">
                <!-- Quantity Controls -->
                <div class="flex items-center">
                  <button
                    @click="updateQty(item, -1)"
                    :disabled="updating === item.id || item.quantity <= 1"
                    class="w-8 h-8 flex items-center justify-center rounded-full border 
                           border-flipkart-gray-dark hover:border-flipkart-blue 
                           disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <svg width="16" height="16" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"/>
                    </svg>
                  </button>
                  <span class="w-12 text-center font-medium text-text-primary">
                    {{ item.quantity }}
                  </span>
                  <button
                    @click="updateQty(item, 1)"
                    :disabled="updating === item.id || item.quantity >= item.product_stock"
                    class="w-8 h-8 flex items-center justify-center rounded-full border 
                           border-flipkart-gray-dark hover:border-flipkart-blue 
                           disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <svg width="16" height="16" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                    </svg>
                  </button>
                </div>

                <!-- Save for Later -->
                <button class="text-sm font-medium text-text-primary uppercase hover:text-flipkart-blue 
                               transition-colors">
                  Save for Later
                </button>

                <!-- Remove -->
                <button
                  @click="remove(item)"
                  :disabled="updating === item.id"
                  class="text-sm font-medium text-text-primary uppercase hover:text-red-500 
                         transition-colors disabled:opacity-50"
                >
                  Remove
                </button>
              </div>
            </div>

            <!-- Place Order Button (Mobile) -->
            <div class="p-4 border-t border-flipkart-gray-dark lg:hidden">
              <RouterLink
                to="/checkout"
                class="block w-full py-3 bg-flipkart-orange text-white text-center 
                       font-medium rounded-sm hover:opacity-90 transition-opacity"
              >
                Place Order
              </RouterLink>
            </div>
          </div>
        </div>

        <!-- Right Column - Price Summary -->
        <div class="lg:w-96 flex-shrink-0">
          <div class="bg-white shadow-card rounded-sm sticky top-32">
            <div class="p-4 border-b border-flipkart-gray-dark">
              <h2 class="text-text-secondary font-medium uppercase text-sm">Price Details</h2>
            </div>

            <div class="p-4 space-y-3">
              <!-- Price Rows -->
              <div class="flex justify-between text-sm">
                <span class="text-text-primary">
                  Price ({{ totalItems }} {{ totalItems === 1 ? 'item' : 'items' }})
                </span>
                <span class="text-text-primary">₹{{ subtotal.toLocaleString('en-IN') }}</span>
              </div>

              <div class="flex justify-between text-sm">
                <span class="text-text-primary">Discount</span>
                <span class="text-flipkart-green">− ₹{{ discount.toLocaleString('en-IN') }}</span>
              </div>

              <div class="flex justify-between text-sm">
                <span class="text-text-primary">Delivery Charges</span>
                <span v-if="deliveryCharges === 0" class="text-flipkart-green">FREE</span>
                <span v-else class="text-text-primary">₹{{ deliveryCharges }}</span>
              </div>

              <!-- Total -->
              <div class="pt-3 border-t border-dashed border-flipkart-gray-dark">
                <div class="flex justify-between">
                  <span class="font-medium text-text-primary">Total Amount</span>
                  <span class="font-medium text-text-primary">₹{{ total.toLocaleString('en-IN') }}</span>
                </div>
              </div>

              <!-- Savings Message -->
              <div class="pt-3">
                <p class="text-sm text-flipkart-green font-medium">
                  You will save ₹{{ discount.toLocaleString('en-IN') }} on this order
                </p>
              </div>
            </div>

            <!-- Place Order Button -->
            <div class="p-4 border-t border-flipkart-gray-dark hidden lg:block">
              <RouterLink
                to="/checkout"
                class="block w-full py-3 bg-flipkart-orange text-white text-center 
                       font-medium rounded-sm hover:opacity-90 transition-opacity"
              >
                Place Order
              </RouterLink>
            </div>
          </div>

          <!-- Safe & Secure -->
          <div class="mt-4 flex items-center justify-center gap-2 text-text-secondary">
            <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
            <span class="text-xs">Safe and Secure Payments. Easy returns. 100% Authentic products.</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
