<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { RouterLink } from 'vue-router'
import { categories, products } from '@/api'

const route = useRoute()
const list = ref([])
const categoryList = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const slug = route.query.category
    const params = slug ? { category_slug: slug } : {}
    const [catRes, prodRes] = await Promise.all([
      categories.list(),
      products.list(params),
    ])
    categoryList.value = catRes.data
    list.value = prodRes.data
  } catch (_) {
    list.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.query.category, load)

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  if (url.startsWith('/static/')) return (import.meta.env.DEV ? 'http://127.0.0.1:8001' : '') + url
  return url
}
</script>

<template>
  <div class="products-page">
    <h1>Products</h1>
    <div class="filters">
      <RouterLink
        :to="{ name: 'Products' }"
        class="filter-chip"
        :class="{ active: !route.query.category }"
      >
        All
      </RouterLink>
      <RouterLink
        v-for="c in categoryList"
        :key="c.id"
        :to="{ name: 'Products', query: { category: c.slug } }"
        class="filter-chip"
        :class="{ active: route.query.category === c.slug }"
      >
        {{ c.name }}
      </RouterLink>
    </div>
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else class="product-grid">
      <RouterLink
        v-for="p in list"
        :key="p.id"
        :to="{ name: 'ProductDetail', params: { id: p.id } }"
        class="product-card card"
      >
        <div class="product-image">
          <img :src="imageUrl(p.image_url)" :alt="p.name" />
        </div>
        <div class="product-info">
          <h3>{{ p.name }}</h3>
          <p class="price">₹{{ p.price.toLocaleString('en-IN') }}</p>
        </div>
      </RouterLink>
    </div>
    <p v-if="!loading && !list.length" class="empty">No products found.</p>
  </div>
</template>

<style scoped>
.products-page h1 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
.filter-chip {
  padding: 0.4rem 0.9rem;
  border-radius: 20px;
  background: #f0f0f0;
  color: #333;
  font-size: 0.9rem;
  text-decoration: none;
}
.filter-chip.active {
  background: #2874f0;
  color: #fff;
}
.loading, .empty {
  padding: 2rem;
  text-align: center;
  color: #666;
}
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1.25rem;
}
.product-card {
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s;
}
.product-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.product-image {
  aspect-ratio: 1;
  background: #f8f8f8;
  overflow: hidden;
}
.product-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.product-info {
  padding: 0.75rem;
}
.product-info h3 {
  font-size: 0.95rem;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.price {
  font-weight: 600;
  color: #2874f0;
}
</style>
