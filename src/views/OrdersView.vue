<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { RouterLink } from 'vue-router'
import { orders } from '@/api'

const list = ref([])
const loading = ref(true)
const filter = ref('all')

// Per-order invoice download state
const invoiceDownloading = reactive({})

async function downloadInvoice(orderId) {
  invoiceDownloading[orderId] = true
  try {
    const res = await orders.generateInvoice(orderId)
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `invoice-${orderId.slice(0, 8)}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (_) {
    alert('Failed to generate invoice. Please try again.')
  } finally {
    invoiceDownloading[orderId] = false
  }
}

const statusFilters = [
  { id: 'all', label: 'All Orders' },
  { id: 'pending', label: 'Pending' },
  { id: 'processing', label: 'Processing' },
  { id: 'shipped', label: 'Shipped' },
  { id: 'delivered', label: 'Delivered' },
]

onMounted(async () => {
  try {
    const res = await orders.list()
    list.value = res.data
  } catch (_) {
    list.value = []
  } finally {
    loading.value = false
  }
})

const filteredOrders = computed(() => {
  if (filter.value === 'all') return list.value
  return list.value.filter(order => order.status.toLowerCase() === filter.value)
})

function getStatusColor(status) {
  switch (status.toLowerCase()) {
    case 'delivered': return 'bg-loopymart-green'
    case 'shipped': return 'bg-loopymart-blue'
    case 'processing': return 'bg-loopymart-orange'
    case 'pending': return 'bg-yellow-500'
    case 'cancelled': return 'bg-red-500'
    default: return 'bg-text-secondary'
  }
}

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  const staticUrl = import.meta.env.VITE_STATIC_URL || ''
  if (url.startsWith('/static/')) return staticUrl + url
  return url
}

// Handles both legacy string addresses and new structured object addresses
function formatShipTo(addr) {
  if (!addr) return 'N/A'
  if (typeof addr === 'string') return addr
  const parts = [addr.full_name, addr.city, addr.pincode ? `– ${addr.pincode}` : ''].filter(Boolean)
  return parts.join(', ')
}

function formatFullAddress(addr) {
  if (!addr) return 'No address provided'
  if (typeof addr === 'string') return addr
  return [
    `${addr.full_name}${addr.phone ? ' · ' + addr.phone : ''}`,
    addr.address_line1 + (addr.address_line2 ? ', ' + addr.address_line2 : ''),
    addr.landmark ? 'Near ' + addr.landmark : '',
    `${addr.city}, ${addr.state} – ${addr.pincode}`,
    addr.country || 'India',
  ].filter(Boolean).join('\n')
}
</script>

<template>
  <div class="min-h-screen bg-loopymart-gray py-4">
    <div class="max-w-container mx-auto px-4">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <h1 class="text-xl font-medium text-text-primary">My Orders</h1>
        <RouterLink to="/products" class="text-loopymart-blue text-sm hover:underline">
          Continue Shopping
        </RouterLink>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="bg-white shadow-card rounded-sm p-12 text-center">
        <div class="inline-block w-8 h-8 border-4 border-loopymart-blue border-t-transparent 
                    rounded-full animate-spin"></div>
        <p class="mt-4 text-text-secondary">Loading orders...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!list.length" class="bg-white shadow-card rounded-sm p-12 text-center">
        <svg width="96" height="96" class="w-24 h-24 mx-auto text-text-hint mb-4" fill="none" stroke="currentColor" 
             viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" 
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
        </svg>
        <h2 class="text-xl font-medium text-text-primary mb-2">No orders yet</h2>
        <p class="text-text-secondary mb-6">Looks like you haven't made any orders.</p>
        <RouterLink to="/products" class="btn btn-primary btn-lg">
          Start Shopping
        </RouterLink>
      </div>

      <!-- Orders Content -->
      <div v-else class="space-y-4">
        <!-- Filters -->
        <div class="bg-white shadow-card rounded-sm p-4 flex items-center gap-2 overflow-x-auto 
                    scrollbar-hide">
          <button
            v-for="f in statusFilters"
            :key="f.id"
            @click="filter = f.id"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors',
              filter === f.id 
                ? 'bg-loopymart-blue text-white' 
                : 'bg-loopymart-gray text-text-primary hover:bg-loopymart-gray-dark'
            ]"
          >
            {{ f.label }}
          </button>
        </div>

        <!-- Orders List -->
        <div v-if="filteredOrders.length" class="space-y-4">
          <div 
            v-for="order in filteredOrders" 
            :key="order.id"
            class="bg-white shadow-card rounded-sm overflow-hidden"
          >
            <!-- Order Header -->
            <div class="p-4 bg-loopymart-gray border-b border-loopymart-gray-dark 
                        flex flex-wrap items-center gap-4">
              <div>
                <p class="text-xs text-text-secondary">ORDER PLACED</p>
                <p class="text-sm font-medium text-text-primary">
                  {{ new Date(order.created_at).toLocaleDateString('en-IN', {
                    year: 'numeric', month: 'long', day: 'numeric'
                  }) }}
                </p>
              </div>
              <div>
                <p class="text-xs text-text-secondary">TOTAL</p>
                <p class="text-sm font-medium text-text-primary">
                  ₹{{ order.total.toLocaleString('en-IN') }}
                </p>
              </div>
              <div>
                <p class="text-xs text-text-secondary">SHIP TO</p>
                <p class="text-sm font-medium text-text-primary line-clamp-1 max-w-[200px]">
                  {{ formatShipTo(order.shipping_address) }}
                </p>
              </div>
              <div class="ml-auto flex items-center gap-4">
                <span :class="[
                  'px-3 py-1 rounded-full text-xs font-medium text-white uppercase',
                  getStatusColor(order.status)
                ]">
                  {{ order.status }}
                </span>
                <span class="text-xs text-text-secondary">
                  Order #{{ order.id.slice(0, 8) }}
                </span>
              </div>
            </div>

            <!-- Order Items -->
            <div class="divide-y divide-loopymart-gray-dark">
              <div 
                v-for="item in order.items" 
                :key="item.id"
                class="p-4 flex gap-4"
              >
                <!-- Product Image -->
                <RouterLink 
                  :to="{ name: 'ProductDetail', params: { id: item.product_id } }"
                  class="w-20 h-20 flex-shrink-0 border border-loopymart-gray-dark rounded-sm p-1"
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
                    class="text-text-primary hover:text-loopymart-blue transition-colors"
                  >
                    <h3 class="font-medium line-clamp-1">{{ item.product_name }}</h3>
                  </RouterLink>
                  <p class="text-sm text-text-secondary mt-1">
                    Qty: {{ item.quantity }} | ₹{{ item.price_at_order.toLocaleString('en-IN') }} each
                  </p>
                  <p class="text-sm font-medium text-text-primary mt-1">
                    ₹{{ (item.price_at_order * item.quantity).toLocaleString('en-IN') }}
                  </p>
                </div>

                <!-- Actions -->
                <div class="flex flex-col gap-2">
                  <RouterLink 
                    :to="{ name: 'ProductDetail', params: { id: item.product_id } }"
                    class="btn btn-sm"
                  >
                    View Product
                  </RouterLink>
                  <button 
                    v-if="order.status.toLowerCase() === 'delivered'"
                    class="btn btn-sm btn-secondary"
                  >
                    Write Review
                  </button>
                </div>
              </div>
            </div>

            <!-- Order Footer -->
            <div class="p-4 bg-loopymart-gray border-t border-loopymart-gray-dark 
                        flex items-center justify-between">
              <div class="text-sm">
                <span v-if="order.status.toLowerCase() === 'delivered'" class="text-loopymart-green">
                  Delivered on {{ new Date(order.updated_at).toLocaleDateString('en-IN') }}
                </span>
                <span v-else-if="order.status.toLowerCase() === 'shipped'" class="text-loopymart-blue">
                  Expected delivery by {{ new Date(Date.now() + 2*24*60*60*1000).toLocaleDateString('en-IN') }}
                </span>
                <span v-else class="text-text-secondary">
                  Order is being processed
                </span>
              </div>
              <div class="flex gap-2 items-center">
                <button class="text-sm text-loopymart-blue hover:underline">
                  Track Order
                </button>
                <span class="text-text-hint">|</span>
                <button
                  class="text-sm text-loopymart-blue hover:underline flex items-center gap-1"
                  :disabled="invoiceDownloading[order.id]"
                  @click="downloadInvoice(order.id)"
                >
                  <span
                    v-if="invoiceDownloading[order.id]"
                    class="inline-block w-3 h-3 border-2 border-loopymart-blue border-t-transparent
                           rounded-full animate-spin"
                  ></span>
                  {{ invoiceDownloading[order.id] ? 'Generating\u2026' : 'Download Invoice' }}
                </button>
                <span class="text-text-hint">|</span>
                <button class="text-sm text-loopymart-blue hover:underline">
                  Need Help?
                </button>
              </div>
            </div>

          </div>
        </div>

        <!-- No Results -->
        <div v-else class="bg-white shadow-card rounded-sm p-12 text-center">
          <p class="text-text-secondary">No orders found with status "{{ filter }}"</p>
          <button @click="filter = 'all'" class="btn btn-primary mt-4">
            View All Orders
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
