<script setup>
import { ref, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { categories, products } from '@/api'
import BannerCarousel from '@/components/BannerCarousel.vue'
import CategoryStrip from '@/components/CategoryStrip.vue'
import ProductCarousel from '@/components/ProductCarousel.vue'
import ProductCard from '@/components/ProductCard.vue'

const allProducts = ref([])
const categoryList = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [catRes, prodRes] = await Promise.all([
      categories.list(),
      products.list({ limit: 32 }),
    ])
    categoryList.value = catRes.data
    allProducts.value = prodRes.data
  } catch (_) {
    allProducts.value = []
    categoryList.value = []
  } finally {
    loading.value = false
  }
})

// Split products into different sections
const topDeals = computed(() => allProducts.value.slice(0, 8))
const bestSellers = computed(() => allProducts.value.slice(8, 16))
const newArrivals = computed(() => allProducts.value.slice(16, 24))
const trendingProducts = computed(() => allProducts.value.slice(0, 12))
</script>

<template>
  <div class="home-page">
    <!-- Hero Banner Carousel -->
    <BannerCarousel />

    <!-- Category Strip -->
    <CategoryStrip />

    <!-- Loading State -->
    <div v-if="loading" class="py-20 text-center">
      <div class="inline-block w-8 h-8 border-4 border-flipkart-blue border-t-transparent 
                  rounded-full animate-spin"></div>
      <p class="mt-4 text-text-secondary">Loading products...</p>
    </div>

    <template v-else>
      <!-- Top Deals Section -->
      <div class="mt-2.5">
        <ProductCarousel
          v-if="topDeals.length"
          title="Top Deals"
          :products="topDeals"
          view-all-link="/products"
        />
      </div>

      <!-- Deal of the Day - Full Width Banner -->
      <section class="mt-2.5 bg-white shadow-sm">
        <div class="flex flex-col md:flex-row">
          <!-- Left Panel -->
          <div class="md:w-64 p-6 bg-flipkart-blue flex flex-col justify-center items-center 
                      text-white text-center">
            <h2 class="text-xl font-semibold mb-2">Deal of the Day</h2>
            <div class="flex items-center gap-2 text-sm mb-4">
              <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>22 : 15 : 05 Left</span>
            </div>
            <RouterLink 
              to="/products"
              class="px-6 py-2 bg-white text-flipkart-blue font-medium rounded-sm
                     hover:bg-gray-100 transition-colors"
            >
              View All
            </RouterLink>
          </div>

          <!-- Right Panel - Products -->
          <div class="flex-1 flex overflow-x-auto scrollbar-hide">
            <ProductCard
              v-for="product in topDeals.slice(0, 5)"
              :key="product.id"
              :product="product"
              variant="horizontal"
            />
          </div>
        </div>
      </section>

      <!-- Best Sellers Section -->
      <div class="mt-2.5">
        <ProductCarousel
          v-if="bestSellers.length"
          title="Best Sellers"
          :products="bestSellers"
          view-all-link="/products"
        />
      </div>

      <!-- Shop by Category Grid -->
      <section v-if="categoryList.length" class="mt-2.5 bg-white shadow-sm p-6">
        <h2 class="text-xl font-semibold text-text-primary mb-4">Shop by Category</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <RouterLink
            v-for="category in categoryList"
            :key="category.id"
            :to="{ name: 'Products', query: { category: category.slug } }"
            class="flex flex-col items-center p-4 rounded-sm border border-flipkart-gray-dark
                   hover:border-flipkart-blue hover:shadow-card transition-all group"
          >
            <div class="w-16 h-16 mb-3 bg-flipkart-gray rounded-full flex items-center 
                        justify-center text-2xl font-bold text-flipkart-blue
                        group-hover:bg-flipkart-blue group-hover:text-white transition-colors">
              {{ category.name?.charAt(0) }}
            </div>
            <span class="text-sm font-medium text-text-primary text-center
                         group-hover:text-flipkart-blue transition-colors">
              {{ category.name }}
            </span>
          </RouterLink>
        </div>
      </section>

      <!-- New Arrivals Section -->
      <div class="mt-2.5">
        <ProductCarousel
          v-if="newArrivals.length"
          title="New Arrivals"
          :products="newArrivals"
          view-all-link="/products"
        />
      </div>

      <!-- Trending Now - Product Grid -->
      <section v-if="trendingProducts.length" class="mt-2.5 bg-white shadow-sm">
        <div class="section-header">
          <h2 class="section-title">Trending Now</h2>
          <RouterLink 
            to="/products"
            class="text-flipkart-blue text-sm font-medium hover:underline"
          >
            View All
          </RouterLink>
        </div>
        <div class="p-4">
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <ProductCard
              v-for="product in trendingProducts"
              :key="product.id"
              :product="product"
              variant="grid"
            />
          </div>
        </div>
      </section>

      <!-- Promotional Banners -->
      <section class="mt-2.5 grid grid-cols-1 md:grid-cols-2 gap-2.5">
        <div class="bg-gradient-to-r from-purple-500 to-indigo-600 p-8 text-white shadow-sm">
          <h3 class="text-2xl font-bold mb-2">Electronics Sale</h3>
          <p class="text-lg opacity-90 mb-4">Up to 50% off on latest gadgets</p>
          <RouterLink 
            to="/products"
            class="inline-block px-6 py-2 bg-white text-purple-600 font-medium rounded-sm
                   hover:bg-gray-100 transition-colors"
          >
            Shop Now
          </RouterLink>
        </div>
        <div class="bg-gradient-to-r from-rose-500 to-pink-600 p-8 text-white shadow-sm">
          <h3 class="text-2xl font-bold mb-2">Fashion Week</h3>
          <p class="text-lg opacity-90 mb-4">New collections are here</p>
          <RouterLink 
            to="/products"
            class="inline-block px-6 py-2 bg-white text-rose-600 font-medium rounded-sm
                   hover:bg-gray-100 transition-colors"
          >
            Explore
          </RouterLink>
        </div>
      </section>

      <!-- Why Clipkart Section -->
      <section class="mt-2.5 bg-white shadow-sm p-8">
        <h2 class="text-xl font-semibold text-text-primary text-center mb-8">
          Why Shop with Clipkart?
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div class="flex flex-col items-center text-center">
            <div class="w-16 h-16 mb-4 bg-flipkart-gray rounded-full flex items-center 
                        justify-center">
              <svg width="32" height="32" class="w-8 h-8 text-flipkart-blue" fill="none" stroke="currentColor" 
                   viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
            </div>
            <h3 class="font-medium text-text-primary mb-1">Safe Payments</h3>
            <p class="text-sm text-text-secondary">100% secure payments</p>
          </div>
          <div class="flex flex-col items-center text-center">
            <div class="w-16 h-16 mb-4 bg-flipkart-gray rounded-full flex items-center 
                        justify-center">
              <svg width="32" height="32" class="w-8 h-8 text-flipkart-blue" fill="none" stroke="currentColor" 
                   viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
              </svg>
            </div>
            <h3 class="font-medium text-text-primary mb-1">Free Delivery</h3>
            <p class="text-sm text-text-secondary">On orders above ₹499</p>
          </div>
          <div class="flex flex-col items-center text-center">
            <div class="w-16 h-16 mb-4 bg-flipkart-gray rounded-full flex items-center 
                        justify-center">
              <svg width="32" height="32" class="w-8 h-8 text-flipkart-blue" fill="none" stroke="currentColor" 
                   viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
            </div>
            <h3 class="font-medium text-text-primary mb-1">Easy Returns</h3>
            <p class="text-sm text-text-secondary">7 day return policy</p>
          </div>
          <div class="flex flex-col items-center text-center">
            <div class="w-16 h-16 mb-4 bg-flipkart-gray rounded-full flex items-center 
                        justify-center">
              <svg width="32" height="32" class="w-8 h-8 text-flipkart-blue" fill="none" stroke="currentColor" 
                   viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"/>
              </svg>
            </div>
            <h3 class="font-medium text-text-primary mb-1">24/7 Support</h3>
            <p class="text-sm text-text-secondary">Dedicated customer support</p>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
