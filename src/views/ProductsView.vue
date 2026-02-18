<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { categories, products } from '@/api'
import ProductCard from '@/components/ProductCard.vue'

const route = useRoute()
const router = useRouter()
const list = ref([])
const categoryList = ref([])
const loading = ref(true)
const searchQuery = ref('')
const showMobileFilters = ref(false)

// Filter states
const selectedCategory = ref('')
const priceRange = ref({ min: 0, max: 100000 })
const selectedRating = ref(0)
const sortBy = ref('relevance')

const sortOptions = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'price_low', label: 'Price: Low to High' },
  { value: 'price_high', label: 'Price: High to Low' },
  { value: 'newest', label: 'Newest First' },
  { value: 'popular', label: 'Popularity' },
]

const priceRanges = [
  { min: 0, max: 500, label: 'Under ₹500' },
  { min: 500, max: 1000, label: '₹500 - ₹1,000' },
  { min: 1000, max: 5000, label: '₹1,000 - ₹5,000' },
  { min: 5000, max: 10000, label: '₹5,000 - ₹10,000' },
  { min: 10000, max: 50000, label: '₹10,000 - ₹50,000' },
  { min: 50000, max: 100000, label: 'Above ₹50,000' },
]

async function loadProducts(searchQ) {
  loading.value = true
  if (route.query.q && searchQuery.value === '') {
    searchQuery.value = route.query.q
  }
  try {
    const slug = route.query.category
    if (slug) selectedCategory.value = slug
    
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
  const query = { ...route.query }
  if (searchQuery.value?.trim()) {
    query.q = searchQuery.value.trim()
  } else {
    delete query.q
  }
  router.replace({ name: 'Products', query })
  loadProducts(searchQuery.value?.trim() || null)
}

function selectCategory(slug) {
  selectedCategory.value = slug
  const query = { ...route.query }
  if (slug) {
    query.category = slug
  } else {
    delete query.category
  }
  router.replace({ name: 'Products', query })
}

function clearFilters() {
  selectedCategory.value = ''
  priceRange.value = { min: 0, max: 100000 }
  selectedRating.value = 0
  searchQuery.value = ''
  router.replace({ name: 'Products' })
  loadProducts()
}

// Filtered and sorted products
const filteredProducts = computed(() => {
  let result = [...list.value]
  
  // Apply price filter (client-side for demo)
  result = result.filter(p => 
    p.price >= priceRange.value.min && p.price <= priceRange.value.max
  )
  
  // Apply sorting
  switch (sortBy.value) {
    case 'price_low':
      result.sort((a, b) => a.price - b.price)
      break
    case 'price_high':
      result.sort((a, b) => b.price - a.price)
      break
    case 'newest':
      result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      break
    default:
      break
  }
  
  return result
})

const activeCategory = computed(() => {
  return categoryList.value.find(c => c.slug === selectedCategory.value)
})

onMounted(loadProducts)
watch(() => route.query.category, loadProducts)
watch(() => route.query.q, (newQ) => {
  if (newQ !== searchQuery.value) {
    searchQuery.value = newQ || ''
    loadProducts()
  }
})
</script>

<template>
  <div class="min-h-screen bg-loopymart-gray">
    <div class="max-w-container mx-auto px-4 py-4">
      <!-- Breadcrumb -->
      <nav class="text-sm text-text-secondary mb-4">
        <RouterLink to="/" class="hover:text-loopymart-blue">Home</RouterLink>
        <span class="mx-2">&gt;</span>
        <span v-if="activeCategory">
          <RouterLink to="/products" class="hover:text-loopymart-blue">Products</RouterLink>
          <span class="mx-2">&gt;</span>
          <span class="text-text-primary">{{ activeCategory.name }}</span>
        </span>
        <span v-else class="text-text-primary">Products</span>
      </nav>

      <div class="flex gap-4">
        <!-- Sidebar Filters - Desktop -->
        <aside class="hidden md:block w-64 flex-shrink-0">
          <div class="bg-white shadow-card rounded-sm sticky top-32">
            <!-- Filters Header -->
            <div class="flex items-center justify-between p-4 border-b border-loopymart-gray-dark">
              <h2 class="font-semibold text-text-primary">Filters</h2>
              <button 
                @click="clearFilters"
                class="text-sm text-loopymart-blue hover:underline"
              >
                Clear All
              </button>
            </div>

            <!-- Categories -->
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h3 class="font-medium text-text-primary text-sm mb-3 uppercase tracking-wide">
                Categories
              </h3>
              <ul class="space-y-2">
                <li>
                  <button
                    @click="selectCategory('')"
                    :class="[
                      'text-sm w-full text-left py-1 transition-colors',
                      !selectedCategory ? 'text-loopymart-blue font-medium' : 'text-text-primary hover:text-loopymart-blue'
                    ]"
                  >
                    All Categories
                  </button>
                </li>
                <li v-for="cat in categoryList" :key="cat.id">
                  <button
                    @click="selectCategory(cat.slug)"
                    :class="[
                      'text-sm w-full text-left py-1 transition-colors',
                      selectedCategory === cat.slug ? 'text-loopymart-blue font-medium' : 'text-text-primary hover:text-loopymart-blue'
                    ]"
                  >
                    {{ cat.name }}
                  </button>
                </li>
              </ul>
            </div>

            <!-- Price Range -->
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h3 class="font-medium text-text-primary text-sm mb-3 uppercase tracking-wide">
                Price
              </h3>
              <ul class="space-y-2">
                <li v-for="range in priceRanges" :key="range.label">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="price"
                      :checked="priceRange.min === range.min && priceRange.max === range.max"
                      @change="priceRange = { min: range.min, max: range.max }"
                      class="text-loopymart-blue focus:ring-flipkart-blue"
                    />
                    <span class="text-sm text-text-primary">{{ range.label }}</span>
                  </label>
                </li>
              </ul>
            </div>

            <!-- Customer Ratings -->
            <div class="p-4">
              <h3 class="font-medium text-text-primary text-sm mb-3 uppercase tracking-wide">
                Customer Ratings
              </h3>
              <ul class="space-y-2">
                <li v-for="rating in [4, 3, 2, 1]" :key="rating">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="rating"
                      :checked="selectedRating === rating"
                      @change="selectedRating = rating"
                      class="text-loopymart-blue focus:ring-flipkart-blue"
                    />
                    <span class="flex items-center gap-1 text-sm text-text-primary">
                      {{ rating }}
                      <svg width="12" height="12" class="w-3 h-3 text-loopymart-orange" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                      </svg>
                      & above
                    </span>
                  </label>
                </li>
              </ul>
            </div>
          </div>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 min-w-0">
          <!-- Search & Sort Bar -->
          <div class="bg-white shadow-card rounded-sm mb-4 p-4">
            <div class="flex flex-col sm:flex-row gap-4">
              <!-- Search -->
              <div class="flex-1 flex gap-2">
                <div class="flex-1 relative">
                  <input
                    v-model="searchQuery"
                    type="search"
                    placeholder="Search in products..."
                    class="form-input pr-10"
                    @keyup.enter="doSearch"
                  />
                  <svg 
                    width="20" height="20" class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-hint"
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                  </svg>
                </div>
                <button @click="doSearch" class="btn btn-primary">
                  Search
                </button>
              </div>

              <!-- Mobile Filter Button -->
              <button 
                @click="showMobileFilters = true"
                class="md:hidden btn flex items-center gap-2"
              >
                <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/>
                </svg>
                Filters
              </button>

              <!-- Sort -->
              <div class="flex items-center gap-2">
                <span class="text-sm text-text-secondary whitespace-nowrap">Sort by:</span>
                <select 
                  v-model="sortBy"
                  class="form-input py-1.5 w-auto"
                >
                  <option 
                    v-for="opt in sortOptions" 
                    :key="opt.value" 
                    :value="opt.value"
                  >
                    {{ opt.label }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <!-- Results Info -->
          <div class="flex items-center justify-between mb-4 px-1">
            <p class="text-sm text-text-secondary">
              <template v-if="route.query.q">
                Showing results for "<span class="text-text-primary font-medium">{{ route.query.q }}</span>"
              </template>
              <template v-else-if="activeCategory">
                Showing products in <span class="text-text-primary font-medium">{{ activeCategory.name }}</span>
              </template>
              <template v-else>
                Showing all products
              </template>
              <span class="ml-1">({{ filteredProducts.length }} items)</span>
            </p>
          </div>

          <!-- Loading State -->
          <div v-if="loading" class="bg-white shadow-card rounded-sm p-12 text-center">
            <div class="inline-block w-8 h-8 border-4 border-loopymart-blue border-t-transparent 
                        rounded-full animate-spin"></div>
            <p class="mt-4 text-text-secondary">Loading products...</p>
          </div>

          <!-- Empty State -->
          <div 
            v-else-if="!filteredProducts.length" 
            class="bg-white shadow-card rounded-sm p-12 text-center"
          >
            <svg width="64" height="64" class="w-16 h-16 mx-auto text-text-hint mb-4" fill="none" stroke="currentColor" 
                 viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
                    d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <h3 class="text-lg font-medium text-text-primary mb-2">No products found</h3>
            <p class="text-text-secondary mb-4">Try adjusting your search or filter criteria</p>
            <button @click="clearFilters" class="btn btn-primary">
              Clear Filters
            </button>
          </div>

          <!-- Product Grid -->
          <div v-else class="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <ProductCard
              v-for="product in filteredProducts"
              :key="product.id"
              :product="product"
              variant="grid"
            />
          </div>
        </main>
      </div>
    </div>

    <!-- Mobile Filters Drawer -->
    <Teleport to="body">
      <div 
        v-if="showMobileFilters" 
        class="fixed inset-0 z-50 md:hidden"
      >
        <!-- Backdrop -->
        <div 
          class="absolute inset-0 bg-black/50"
          @click="showMobileFilters = false"
        ></div>

        <!-- Drawer -->
        <div class="absolute inset-y-0 left-0 w-80 max-w-full bg-white shadow-xl animate-slideIn">
          <!-- Header -->
          <div class="flex items-center justify-between p-4 border-b border-loopymart-gray-dark">
            <h2 class="font-semibold text-text-primary">Filters</h2>
            <button 
              @click="showMobileFilters = false"
              class="p-1 hover:bg-loopymart-gray rounded-full"
            >
              <svg width="24" height="24" class="w-6 h-6 text-text-secondary" fill="none" stroke="currentColor" 
                   viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <!-- Filter Content -->
          <div class="overflow-y-auto h-[calc(100%-120px)]">
            <!-- Categories -->
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h3 class="font-medium text-text-primary text-sm mb-3 uppercase">Categories</h3>
              <ul class="space-y-2">
                <li>
                  <button
                    @click="selectCategory(''); showMobileFilters = false"
                    :class="[
                      'text-sm w-full text-left py-1',
                      !selectedCategory ? 'text-loopymart-blue font-medium' : 'text-text-primary'
                    ]"
                  >
                    All Categories
                  </button>
                </li>
                <li v-for="cat in categoryList" :key="cat.id">
                  <button
                    @click="selectCategory(cat.slug); showMobileFilters = false"
                    :class="[
                      'text-sm w-full text-left py-1',
                      selectedCategory === cat.slug ? 'text-loopymart-blue font-medium' : 'text-text-primary'
                    ]"
                  >
                    {{ cat.name }}
                  </button>
                </li>
              </ul>
            </div>

            <!-- Price Range -->
            <div class="p-4">
              <h3 class="font-medium text-text-primary text-sm mb-3 uppercase">Price</h3>
              <ul class="space-y-2">
                <li v-for="range in priceRanges" :key="range.label">
                  <label class="flex items-center gap-2">
                    <input
                      type="radio"
                      name="mobile-price"
                      :checked="priceRange.min === range.min && priceRange.max === range.max"
                      @change="priceRange = { min: range.min, max: range.max }"
                    />
                    <span class="text-sm text-text-primary">{{ range.label }}</span>
                  </label>
                </li>
              </ul>
            </div>
          </div>

          <!-- Footer -->
          <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-loopymart-gray-dark bg-white">
            <div class="flex gap-3">
              <button 
                @click="clearFilters(); showMobileFilters = false"
                class="flex-1 btn"
              >
                Clear All
              </button>
              <button 
                @click="showMobileFilters = false"
                class="flex-1 btn btn-primary"
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
