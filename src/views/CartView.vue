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

const total = computed(() =>
  items.value.reduce((s, i) => s + i.product_price * i.quantity, 0)
)

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  if (url.startsWith('/static/')) return (import.meta.env.DEV ? 'http://127.0.0.1:8001' : '') + url
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
  <div class="cart-page">
    <h1>Cart</h1>
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="!items.length" class="empty">
      <p>Your cart is empty.</p>
      <RouterLink to="/products" class="btn btn-primary">Shop now</RouterLink>
    </div>
    <div v-else>
      <div class="cart-list">
        <div v-for="item in items" :key="item.id" class="cart-item card">
          <div class="cart-item-image">
            <img :src="imageUrl(item.product_image_url)" :alt="item.product_name" />
          </div>
          <div class="cart-item-info">
            <h3>{{ item.product_name }}</h3>
            <p class="price">₹{{ item.product_price.toLocaleString('en-IN') }}</p>
            <div class="qty-controls">
              <button
                type="button"
                class="btn qty-btn"
                :disabled="updating === item.id || item.quantity <= 1"
                @click="updateQty(item, -1)"
              >
                −
              </button>
              <span class="qty">{{ item.quantity }}</span>
              <button
                type="button"
                class="btn qty-btn"
                :disabled="updating === item.id || item.quantity >= item.product_stock"
                @click="updateQty(item, 1)"
              >
                +
              </button>
            </div>
            <button
              type="button"
              class="btn btn-danger remove-btn"
              :disabled="updating === item.id"
              @click="remove(item)"
            >
              Remove
            </button>
          </div>
        </div>
      </div>
      <div class="cart-summary card">
        <p class="total">Total: ₹{{ total.toLocaleString('en-IN') }}</p>
        <RouterLink to="/checkout" class="btn btn-primary btn-block">Proceed to Checkout</RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cart-page h1 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}
.loading, .empty {
  padding: 2rem;
  text-align: center;
}
.empty .btn {
  margin-top: 1rem;
}
.cart-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.cart-item {
  display: flex;
  gap: 1rem;
  padding: 1rem;
}
.cart-item-image {
  width: 100px;
  height: 100px;
  flex-shrink: 0;
  background: #f8f8f8;
  overflow: hidden;
}
.cart-item-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.cart-item-info {
  flex: 1;
  min-width: 0;
}
.cart-item-info h3 {
  font-size: 1rem;
  margin-bottom: 0.25rem;
}
.price {
  font-weight: 600;
  color: #2874f0;
  margin-bottom: 0.5rem;
}
.qty-controls {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-right: 1rem;
}
.qty-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  font-size: 1.2rem;
  line-height: 1;
}
.qty {
  min-width: 1.5rem;
  text-align: center;
}
.remove-btn {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  padding: 0.35rem 0.75rem;
}
.cart-summary {
  max-width: 360px;
  padding: 1.25rem;
}
.total {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 1rem;
}
.btn-block {
  display: block;
  width: 100%;
}
</style>
