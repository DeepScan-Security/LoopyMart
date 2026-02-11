<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { products, cart } from '@/api'
import client from '@/api/client'

const route = useRoute()
const product = ref(null)
const loading = ref(true)
const quantity = ref(1)
const adding = ref(false)
const message = ref('')

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

onMounted(async () => {
  try {
    const res = await products.get(route.params.id)
    product.value = res.data
    
    // Fetch ratings data in parallel
    const productId = route.params.id
    const [statsRes, reviewsRes] = await Promise.all([
      client.get(`/ratings/product/${productId}/stats`).catch(() => ({ data: null })),
      client.get(`/ratings/product/${productId}`).catch(() => ({ data: { ratings: [] } })),
    ])
    
    ratingStats.value = statsRes.data
    reviews.value = reviewsRes.data?.ratings || []
    
    // If logged in, check if user can rate and get their existing rating
    if (isLoggedIn.value) {
      const [myRatingRes] = await Promise.all([
        client.get(`/ratings/my-rating/${productId}`).catch(() => ({ data: null })),
      ])
      
      if (myRatingRes.data) {
        myRating.value = myRatingRes.data
        userRating.value = myRatingRes.data.rating
        userReview.value = myRatingRes.data.review || ''
      }
      
      // Check if user has purchased this product (can rate)
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
    
    // Refresh rating stats and reviews
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
</script>

<template>
  <div class="product-detail">
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="!product" class="empty">Product not found.</div>
    <div v-else>
      <div class="detail-grid">
        <div class="image-wrap card">
          <img :src="imageUrl(product.image_url)" :alt="product.name" />
        </div>
        <div class="info">
          <h1>{{ product.name }}</h1>
          
          <!-- Rating Stars Display -->
          <div v-if="ratingStats" class="rating-display">
            <div class="stars">
              <span 
                v-for="star in 5" 
                :key="star" 
                class="star"
                :class="{ filled: star <= Math.round(ratingStats.average_rating) }"
              >★</span>
            </div>
            <span class="rating-text">
              {{ ratingStats.average_rating.toFixed(1) }} 
              ({{ ratingStats.total_ratings }} {{ ratingStats.total_ratings === 1 ? 'review' : 'reviews' }})
            </span>
          </div>
          <div v-else class="rating-display no-ratings">
            <span class="rating-text">No ratings yet</span>
          </div>
          
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
      
      <!-- Ratings & Reviews Section -->
      <div class="ratings-section card">
        <h2>Ratings & Reviews</h2>
        
        <!-- Rate This Product (if logged in and purchased) -->
        <div v-if="isLoggedIn && canRate" class="rate-product">
          <h3>{{ myRating ? 'Update Your Rating' : 'Rate This Product' }}</h3>
          <div class="rating-input">
            <div class="star-input">
              <span 
                v-for="star in 5" 
                :key="star" 
                class="star clickable"
                :class="{ filled: star <= userRating, hover: star <= userRating }"
                @click="setRating(star)"
                @mouseenter="userRating = star"
              >★</span>
            </div>
            <span class="rating-label">{{ userRating > 0 ? userRating + ' out of 5' : 'Click to rate' }}</span>
          </div>
          <div class="form-group">
            <label>Write a review (optional)</label>
            <textarea 
              v-model="userReview" 
              placeholder="Share your experience with this product..."
              rows="3"
            ></textarea>
          </div>
          <button 
            class="btn btn-primary" 
            :disabled="submittingRating || !userRating"
            @click="submitRating"
          >
            {{ submittingRating ? 'Submitting...' : (myRating ? 'Update Rating' : 'Submit Rating') }}
          </button>
          <p v-if="ratingMessage" class="rating-message" :class="{ error: ratingMessage.includes('Failed') }">
            {{ ratingMessage }}
          </p>
        </div>
        
        <div v-else-if="isLoggedIn && !canRate" class="rate-notice">
          <p>Purchase and receive this product to leave a rating.</p>
        </div>
        
        <div v-else class="rate-notice">
          <p>
            <router-link :to="'/login?redirect=' + $route.fullPath">Login</router-link> 
            to rate this product.
          </p>
        </div>
        
        <!-- Reviews List -->
        <div class="reviews-list">
          <h3>Customer Reviews</h3>
          <div v-if="reviews.length === 0" class="no-reviews">
            No reviews yet. Be the first to review!
          </div>
          <div v-else>
            <div v-for="review in reviews" :key="review.id" class="review-item">
              <div class="review-header">
                <div class="review-stars">
                  <span 
                    v-for="star in 5" 
                    :key="star" 
                    class="star small"
                    :class="{ filled: star <= review.rating }"
                  >★</span>
                </div>
                <span class="review-date">
                  {{ new Date(review.created_at).toLocaleDateString() }}
                </span>
              </div>
              <p v-if="review.review" class="review-text">{{ review.review }}</p>
            </div>
          </div>
        </div>
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

/* Rating Display */
.rating-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.rating-display.no-ratings {
  color: #999;
}

.stars {
  display: flex;
  gap: 2px;
}

.star {
  color: #ddd;
  font-size: 1.2rem;
  line-height: 1;
}

.star.filled {
  color: #ffc107;
}

.star.small {
  font-size: 0.9rem;
}

.rating-text {
  color: #666;
  font-size: 0.9rem;
}

/* Ratings Section */
.ratings-section {
  margin-top: 2rem;
  padding: 1.5rem;
}

.ratings-section h2 {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #eee;
}

.ratings-section h3 {
  font-size: 1rem;
  margin-bottom: 1rem;
}

/* Rate Product */
.rate-product {
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.rating-input {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.star-input {
  display: flex;
  gap: 4px;
}

.star.clickable {
  cursor: pointer;
  font-size: 1.75rem;
  transition: transform 0.1s, color 0.1s;
}

.star.clickable:hover {
  transform: scale(1.1);
}

.rating-label {
  color: #666;
  font-size: 0.9rem;
}

.rate-product .form-group {
  max-width: 100%;
  margin-bottom: 1rem;
}

.rate-product textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
  resize: vertical;
}

.rating-message {
  margin-top: 0.75rem;
  font-size: 0.9rem;
  color: #10b981;
}

.rating-message.error {
  color: #e53e3e;
}

.rate-notice {
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 2rem;
  color: #666;
}

.rate-notice a {
  color: #2874f0;
  text-decoration: none;
}

/* Reviews List */
.reviews-list {
  margin-top: 1.5rem;
}

.no-reviews {
  color: #999;
  font-style: italic;
  padding: 1rem 0;
}

.review-item {
  padding: 1rem 0;
  border-bottom: 1px solid #eee;
}

.review-item:last-child {
  border-bottom: none;
}

.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.review-stars {
  display: flex;
  gap: 2px;
}

.review-date {
  color: #999;
  font-size: 0.85rem;
}

.review-text {
  color: #555;
  line-height: 1.5;
  margin: 0;
}
</style>
