<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps({
  product: {
    type: Object,
    required: true
  },
  variant: {
    type: String,
    default: 'grid', // 'grid' | 'horizontal' | 'compact'
  }
})

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  const staticUrl = import.meta.env.VITE_STATIC_URL || ''
  if (url.startsWith('/static/')) return staticUrl + url
  return url
}

const displayPrice = computed(() => {
  return `₹${props.product.price?.toLocaleString('en-IN') || 0}`
})

const originalPrice = computed(() => {
  // Simulate MRP as 20-40% higher than current price for demo
  const mrp = Math.round(props.product.price * (1.2 + Math.random() * 0.2))
  return `₹${mrp.toLocaleString('en-IN')}`
})

const discountPercent = computed(() => {
  // Calculate discount percentage
  const price = props.product.price || 0
  const mrp = Math.round(price * (1.2 + Math.random() * 0.2))
  return Math.round(((mrp - price) / mrp) * 100)
})

const rating = computed(() => {
  // Simulate rating between 3.5 and 5
  return (3.5 + Math.random() * 1.5).toFixed(1)
})

const ratingCount = computed(() => {
  // Simulate review count
  return Math.floor(100 + Math.random() * 10000)
})

const ratingClass = computed(() => {
  const r = parseFloat(rating.value)
  if (r >= 4) return 'rating-high'
  if (r >= 3) return 'rating-medium'
  return 'rating-low'
})

const isAssured = computed(() => {
  // Randomly assign assured status for demo
  return props.product.price > 500
})
</script>

<template>
  <!-- Grid Variant -->
  <RouterLink
    v-if="variant === 'grid'"
    :to="{ name: 'ProductDetail', params: { id: product.id } }"
    class="card card-hover flex flex-col bg-white group"
  >
    <!-- Image Container -->
    <div class="relative p-4 pb-2">
      <div class="aspect-square overflow-hidden flex items-center justify-center bg-white">
        <img
          :src="imageUrl(product.image_url)"
          :alt="product.name"
          class="max-w-full max-h-full object-contain transition-transform duration-300
                 group-hover:scale-105"
        />
      </div>
      <!-- Wishlist Button -->
      <button
        class="absolute top-2 right-2 w-8 h-8 flex items-center justify-center rounded-full
               bg-white shadow-sm hover:shadow-md transition-shadow opacity-0 
               group-hover:opacity-100"
        @click.prevent.stop
      >
        <svg width="20" height="20" class="w-5 h-5 text-text-secondary hover:text-red-500 transition-colors" 
             fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
        </svg>
      </button>
    </div>

    <!-- Product Info -->
    <div class="p-4 pt-2 flex flex-col gap-1.5 flex-1">
      <!-- Brand/Assured Badge -->
      <div class="flex items-center gap-2">
        <span v-if="isAssured" class="flex items-center gap-1">
          <svg width="48" height="16" class="w-12 h-4" viewBox="0 0 48 16">
            <rect width="48" height="16" rx="2" fill="#2874f0"/>
            <text x="4" y="11" fill="white" font-size="8" font-weight="500">ASSURED</text>
          </svg>
        </span>
      </div>

      <!-- Product Name -->
      <h3 class="text-sm text-text-primary line-clamp-2 leading-tight">
        {{ product.name }}
      </h3>

      <!-- Rating -->
      <div class="flex items-center gap-2">
        <span :class="['rating', ratingClass]">
          {{ rating }}
          <svg width="12" height="12" class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
          </svg>
        </span>
        <span class="text-xs text-text-secondary">({{ ratingCount.toLocaleString() }})</span>
      </div>

      <!-- Price Section -->
      <div class="flex items-center gap-2 mt-auto pt-1">
        <span class="text-base font-medium text-text-primary">{{ displayPrice }}</span>
        <span class="price-strike">{{ originalPrice }}</span>
        <span class="price-discount">{{ discountPercent }}% off</span>
      </div>

      <!-- Free Delivery -->
      <p class="text-xs text-text-secondary">Free delivery</p>
    </div>
  </RouterLink>

  <!-- Horizontal Variant (for carousel) -->
  <RouterLink
    v-else-if="variant === 'horizontal'"
    :to="{ name: 'ProductDetail', params: { id: product.id } }"
    class="flex flex-col items-center p-4 min-w-[150px] max-w-[180px] text-center 
           hover:shadow-card-hover transition-shadow group"
  >
    <div class="w-32 h-32 flex items-center justify-center mb-3">
      <img
        :src="imageUrl(product.image_url)"
        :alt="product.name"
        class="max-w-full max-h-full object-contain transition-transform duration-300
               group-hover:scale-105"
      />
    </div>
    <h3 class="text-sm text-text-primary line-clamp-1 mb-1">{{ product.name }}</h3>
    <div class="flex items-center justify-center gap-1 mb-1">
      <span :class="['rating text-[10px] py-0', ratingClass]">
        {{ rating }}
        <svg width="10" height="10" class="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
        </svg>
      </span>
    </div>
    <p class="text-sm font-medium text-text-primary">{{ displayPrice }}</p>
    <p class="text-xs text-loopymart-green">{{ discountPercent }}% off</p>
  </RouterLink>

  <!-- Compact Variant (small cards) -->
  <RouterLink
    v-else-if="variant === 'compact'"
    :to="{ name: 'ProductDetail', params: { id: product.id } }"
    class="flex items-center gap-3 p-3 bg-white rounded-sm hover:shadow-card transition-shadow"
  >
    <div class="w-16 h-16 flex-shrink-0 flex items-center justify-center">
      <img
        :src="imageUrl(product.image_url)"
        :alt="product.name"
        class="max-w-full max-h-full object-contain"
      />
    </div>
    <div class="flex-1 min-w-0">
      <h3 class="text-sm text-text-primary line-clamp-1">{{ product.name }}</h3>
      <p class="text-sm font-medium text-text-primary">{{ displayPrice }}</p>
      <p class="text-xs text-loopymart-green">{{ discountPercent }}% off</p>
    </div>
  </RouterLink>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
