<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { categories, products } from '@/api'

const featured = ref([])
const categoryList = ref([])

onMounted(async () => {
  try {
    const [catRes, prodRes] = await Promise.all([
      categories.list(),
      products.list({ limit: 8 }),
    ])
    categoryList.value = catRes.data
    featured.value = prodRes.data
  } catch (_) {
    featured.value = []
    categoryList.value = []
  }
})

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  if (url.startsWith('/static/')) return (import.meta.env.DEV ? 'http://127.0.0.1:8001' : '') + url
  return url
}
</script>

<template>
  <div class="home">
    <section class="hero">
      <h1>Welcome to Flipkart Clone</h1>
      <p>Shop electronics, fashion, and more.</p>
      <RouterLink to="/products" class="btn btn-primary">Browse Products</RouterLink>
    </section>
    <section v-if="categoryList.length" class="categories">
      <h2>Categories</h2>
      <div class="category-grid">
        <RouterLink
          v-for="c in categoryList"
          :key="c.id"
          :to="{ name: 'Products', query: { category: c.slug } }"
          class="category-card card"
        >
          <span class="cat-name">{{ c.name }}</span>
        </RouterLink>
      </div>
    </section>
    <section class="featured">
      <h2>Featured Products</h2>
      <div class="product-grid">
        <RouterLink
          v-for="p in featured"
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
    </section>
  </div>
</template>

<style scoped>
.hero {
  text-align: center;
  padding: 2rem 0 3rem;
}
.hero h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}
.hero p {
  color: var(--color-text);
  opacity: 0.9;
  margin-bottom: 1.5rem;
}
.categories, .featured {
  margin-top: 2rem;
}
.categories h2, .featured h2 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
}
.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 1rem;
}
.category-card {
  padding: 1rem;
  text-align: center;
  text-decoration: none;
  color: inherit;
}
.cat-name {
  font-weight: 600;
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
