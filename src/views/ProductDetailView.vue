<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { products, cart } from '@/api'
import client from '@/api/client'

const route = useRoute()
const product = ref(null)
const loading = ref(true)
const quantity = ref(1)
const adding = ref(false)
const message = ref('')
const messageType = ref('success')
const selectedImage = ref(0)

// Ratings
const ratingStats = ref(null)
const reviews = ref([])
const myRating = ref(null)
const userRating = ref(0)
const userReview = ref('')
const submittingRating = ref(false)
const ratingMessage = ref('')
const canRate = ref(false)
const isLoggedIn = computed(() => !!localStorage.getItem('token'))

// Demo product images (single product with zoom simulation)
const productImages = computed(() => {
  if (!product.value) return []
  // Create multiple views from single image for demo
  return [
    product.value.image_url,
    product.value.image_url,
    product.value.image_url,
    product.value.image_url,
  ]
})

onMounted(async () => {
  try {
    const res = await products.get(route.params.id)
    product.value = res.data
    
    const productId = route.params.id
    const [statsRes, reviewsRes] = await Promise.all([
      client.get(`/ratings/product/${productId}/stats`).catch(() => ({ data: null })),
      client.get(`/ratings/product/${productId}`).catch(() => ({ data: { ratings: [] } })),
    ])
    
    ratingStats.value = statsRes.data
    reviews.value = reviewsRes.data?.ratings || []
    
    if (isLoggedIn.value) {
      const [myRatingRes] = await Promise.all([
        client.get(`/ratings/my-rating/${productId}`).catch(() => ({ data: null })),
      ])
      
      if (myRatingRes.data) {
        myRating.value = myRatingRes.data
        userRating.value = myRatingRes.data.rating
        userReview.value = myRatingRes.data.review || ''
      }
      
      const ordersRes = await client.get('/orders').catch(() => ({ data: [] }))
      const hasPurchased = ordersRes.data.some(order => 
        order.status === 'delivered' && 
        order.items?.some(item => item.product_id === productId)
      )
      canRate.value = hasPurchased
    }
  } catch (_) {
    product.value = null
  } finally {
    loading.value = false
  }
})

const maxQty = computed(() => product.value ? Math.max(1, product.value.stock) : 1)

const displayPrice = computed(() => {
  return `₹${product.value?.price?.toLocaleString('en-IN') || 0}`
})

const originalPrice = computed(() => {
  const mrp = Math.round((product.value?.price || 0) * 1.3)
  return `₹${mrp.toLocaleString('en-IN')}`
})

const discountPercent = computed(() => {
  const price = product.value?.price || 0
  const mrp = Math.round(price * 1.3)
  return Math.round(((mrp - price) / mrp) * 100)
})

const averageRating = computed(() => {
  return ratingStats.value?.average_rating?.toFixed(1) || '0.0'
})

const totalRatings = computed(() => {
  return ratingStats.value?.total_ratings || 0
})

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
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
    message.value = 'Added to cart successfully!'
    messageType.value = 'success'
  } catch (e) {
    message.value = e.response?.data?.detail || 'Failed to add to cart'
    messageType.value = 'error'
  } finally {
    adding.value = false
  }
}

function setRating(star) {
  userRating.value = star
}

async function submitRating() {
  if (!userRating.value) {
    ratingMessage.value = 'Please select a rating'
    return
  }
  
  submittingRating.value = true
  ratingMessage.value = ''
  
  try {
    await client.post('/ratings', {
      product_id: route.params.id,
      rating: userRating.value,
      review: userReview.value || null,
    })
    
    ratingMessage.value = myRating.value ? 'Rating updated!' : 'Rating submitted!'
    myRating.value = { rating: userRating.value, review: userReview.value }
    
    const [statsRes, reviewsRes] = await Promise.all([
      client.get(`/ratings/product/${route.params.id}/stats`),
      client.get(`/ratings/product/${route.params.id}`),
    ])
    ratingStats.value = statsRes.data
    reviews.value = reviewsRes.data?.ratings || []
  } catch (e) {
    ratingMessage.value = e.response?.data?.detail || 'Failed to submit rating'
  } finally {
    submittingRating.value = false
  }
}

