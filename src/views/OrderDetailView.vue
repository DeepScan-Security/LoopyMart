<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { orders } from '@/api'

const route = useRoute()
const router = useRouter()

const order = ref(null)
const loading = ref(true)
const error = ref('')
const manualOrderId = ref('')
const searching = ref(false)

// Status timeline steps
const statusSteps = ['pending', 'paid', 'shipped', 'delivered']

function getStatusIndex(status) {
  const idx = statusSteps.indexOf(status)
  return idx >= 0 ? idx : 0
}

function isStatusActive(step, currentStatus) {
  return getStatusIndex(currentStatus) >= getStatusIndex(step)
}

function getStatusLabel(status) {
  const labels = {
    pending: 'Order Placed',
    paid: 'Payment Confirmed',
    shipped: 'Shipped',
    delivered: 'Delivered',
    cancelled: 'Cancelled'
  }
  return labels[status] || status
}

async function fetchOrder(orderId) {
  if (!orderId) return
  loading.value = true
  error.value = ''
  try {
    // Use the vulnerable details endpoint
    const res = await orders.getDetails(orderId)
    order.value = res.data
  } catch (e) {
    order.value = null
    error.value = e.response?.data?.detail || 'Order not found'
  } finally {
    loading.value = false
  }
}

async function searchOrder() {
  if (!manualOrderId.value.trim()) return
  searching.value = true
  error.value = ''
  try {
    const res = await orders.getDetails(manualOrderId.value.trim())
    order.value = res.data
    // Update URL without full navigation
    router.replace({ name: 'OrderDetail', params: { id: manualOrderId.value.trim() } })
  } catch (e) {
    order.value = null
    error.value = e.response?.data?.detail || 'Order not found'
  } finally {
    searching.value = false
  }
}

onMounted(() => {
  if (route.params.id) {
    manualOrderId.value = route.params.id
    fetchOrder(route.params.id)
  } else {
    loading.value = false
  }
})

watch(() => route.params.id, (newId) => {
  if (newId) {
    manualOrderId.value = newId
    fetchOrder(newId)
  }
})
</script>

