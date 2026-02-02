<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { products, cart } from '@/api'

const route = useRoute()
const product = ref(null)
const loading = ref(true)
const quantity = ref(1)
const adding = ref(false)
const message = ref('')

onMounted(async () => {
  try {
    const res = await products.get(route.params.id)
    product.value = res.data
  } catch (_) {
    product.value = null
  } finally {
    loading.value = false
  }
})

const maxQty = computed(() => product.value ? Math.max(1, product.value.stock) : 1)

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  // Use VITE_STATIC_URL env variable or default to API proxy in dev
  const staticUrl = import.meta.env.VITE_STATIC_URL || ''
  if (url.startsWith('/static/')) return staticUrl + url
  return url
}

async function addToCart() {
  if (!product.value) return
  adding.value = true
  message.value = ''
  try {
    await cart.add({ product_id: product.value.id, quantity: quantity.value })
    const count = parseInt(sessionStorage.getItem('cartCount') || '0', 10) + quantity.value
    sessionStorage.setItem('cartCount', String(count))
    message.value = 'Added to cart!'
  } catch (e) {
    message.value = e.response?.data?.detail || 'Failed to add to cart'
  } finally {
    adding.value = false
  }
}
</script>

<template>
  <div class="product-detail">
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="!product" class="empty">Product not found.</div>
    <div v-else class="detail-grid">
      <div class="image-wrap card">
        <img :src="imageUrl(product.image_url)" :alt="product.name" />
      </div>
      <div class="info">
        <h1>{{ product.name }}</h1>
        <p class="price">₹{{ product.price.toLocaleString('en-IN') }}</p>
        <p v-if="product.description" class="description">{{ product.description }}</p>
        <p class="stock">In stock: {{ product.stock }}</p>
        <div class="form-group">
          <label>Quantity</label>
          <input v-model.number="quantity" type="number" min="1" :max="maxQty" />
        </div>
        <button
          class="btn btn-primary"
          :disabled="adding || product.stock < 1"
          @click="addToCart"
        >
          {{ adding ? 'Adding...' : 'Add to Cart' }}
        </button>
        <p v-if="message" class="message">{{ message }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.product-detail {
  max-width: 900px;
}
.loading, .empty {
  padding: 2rem;
  text-align: center;
}
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  align-items: start;
}
@media (max-width: 700px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
.image-wrap {
  aspect-ratio: 1;
  padding: 1rem;
  background: #f8f8f8;
}
.image-wrap img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.info h1 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}
.price {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2874f0;
  margin-bottom: 1rem;
}
.description {
  color: #555;
  margin-bottom: 1rem;
  line-height: 1.5;
}
.stock {
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
.info .form-group {
  max-width: 120px;
  margin-bottom: 1rem;
}
.message {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #0a0;
}
</style>
