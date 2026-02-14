<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { RouterLink } from 'vue-router'
import { categories, products } from '@/api'

const route = useRoute()
const router = useRouter()
const list = ref([])
const categoryList = ref([])
const loading = ref(true)
const searchQuery = ref('')

async function load(searchQ) {
  loading.value = true
  // Read q from URL on load (unless explicitly passed e.g. from doSearch)
  if (route.query.q && searchQuery.value === '') {
    searchQuery.value = route.query.q
  }
  try {
    const slug = route.query.category
    // Use explicit searchQ when provided (avoids race with router.update)
    const q = searchQ !== undefined ? (searchQ?.trim() || null) : (searchQuery.value?.trim() || route.query.q || null)
    const params = { limit: 100 }
    if (slug) params.category_slug = slug
    if (q) {
      params.q = q
      params.search = q
    }
    const [catRes, prodRes] = await Promise.all([
      categories.list(),
      products.list(params),
    ])
    categoryList.value = catRes.data
    list.value = prodRes.data
  } catch (e) {
    list.value = []
  } finally {
    loading.value = false
  }
}

function doSearch() {
  // Update URL with search query
  const query = { ...route.query }
  if (searchQuery.value?.trim()) {
    query.q = searchQuery.value.trim()
  } else {
    delete query.q
  }
  router.replace({ name: 'Products', query })
  // Pass search term explicitly so filter is applied immediately (no race with route)
  load(searchQuery.value?.trim() || null)
}

onMounted(load)
watch(() => route.query.category, load)
watch(() => route.query.q, (newQ) => {
  if (newQ !== searchQuery.value) {
    searchQuery.value = newQ || ''
    load()
  }
})

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  // Use VITE_STATIC_URL env variable or default to API proxy in dev
  const staticUrl = import.meta.env.VITE_STATIC_URL || ''
  // #region agent log
  if (url.startsWith('/static/')) {
    const finalUrl = staticUrl + url
    fetch('http://127.0.0.1:7242/ingest/0047ae72-2236-4c94-b642-e409f5c5e173',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ProductsView.vue:imageUrl',message:'Image URL construction',data:{originalUrl:url,staticUrl:staticUrl,finalUrl:finalUrl},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'H1'})}).catch(()=>{});
    return finalUrl
  }
  // #endregion
  return url
}
</script>

<template>
  <div class="products-page">
    <h1>Products</h1>
    <div class="search-row">
      <input
        v-model="searchQuery"
        type="search"
        placeholder="Search products..."
        class="search-input"
        @keyup.enter="doSearch"
      />
      <button type="button" class="btn btn-primary search-btn" @click="doSearch">Search</button>
    </div>
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
.search-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.search-input {
  flex: 1;
  min-width: 180px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}
.search-btn {
  white-space: nowrap;
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