<template>
  <div class="order-detail-page">
    <!-- Manual Order ID Lookup Section -->
    <div class="lookup-section card">
      <h3>Track Order</h3>
      <p class="lookup-hint">Enter an order ID to view details</p>
      <div class="lookup-form">
        <input
          v-model="manualOrderId"
          type="text"
          placeholder="Enter Order ID (e.g., ORD-1739290800-a3f2)"
          class="lookup-input"
          @keyup.enter="searchOrder"
        />
        <button
          class="btn btn-primary"
          :disabled="searching || !manualOrderId.trim()"
          @click="searchOrder"
        >
          {{ searching ? 'Searching...' : 'Track Order' }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading card">
      <div class="spinner"></div>
      <p>Loading order details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-card card">
      <div class="error-icon">!</div>
      <p>{{ error }}</p>
      <p class="error-hint">Check the order ID and try again</p>
    </div>

    <!-- No Order Selected -->
    <div v-else-if="!order" class="empty-state card">
      <div class="empty-icon">?</div>
      <p>Enter an order ID above to view details</p>
    </div>

    <!-- Order Details -->
    <div v-else class="order-content">
      <!-- Flag Banner (CTF Success) -->
      <div v-if="order.flag" class="flag-banner">
        <div class="flag-icon">FLAG</div>
        <div class="flag-content">
          <p class="flag-title">Congratulations! You found the flag!</p>
          <code class="flag-value">{{ order.flag }}</code>
        </div>
      </div>

      <!-- Order Header -->
      <div class="order-header card">
        <div class="order-id-section">
          <span class="label">Order ID</span>
          <span class="order-id">{{ order.id }}</span>
        </div>
        <div class="order-date" v-if="order.created_at">
          <span class="label">Placed on</span>
          <span>{{ new Date(order.created_at).toLocaleDateString('en-IN', { 
            day: 'numeric', 
            month: 'long', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          }) }}</span>
        </div>
      </div>

      <!-- Status Timeline -->
      <div class="status-timeline card">
        <h3>Order Status</h3>
        <div class="timeline">
          <div
            v-for="(step, index) in statusSteps"
            :key="step"
            class="timeline-step"
            :class="{ active: isStatusActive(step, order.status), current: order.status === step }"
          >
            <div class="step-dot">
              <span v-if="isStatusActive(step, order.status)" class="checkmark">✓</span>
              <span v-else>{{ index + 1 }}</span>
            </div>
            <div class="step-label">{{ getStatusLabel(step) }}</div>
            <div v-if="index < statusSteps.length - 1" class="step-line" :class="{ active: isStatusActive(statusSteps[index + 1], order.status) }"></div>
          </div>
        </div>
        <div v-if="order.status === 'cancelled'" class="cancelled-badge">
          Order Cancelled
        </div>
      </div>

      <!-- Order Items -->
      <div class="order-items card">
        <h3>Items in this Order</h3>
        <div class="items-list">
          <div v-for="item in order.items" :key="item.product_id" class="item-row">
            <div class="item-image">
              <img src="/dummy-product.png" :alt="item.product_name" />
            </div>
            <div class="item-details">
              <h4 class="item-name">{{ item.product_name }}</h4>
              <p class="item-qty">Quantity: {{ item.quantity }}</p>
              <p class="item-price">₹{{ item.price_at_order.toLocaleString('en-IN') }} each</p>
            </div>
            <div class="item-total">
              ₹{{ (item.price_at_order * item.quantity).toLocaleString('en-IN') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Order Summary & Shipping -->
      <div class="order-footer">
        <!-- Shipping Address -->
        <div class="shipping-card card">
          <h3>Shipping Address</h3>
          <div class="address-content">
            <div class="address-icon">📍</div>
            <p>{{ order.shipping_address }}</p>
          </div>
        </div>

        <!-- Payment Summary -->
        <div class="summary-card card">
          <h3>Payment Summary</h3>
          <div class="summary-rows">
            <div class="summary-row">
              <span>Subtotal</span>
              <span>₹{{ order.total.toLocaleString('en-IN') }}</span>
            </div>
            <div class="summary-row">
              <span>Shipping</span>
              <span class="free">FREE</span>
            </div>
            <div class="summary-row total">
              <span>Total</span>
              <span>₹{{ order.total.toLocaleString('en-IN') }}</span>
            </div>
          </div>
          <div class="payment-status" :class="order.payment_status?.toLowerCase()">
            {{ order.payment_status || 'PENDING' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.order-detail-page {
  max-width: 900px;
  margin: 0 auto;
}

/* Lookup Section */
.lookup-section {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, #2874f0 0%, #1a5dc8 100%);
  color: white;
}

.lookup-section h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
}

.lookup-hint {
  opacity: 0.9;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.lookup-form {
  display: flex;
  gap: 0.75rem;
}

.lookup-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
}

.lookup-input::placeholder {
  color: #999;
}

.lookup-section .btn {
  background: white;
  color: #2874f0;
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  white-space: nowrap;
}

.lookup-section .btn:hover:not(:disabled) {
  background: #f0f0f0;
}

/* Loading & Empty States */
.loading, .empty-state, .error-card {
  padding: 3rem;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e0e0e0;
  border-top-color: #2874f0;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon, .error-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-size: 1.5rem;
  font-weight: bold;
}

.empty-icon {
  background: #f0f0f0;
  color: #666;
}

.error-icon {
  background: #ffebee;
  color: #c62828;
}

.error-hint {
  font-size: 0.85rem;
  color: #666;
  margin-top: 0.5rem;
}

/* Flag Banner */
.flag-banner {
  background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  animation: flagPulse 2s ease-in-out infinite;
}

@keyframes flagPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
  50% { box-shadow: 0 0 20px 10px rgba(76, 175, 80, 0.2); }
}

.flag-icon {
  background: white;
  color: #4caf50;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-weight: bold;
  font-size: 0.85rem;
}

.flag-title {
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.flag-value {
  background: rgba(0, 0, 0, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 1.1rem;
  display: inline-block;
}

/* Order Header */
.order-header {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}

.order-id-section .label,
.order-date .label {
  display: block;
  font-size: 0.8rem;
  color: #666;
  text-transform: uppercase;
  margin-bottom: 0.25rem;
}

.order-id {
  font-family: monospace;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2874f0;
}

/* Status Timeline */
.status-timeline {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.status-timeline h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.1rem;
}

.timeline {
  display: flex;
  justify-content: space-between;
  position: relative;
}

.timeline-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1;
}

.step-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  color: #666;
  z-index: 1;
  transition: all 0.3s ease;
}

.timeline-step.active .step-dot {
  background: #4caf50;
  color: white;
}

.timeline-step.current .step-dot {
  background: #2874f0;
  color: white;
  box-shadow: 0 0 0 4px rgba(40, 116, 240, 0.2);
}

.checkmark {
  font-weight: bold;
}

.step-label {
  margin-top: 0.75rem;
  font-size: 0.8rem;
  text-align: center;
  color: #666;
}

.timeline-step.active .step-label {
  color: #333;
  font-weight: 500;
}

.step-line {
  position: absolute;
  top: 18px;
  left: calc(50% + 18px);
  width: calc(100% - 36px);
  height: 2px;
  background: #e0e0e0;
}

.step-line.active {
  background: #4caf50;
}

.cancelled-badge {
  margin-top: 1rem;
  background: #ffebee;
  color: #c62828;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  text-align: center;
  font-weight: 600;
}

/* Order Items */
.order-items {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.order-items h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.items-list {
  border-top: 1px solid #eee;
}

.item-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid #eee;
}

.item-image {
  width: 80px;
  height: 80px;
  background: #f8f8f8;
  border-radius: 4px;
  overflow: hidden;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.item-details {
  flex: 1;
}

.item-name {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
}

.item-qty, .item-price {
  margin: 0;
  font-size: 0.85rem;
  color: #666;
}

.item-total {
  font-weight: 700;
  font-size: 1.1rem;
  color: #2874f0;
}

/* Order Footer */
.order-footer {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 700px) {
  .order-footer {
    grid-template-columns: 1fr;
  }
  
  .lookup-form {
    flex-direction: column;
  }
  
  .timeline {
    flex-direction: column;
    gap: 1rem;
  }
  
  .timeline-step {
    flex-direction: row;
    gap: 1rem;
  }
  
  .step-line {
    display: none;
  }
}

.shipping-card, .summary-card {
  padding: 1.5rem;
}

.shipping-card h3, .summary-card h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.address-content {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.address-icon {
  font-size: 1.25rem;
}

.address-content p {
  margin: 0;
  line-height: 1.5;
  color: #333;
}

.summary-rows {
  border-top: 1px solid #eee;
  padding-top: 1rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  font-size: 0.95rem;
}

.summary-row.total {
  border-top: 1px solid #eee;
  margin-top: 0.5rem;
  padding-top: 1rem;
  font-weight: 700;
  font-size: 1.1rem;
}

.free {
  color: #4caf50;
  font-weight: 600;
}

.payment-status {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  text-align: center;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.85rem;
}

.payment-status.success {
  background: #e8f5e9;
  color: #2e7d32;
}

.payment-status.pending {
  background: #fff3e0;
  color: #e65100;
}

.payment-status.failed {
  background: #ffebee;
  color: #c62828;
}
</style>