function getRatingBarWidth(stars) {
  if (!ratingStats.value || totalRatings.value === 0) return 0
  const count = ratingStats.value.rating_distribution?.[stars] || 0
  return (count / totalRatings.value) * 100
}
</script>

<template>
  <div class="min-h-screen bg-flipkart-gray py-4">
    <div class="max-w-container mx-auto px-4">
      <!-- Loading State -->
      <div v-if="loading" class="bg-white shadow-card rounded-sm p-12 text-center">
        <div class="inline-block w-8 h-8 border-4 border-flipkart-blue border-t-transparent 
                    rounded-full animate-spin"></div>
        <p class="mt-4 text-text-secondary">Loading product...</p>
      </div>

      <!-- Not Found State -->
      <div v-else-if="!product" class="bg-white shadow-card rounded-sm p-12 text-center">
        <svg width="64" height="64" class="w-16 h-16 mx-auto text-text-hint mb-4" fill="none" stroke="currentColor" 
             viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <h2 class="text-lg font-medium text-text-primary mb-2">Product not found</h2>
        <RouterLink to="/products" class="btn btn-primary">Browse Products</RouterLink>
      </div>

      <!-- Product Content -->
      <template v-else>
        <!-- Breadcrumb -->
        <nav class="text-sm text-text-secondary mb-4">
          <RouterLink to="/" class="hover:text-flipkart-blue">Home</RouterLink>
          <span class="mx-2">&gt;</span>
          <RouterLink to="/products" class="hover:text-flipkart-blue">Products</RouterLink>
          <span class="mx-2">&gt;</span>
          <span class="text-text-primary">{{ product.name }}</span>
        </nav>

        <div class="flex flex-col lg:flex-row gap-4">
          <!-- Left Column - Image Gallery -->
          <div class="lg:w-[40%]">
            <div class="bg-white shadow-card rounded-sm sticky top-32">
              <!-- Main Image -->
              <div class="relative p-4">
                <div class="aspect-square flex items-center justify-center bg-white">
                  <img
                    :src="imageUrl(productImages[selectedImage])"
                    :alt="product.name"
                    class="max-w-full max-h-full object-contain"
                  />
                </div>
                <!-- Wishlist Button -->
                <button class="absolute top-4 right-4 w-10 h-10 flex items-center justify-center 
                               rounded-full border border-flipkart-gray-dark bg-white 
                               hover:border-flipkart-blue transition-colors">
                  <svg width="20" height="20" class="w-5 h-5 text-text-secondary hover:text-red-500" 
                       fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                  </svg>
                </button>
              </div>

              <!-- Thumbnail Strip -->
              <div class="flex gap-2 p-4 pt-0 overflow-x-auto">
                <button
                  v-for="(img, index) in productImages"
                  :key="index"
                  @click="selectedImage = index"
                  :class="[
                    'w-16 h-16 flex-shrink-0 border rounded-sm p-1 transition-colors',
                    selectedImage === index 
                      ? 'border-flipkart-blue' 
                      : 'border-flipkart-gray-dark hover:border-flipkart-blue'
                  ]"
                >
                  <img
                    :src="imageUrl(img)"
                    :alt="`${product.name} view ${index + 1}`"
                    class="w-full h-full object-contain"
                  />
                </button>
              </div>

              <!-- Action Buttons -->
              <div class="flex gap-3 p-4 border-t border-flipkart-gray-dark">
                <button
                  @click="addToCart"
                  :disabled="adding || product.stock < 1"
                  class="flex-1 btn btn-lg bg-flipkart-orange text-white border-flipkart-orange 
                         hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
                  </svg>
                  {{ adding ? 'ADDING...' : 'ADD TO CART' }}
                </button>
                <RouterLink
                  to="/checkout"
                  class="flex-1 btn btn-lg btn-primary flex items-center justify-center gap-2"
                >
                  <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                  BUY NOW
                </RouterLink>
              </div>

              <!-- Message -->
              <div 
                v-if="message" 
                :class="[
                  'mx-4 mb-4 p-3 rounded-sm text-sm',
                  messageType === 'success' 
                    ? 'bg-green-50 text-flipkart-green' 
                    : 'bg-red-50 text-red-600'
                ]"
              >
                {{ message }}
              </div>
            </div>
          </div>

          <!-- Right Column - Product Info -->
          <div class="lg:flex-1">
            <div class="bg-white shadow-card rounded-sm p-6">
              <!-- Product Title -->
              <h1 class="text-xl font-medium text-text-primary mb-2">
                {{ product.name }}
              </h1>

              <!-- Rating Summary -->
              <div class="flex items-center gap-3 mb-4">
                <span 
                  v-if="ratingStats"
                  class="inline-flex items-center gap-1 px-2 py-0.5 bg-flipkart-green 
                         text-white text-sm font-medium rounded-sm"
                >
                  {{ averageRating }}
                  <svg width="12" height="12" class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                  </svg>
                </span>
                <span class="text-text-secondary text-sm">
                  {{ totalRatings }} Ratings & {{ reviews.length }} Reviews
                </span>
                <span 
                  v-if="product.stock > 0 && product.stock <= 10"
                  class="ml-auto px-2 py-0.5 bg-red-100 text-red-600 text-xs font-medium rounded-sm"
                >
                  Only {{ product.stock }} left
                </span>
              </div>

              <!-- Price Section -->
              <div class="py-4 border-t border-flipkart-gray-dark">
                <div class="flex items-baseline gap-3">
                  <span class="text-3xl font-medium text-text-primary">{{ displayPrice }}</span>
                  <span class="text-lg text-text-secondary line-through">{{ originalPrice }}</span>
                  <span class="text-lg text-flipkart-green font-medium">
                    {{ discountPercent }}% off
                  </span>
                </div>
                <p class="text-sm text-flipkart-green mt-1">inclusive of all taxes</p>
              </div>

              <!-- Offers -->
              <div class="py-4 border-t border-flipkart-gray-dark">
                <h3 class="font-medium text-text-primary mb-3">Available Offers</h3>
                <ul class="space-y-2">
                  <li class="flex items-start gap-2 text-sm">
                    <svg width="16" height="16" class="w-4 h-4 text-flipkart-green flex-shrink-0 mt-0.5" 
                         fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z"/>
                    </svg>
                    <span><strong>Bank Offer:</strong> 10% off on HDFC Bank Credit Card EMI</span>
                  </li>
                  <li class="flex items-start gap-2 text-sm">
                    <svg width="16" height="16" class="w-4 h-4 text-flipkart-green flex-shrink-0 mt-0.5" 
                         fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z"/>
                    </svg>
                    <span><strong>Special Price:</strong> Get extra 5% off (price inclusive)</span>
                  </li>
                  <li class="flex items-start gap-2 text-sm">
                    <svg width="16" height="16" class="w-4 h-4 text-flipkart-green flex-shrink-0 mt-0.5" 
                         fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z"/>
                    </svg>
                    <span><strong>Partner Offer:</strong> Sign up for Clipkart Pay Later & get free gift</span>
                  </li>
                </ul>
              </div>

              <!-- Quantity Selector -->
              <div class="py-4 border-t border-flipkart-gray-dark">
                <div class="flex items-center gap-4">
                  <label class="text-sm text-text-secondary">Quantity:</label>
                  <div class="flex items-center border border-flipkart-gray-dark rounded-sm">
                    <button
                      @click="quantity = Math.max(1, quantity - 1)"
                      class="w-10 h-10 flex items-center justify-center text-text-primary 
                             hover:bg-flipkart-gray transition-colors"
                    >
                      <svg width="16" height="16" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"/>
                      </svg>
                    </button>
                    <input
                      v-model.number="quantity"
                      type="number"
                      min="1"
                      :max="maxQty"
                      class="w-16 h-10 text-center border-x border-flipkart-gray-dark text-sm
                             focus:outline-none"
                    />
                    <button
                      @click="quantity = Math.min(maxQty, quantity + 1)"
                      class="w-10 h-10 flex items-center justify-center text-text-primary 
                             hover:bg-flipkart-gray transition-colors"
                    >
                      <svg width="16" height="16" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                      </svg>
                    </button>
                  </div>
                  <span 
                    v-if="product.stock < 1" 
                    class="text-red-500 text-sm"
                  >
                    Out of Stock
                  </span>
                  <span 
                    v-else
                    class="text-flipkart-green text-sm"
                  >
                    In Stock ({{ product.stock }} available)
                  </span>
                </div>
              </div>

              <!-- Delivery -->
              <div class="py-4 border-t border-flipkart-gray-dark">
                <div class="flex items-start gap-4">
                  <svg width="20" height="20" class="w-5 h-5 text-text-secondary flex-shrink-0" fill="none" 
                       stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                  <div>
                    <p class="text-sm text-text-primary font-medium">
                      Delivery by Tomorrow
                    </p>
                    <p class="text-sm text-text-secondary">
                      Free delivery on orders above ₹499
                    </p>
                  </div>
                </div>
              </div>

              <!-- Description -->
              <div v-if="product.description" class="py-4 border-t border-flipkart-gray-dark">
                <h3 class="font-medium text-text-primary mb-3">Product Description</h3>
                <p class="text-sm text-text-secondary leading-relaxed">
                  {{ product.description }}
                </p>
              </div>

              <!-- Services -->
              <div class="py-4 border-t border-flipkart-gray-dark">
                <div class="grid grid-cols-3 gap-4">
                  <div class="flex flex-col items-center text-center">
                    <svg width="32" height="32" class="w-8 h-8 text-text-secondary mb-2" fill="none" stroke="currentColor" 
                         viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
                            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                    </svg>
                    <span class="text-xs text-text-secondary">7 Day Replacement</span>
                  </div>
                  <div class="flex flex-col items-center text-center">
                    <svg width="32" height="32" class="w-8 h-8 text-text-secondary mb-2" fill="none" stroke="currentColor" 
                         viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
                            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                    </svg>
                    <span class="text-xs text-text-secondary">Secure Transaction</span>
                  </div>
                  <div class="flex flex-col items-center text-center">
                    <svg width="32" height="32" class="w-8 h-8 text-text-secondary mb-2" fill="none" stroke="currentColor" 
                         viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
                            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                    </svg>
                    <span class="text-xs text-text-secondary">Free Delivery</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Ratings & Reviews Section -->
            <div class="bg-white shadow-card rounded-sm mt-4 p-6">
              <h2 class="text-lg font-medium text-text-primary mb-4">
                Ratings & Reviews
              </h2>

              <!-- Rating Overview -->
              <div class="flex flex-col sm:flex-row gap-6 pb-6 border-b border-flipkart-gray-dark">
                <!-- Average Rating -->
                <div class="text-center sm:pr-6 sm:border-r sm:border-flipkart-gray-dark">
                  <div class="text-4xl font-medium text-text-primary">
                    {{ averageRating }}
                  </div>
                  <div class="flex justify-center gap-1 my-2">
                    <svg 
                      v-for="star in 5" 
                      :key="star"
                      width="16" height="16"
                      :class="[
                        'w-4 h-4',
                        star <= Math.round(parseFloat(averageRating))
                          ? 'text-flipkart-green'
                          : 'text-flipkart-gray-dark'
                      ]"
                      fill="currentColor" viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                    </svg>
                  </div>
                  <p class="text-sm text-text-secondary">
                    {{ totalRatings }} ratings
                  </p>
                </div>

                <!-- Rating Bars -->
                <div class="flex-1 space-y-2">
                  <div v-for="star in [5, 4, 3, 2, 1]" :key="star" class="flex items-center gap-2">
                    <span class="text-sm text-text-secondary w-4">{{ star }}</span>
                    <svg width="12" height="12" class="w-3 h-3 text-flipkart-green" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                    </svg>
                    <div class="flex-1 h-1.5 bg-flipkart-gray rounded-full overflow-hidden">
                      <div 
                        class="h-full bg-flipkart-green transition-all duration-300"
                        :style="{ width: `${getRatingBarWidth(star)}%` }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Rate This Product -->
              <div v-if="isLoggedIn && canRate" class="py-6 border-b border-flipkart-gray-dark">
                <h3 class="font-medium text-text-primary mb-4">
                  {{ myRating ? 'Update Your Rating' : 'Rate This Product' }}
                </h3>
                <div class="flex items-center gap-4 mb-4">
                  <div class="flex gap-1">
                    <button
                      v-for="star in 5"
                      :key="star"
                      @click="setRating(star)"
                      class="p-1 transition-transform hover:scale-110"
                    >
                      <svg 
                        width="32" height="32"
                        :class="[
                          'w-8 h-8 transition-colors',
                          star <= userRating ? 'text-flipkart-orange' : 'text-flipkart-gray-dark'
                        ]"
                        fill="currentColor" viewBox="0 0 20 20"
                      >
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                      </svg>
                    </button>
                  </div>
                  <span class="text-sm text-text-secondary">
                    {{ userRating > 0 ? `${userRating} out of 5` : 'Click to rate' }}
                  </span>
                </div>
                <textarea
                  v-model="userReview"
                  placeholder="Share your experience with this product..."
                  class="form-input resize-none mb-4"
                  rows="3"
                ></textarea>
                <button
                  @click="submitRating"
                  :disabled="submittingRating || !userRating"
                  class="btn btn-primary"
                >
                  {{ submittingRating ? 'Submitting...' : (myRating ? 'Update Rating' : 'Submit Rating') }}
                </button>
                <p 
                  v-if="ratingMessage" 
                  :class="[
                    'mt-2 text-sm',
                    ratingMessage.includes('Failed') ? 'text-red-500' : 'text-flipkart-green'
                  ]"
                >
                  {{ ratingMessage }}
                </p>
              </div>

              <div v-else-if="isLoggedIn && !canRate" class="py-6 border-b border-flipkart-gray-dark">
                <p class="text-text-secondary text-sm">
                  Purchase and receive this product to leave a rating.
                </p>
              </div>

              <div v-else class="py-6 border-b border-flipkart-gray-dark">
                <p class="text-text-secondary text-sm">
                  <RouterLink :to="'/login?redirect=' + $route.fullPath" class="text-flipkart-blue">
                    Login
                  </RouterLink>
                  to rate this product.
                </p>
              </div>

              <!-- Reviews List -->
              <div class="pt-6">
                <h3 class="font-medium text-text-primary mb-4">Customer Reviews</h3>
                <div v-if="reviews.length === 0" class="text-text-secondary text-sm">
                  No reviews yet. Be the first to review!
                </div>
                <div v-else class="space-y-4">
                  <div 
                    v-for="review in reviews" 
                    :key="review.id" 
                    class="pb-4 border-b border-flipkart-gray-dark last:border-b-0"
                  >
                    <div class="flex items-center gap-3 mb-2">
                      <span 
                        :class="[
                          'inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm text-xs text-white',
                          review.rating >= 4 ? 'bg-flipkart-green' : 
                          review.rating >= 3 ? 'bg-flipkart-orange' : 'bg-red-500'
                        ]"
                      >
                        {{ review.rating }}
                        <svg width="10" height="10" class="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                        </svg>
                      </span>
                      <span class="text-xs text-text-hint">
                        {{ new Date(review.created_at).toLocaleDateString('en-IN', { 
                          year: 'numeric', month: 'short', day: 'numeric' 
                        }) }}
                      </span>
                    </div>
                    <p v-if="review.review" class="text-sm text-text-primary">
                      {{ review.review }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
