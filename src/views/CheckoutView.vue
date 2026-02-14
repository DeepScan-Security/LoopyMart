<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { cart, orders } from '@/api'
import client from '@/api/client'

const router = useRouter()
const items = ref([])
const shippingAddress = ref('')
const loading = ref(true)
const submitting = ref(false)
const error = ref('')

// Payment state
const paymentMethod = ref('wallet')
const walletBalance = ref(0)
const selectedCoupon = ref(null)
const coupons = ref([])
const couponDiscount = ref(0)
const showCoupons = ref(false)

onMounted(async () => {
  try {
    const [cartRes, walletRes, couponsRes] = await Promise.all([
      cart.list(),
      client.get('/payments/wallet/balance'),
      client.get('/payments/coupons'),
    ])
    items.value = cartRes.data
    walletBalance.value = walletRes.data.balance
    coupons.value = couponsRes.data
  } catch (_) {
    items.value = []
  } finally {
    loading.value = false
  }
})

const subtotal = computed(() =>
  items.value.reduce((s, i) => s + i.product_price * i.quantity, 0)
)

const total = computed(() => Math.max(0, subtotal.value - couponDiscount.value))

async function applyCoupon(coupon) {
  if (coupon.is_used) {
    error.value = 'Coupon already used'
    return
  }
  
  try {
    const res = await client.post('/payments/coupon/apply', { coupon_code: coupon.code })
    if (res.data.is_valid) {
      selectedCoupon.value = coupon
      couponDiscount.value = res.data.discount
      showCoupons.value = false
      error.value = ''
    } else {
      error.value = res.data.message
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to apply coupon'
  }
}

function removeCoupon() {
  selectedCoupon.value = null
  couponDiscount.value = 0
}

async function placeOrder() {
  if (!shippingAddress.value.trim()) {
    error.value = 'Please enter shipping address'
    return
  }
  
  if (paymentMethod.value === 'wallet' && walletBalance.value < total.value) {
    error.value = 'Insufficient wallet balance'
    return
  }
  
  submitting.value = true
  error.value = ''
  
  try {
    // Create order first (without payment)
    const orderRes = await orders.create({ shipping_address: shippingAddress.value.trim() })
    const orderId = orderRes.data.id
    
    // Process dummy payment
    const paymentRes = await client.post('/payments/dummy-pay', {
      order_id: orderId,
      amount: total.value,
      payment_method: paymentMethod.value,
      coupon_code: selectedCoupon.value?.code || null,
    })
    
    if (paymentRes.data.status === 'SUCCESS') {
      sessionStorage.setItem('cartCount', '0')
      router.push({ name: 'Orders' })
    } else {
      error.value = 'Payment failed. Please try again.'
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to place order'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="checkout-page">
    <h1>Checkout</h1>
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="!items.length" class="empty">
      <p>Your cart is empty.</p>
      <router-link to="/products" class="btn btn-primary">Shop now</router-link>
    </div>
    <div v-else class="checkout-container">
      <form class="checkout-form" @submit.prevent="placeOrder">
        <!-- Shipping Address -->
        <div class="form-group">
          <label for="address">Shipping Address</label>
          <textarea
            id="address"
            v-model="shippingAddress"
            rows="3"
            placeholder="Full address, city, state, PIN"
            required
          />
        </div>

        <!-- Payment Method -->
        <div class="form-group">
          <label>Payment Method</label>
          <div class="payment-methods">
            <label class="payment-option">
              <input type="radio" v-model="paymentMethod" value="wallet" />
              <span>Wallet (₹{{ walletBalance.toLocaleString('en-IN') }})</span>
            </label>
            <label class="payment-option">
              <input type="radio" v-model="paymentMethod" value="card" />
              <span>Credit/Debit Card</span>
            </label>
            <label class="payment-option">
              <input type="radio" v-model="paymentMethod" value="upi" />
              <span>UPI</span>
            </label>
            <label class="payment-option">
              <input type="radio" v-model="paymentMethod" value="cod" />
              <span>Cash on Delivery</span>
            </label>
          </div>
        </div>

        <!-- Apply Coupon -->
        <div class="form-group">
          <label>Apply Coupon</label>
          <div v-if="selectedCoupon" class="applied-coupon">
            <span>{{ selectedCoupon.code }} - ₹{{ selectedCoupon.discount }} off</span>
            <button type="button" @click="removeCoupon" class="btn-remove">Remove</button>
          </div>
          <button v-else type="button" @click="showCoupons = !showCoupons" class="btn-secondary">
            {{ showCoupons ? 'Hide Coupons' : 'View Available Coupons' }}
          </button>
          
          <div v-if="showCoupons && !selectedCoupon" class="coupons-list">
            <div v-for="coupon in coupons" :key="coupon.code" 
                 class="coupon-card" 
                 :class="{ 'coupon-used': coupon.is_used }">
              <div class="coupon-info">
                <strong>{{ coupon.code }}</strong>
                <p>{{ coupon.description }}</p>
                <span class="coupon-discount">Save ₹{{ coupon.discount }}</span>
              </div>
              <button 
                v-if="!coupon.is_used"
                type="button" 
                @click="applyCoupon(coupon)" 
                class="btn-apply">
                Apply
              </button>
              <span v-else class="used-label">Used</span>
            </div>
          </div>
        </div>

        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary btn-place-order" :disabled="submitting">
          {{ submitting ? 'Processing...' : `Pay ₹${total.toLocaleString('en-IN')}` }}
        </button>
      </form>

      <!-- Order Summary -->
      <div class="order-summary card">
        <h3>Order Summary</h3>
        <ul class="items-list">
          <li v-for="item in items" :key="item.id">
            <span>{{ item.product_name }} × {{ item.quantity }}</span>
            <span>₹{{ (item.product_price * item.quantity).toLocaleString('en-IN') }}</span>
          </li>
        </ul>
        <div class="summary-row">
          <span>Subtotal</span>
          <span>₹{{ subtotal.toLocaleString('en-IN') }}</span>
        </div>
        <div v-if="couponDiscount > 0" class="summary-row discount">
          <span>Coupon Discount</span>
          <span>-₹{{ couponDiscount.toLocaleString('en-IN') }}</span>
        </div>
        <div class="summary-row total">
          <span>Total</span>
          <span>₹{{ total.toLocaleString('en-IN') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.checkout-page h1 {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
}

.loading, .empty {
  padding: 2rem;
  text-align: center;
}

.checkout-container {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 2rem;
  align-items: start;
}

@media (max-width: 900px) {
  .checkout-container {
    grid-template-columns: 1fr;
  }
}

.checkout-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.95rem;
}

.payment-methods {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.payment-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.payment-option:has(input:checked) {
  border-color: #2874f0;
  background: #f0f5ff;
}

.payment-option input[type="radio"] {
  cursor: pointer;
}

.applied-coupon {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  background: #d1fae5;
  border: 1px solid #10b981;
  border-radius: 6px;
  font-size: 0.9rem;
}

.btn-remove {
  background: #ef4444;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-secondary {
  width: 100%;
  padding: 0.75rem;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.coupons-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1rem;
}

.coupon-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border: 2px dashed #2874f0;
  border-radius: 8px;
  background: #f0f5ff;
}

.coupon-card.coupon-used {
  opacity: 0.5;
  border-color: #ccc;
  background: #f5f5f5;
}

.coupon-info strong {
  display: block;
  color: #2874f0;
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.coupon-info p {
  margin: 0.25rem 0;
  font-size: 0.85rem;
  color: #666;
}

.coupon-discount {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  background: #2874f0;
  color: white;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
}

.btn-apply {
  padding: 0.5rem 1rem;
  background: #2874f0;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.used-label {
  color: #999;
  font-weight: 600;
}

.order-summary {
  padding: 1.5rem;
  position: sticky;
  top: 1rem;
}

.order-summary h3 {
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.items-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1rem;
}

.items-list li {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  font-size: 0.9rem;
  border-bottom: 1px solid #f0f0f0;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  font-size: 0.95rem;
}

.summary-row.discount {
  color: #10b981;
  font-weight: 600;
}

.summary-row.total {
  font-size: 1.2rem;
  font-weight: 700;
  margin-top: 0.5rem;
  padding-top: 1rem;
  border-top: 2px solid #e5e7eb;
}

.btn-place-order {
  width: 100%;
  padding: 1rem;
  font-size: 1rem;
  font-weight: 600;
}

.error {
  color: #e53e3e;
  margin: 0;
  font-size: 0.9rem;
  padding: 0.75rem;
  background: #fee;
  border-radius: 4px;
}
</style>
