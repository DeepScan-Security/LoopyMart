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

async function placeOrder() {
  if (!shippingAddress.value.trim()) {
    error.value = 'Please enter shipping address'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    await orders.create({ shipping_address: shippingAddress.value.trim() })
    sessionStorage.setItem('cartCount', '0')
    router.push({ name: 'Orders' })
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
        {{ submitting ? 'Placing order...' : 'Place Order' }}
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
