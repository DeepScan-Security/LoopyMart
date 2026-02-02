<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { cart, orders } from '@/api'

const router = useRouter()
const items = ref([])
const shippingAddress = ref('')
const loading = ref(true)
const submitting = ref(false)
const error = ref('')

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

const total = computed(() =>
  items.value.reduce((s, i) => s + i.product_price * i.quantity, 0)
)

function loadRazorpay() {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(window.Razorpay)
      return
    }
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.async = true
    script.onload = () => resolve(window.Razorpay)
    script.onerror = () => resolve(null)
    document.body.appendChild(script)
  })
}

async function placeOrder() {
  if (!shippingAddress.value.trim()) {
    error.value = 'Please enter shipping address'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    const payRes = await orders.createPayment({ shipping_address: shippingAddress.value.trim() }).catch((e) => {
      if (e.response?.status === 503) return null
      throw e
    })
    if (!payRes) {
      await orders.create({ shipping_address: shippingAddress.value.trim() })
      sessionStorage.setItem('cartCount', '0')
      router.push({ name: 'Orders' })
      return
    }
    const { order_id, amount_paise, razorpay_order_id, key_id } = payRes.data
    const Razorpay = await loadRazorpay()
    if (!Razorpay) {
      error.value = 'Payment script failed to load. Try again or use Place Order without payment.'
      return
    }
    const options = {
      key: key_id,
      amount: amount_paise,
      order_id: razorpay_order_id,
      name: 'Flipkart Clone',
      description: 'Order payment',
      handler: async (response) => {
        try {
          await orders.verifyPayment({
            order_id,
            razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          })
          sessionStorage.setItem('cartCount', '0')
          router.push({ name: 'Orders' })
        } catch (e) {
          error.value = e.response?.data?.detail || 'Payment verification failed'
        } finally {
          submitting.value = false
        }
      },
      prefill: { email: '' },
      theme: { color: '#2874f0' },
    }
    const rzp = new Razorpay(options)
    rzp.on('payment.failed', () => {
      error.value = 'Payment failed or was cancelled'
      submitting.value = false
    })
    rzp.open()
    return
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to place order'
  }
  submitting.value = false
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
    <form v-else class="checkout-form" @submit.prevent="placeOrder">
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
      <div class="order-summary card">
        <h3>Order Summary</h3>
        <ul>
          <li v-for="item in items" :key="item.id">
            {{ item.product_name }} × {{ item.quantity }} — ₹{{ (item.product_price * item.quantity).toLocaleString('en-IN') }}
          </li>
        </ul>
        <p class="total">Total: ₹{{ total.toLocaleString('en-IN') }}</p>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" class="btn btn-primary" :disabled="submitting">
        {{ submitting ? 'Opening payment...' : 'Pay with Razorpay / Place Order' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.checkout-page h1 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}
.loading, .empty {
  padding: 2rem;
  text-align: center;
}
.checkout-form {
  max-width: 500px;
}
.order-summary {
  padding: 1.25rem;
  margin: 1rem 0;
}
.order-summary h3 {
  font-size: 1rem;
  margin-bottom: 0.75rem;
}
.order-summary ul {
  list-style: none;
  padding: 0;
  margin: 0 0 1rem;
  font-size: 0.9rem;
}
.order-summary li {
  padding: 0.25rem 0;
}
.total {
  font-size: 1.2rem;
  font-weight: 700;
}
.error {
  color: #e53e3e;
  margin: 0.5rem 0;
  font-size: 0.9rem;
}
</style>
