<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { cart, orders, addresses as addressesApi } from '@/api'
import client from '@/api/client'

const router = useRouter()
const items = ref([])
const INDIA_STATES = [
  'Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar',
  'Chandigarh', 'Chhattisgarh', 'Dadra and Nagar Haveli and Daman and Diu', 'Delhi',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jammu and Kashmir', 'Jharkhand',
  'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep', 'Madhya Pradesh', 'Maharashtra',
  'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry', 'Punjab',
  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh',
  'Uttarakhand', 'West Bengal',
]

const shippingAddress = ref({
  full_name: '',
  phone: '',
  pincode: '',
  address_line1: '',
  address_line2: '',
  landmark: '',
  city: '',
  state: '',
  country: 'India',
  address_type: 'Home',
})
const addressErrors = ref({})
const loading = ref(true)
const submitting = ref(false)
const error = ref('')

// Checkout steps
const currentStep = ref(1) // 1: Address, 2: Payment, 3: Review

// Saved addresses
const savedAddresses = ref([])
const selectedSavedAddressId = ref(null)
const saveAddressForNextTime = ref(false)

function selectSavedAddress(addr) {
  selectedSavedAddressId.value = addr.id
  shippingAddress.value = {
    full_name: addr.full_name || '',
    phone: addr.phone || '',
    pincode: addr.pincode || '',
    address_line1: addr.address_line1 || '',
    address_line2: addr.address_line2 || '',
    landmark: addr.landmark || '',
    city: addr.city || '',
    state: addr.state || '',
    country: addr.country || 'India',
    address_type: addr.address_type || 'Home',
  }
  addressErrors.value = {}
}

// Payment state
const paymentMethod = ref('wallet')
const walletBalance = ref(0)
const selectedCoupon = ref(null)
const coupons = ref([])
const couponDiscount = ref(0)
const showCoupons = ref(false)

onMounted(async () => {
  try {
    const [cartRes, walletRes, couponsRes, addrRes] = await Promise.all([
      cart.list(),
      client.get('/payments/wallet/balance'),
      client.get('/payments/coupons'),
      addressesApi.list().catch(() => ({ data: [] })),
    ])
    items.value = cartRes.data
    walletBalance.value = walletRes.data.balance
    coupons.value = couponsRes.data
    savedAddresses.value = addrRes.data
    // Auto-fill the default address if present
    const defaultAddr = addrRes.data.find(a => a.is_default)
    if (defaultAddr) {
      selectSavedAddress(defaultAddr)
    }
  } catch (_) {
    items.value = []
  } finally {
    loading.value = false
  }
})

const subtotal = computed(() =>
  items.value.reduce((s, i) => s + i.product_price * i.quantity, 0)
)

const totalItems = computed(() =>
  items.value.reduce((s, i) => s + i.quantity, 0)
)

const discount = computed(() => Math.round(subtotal.value * 0.1) + couponDiscount.value)
const deliveryCharges = computed(() => subtotal.value > 499 ? 0 : 40)
const total = computed(() => Math.max(0, subtotal.value - discount.value + deliveryCharges.value))

const addressSummary = computed(() => {
  const a = shippingAddress.value
  if (!a.full_name) return ''
  return [
    `${a.full_name} · ${a.phone}`,
    a.address_line1 + (a.address_line2 ? ', ' + a.address_line2 : ''),
    a.landmark ? 'Near ' + a.landmark : '',
    `${a.city}, ${a.state} – ${a.pincode}`,
    a.country,
  ].filter(Boolean).join('\n')
})

function validateAddress() {
  const errors = {}
  const a = shippingAddress.value
  if (!a.full_name.trim()) errors.full_name = 'Full name is required'
  if (!/^\d{10}$/.test(a.phone.trim())) errors.phone = 'Enter a valid 10-digit phone number'
  if (!/^\d{6}$/.test(a.pincode.trim())) errors.pincode = 'Enter a valid 6-digit PIN code'
  if (!a.address_line1.trim()) errors.address_line1 = 'Address is required'
  if (!a.city.trim()) errors.city = 'City / Town is required'
  if (!a.state.trim()) errors.state = 'State is required'
  addressErrors.value = errors
  return Object.keys(errors).length === 0
}

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  const staticUrl = import.meta.env.VITE_STATIC_URL || ''
  if (url.startsWith('/static/')) return staticUrl + url
  return url
}

async function applyCoupon(coupon) {
  if (coupon.is_used) {
    error.value = 'Coupon already used'
    return
  }
  
  try {
    const res = await client.post('/payments/coupon/apply', { coupon_code: coupon.code })
    if (res.data.is_valid) {
      selectedCoupon.value = coupon
      couponDiscount.value = res.data.discount
      showCoupons.value = false
      error.value = ''
    } else {
      error.value = res.data.message
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to apply coupon'
  }
}

function removeCoupon() {
  selectedCoupon.value = null
  couponDiscount.value = 0
}

function proceedToPayment() {
  if (!validateAddress()) {
    error.value = 'Please fill in all required address fields'
    return
  }
  error.value = ''
  currentStep.value = 2
}

function proceedToReview() {
  error.value = ''
  currentStep.value = 3
}

async function placeOrder() {
  if (paymentMethod.value === 'wallet' && walletBalance.value < total.value) {
    error.value = 'Insufficient wallet balance'
    return
  }
  
  submitting.value = true
  error.value = ''
  
  try {
    // Optionally save address before placing
    if (saveAddressForNextTime.value && !selectedSavedAddressId.value) {
      try {
        await addressesApi.create({ ...shippingAddress.value })
      } catch (_) { /* non-fatal */ }
    }

    const orderRes = await orders.create({ shipping_address: shippingAddress.value })
    const orderId = orderRes.data.id
    
    const paymentRes = await client.post('/payments/dummy-pay', {
      order_id: orderId,
      amount: total.value,
      payment_method: paymentMethod.value,
      coupon_code: selectedCoupon.value?.code || null,
    })
    
    if (paymentRes.data.status === 'SUCCESS') {
      sessionStorage.setItem('cartCount', '0')
      router.push({ name: 'Orders' })
    } else {
      error.value = 'Payment failed. Please try again.'
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to place order'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-loopymart-gray py-4">
    <div class="max-w-container mx-auto px-4">
      <!-- Loading State -->
      <div v-if="loading" class="bg-white shadow-card rounded-sm p-12 text-center">
        <div class="inline-block w-8 h-8 border-4 border-loopymart-blue border-t-transparent 
                    rounded-full animate-spin"></div>
        <p class="mt-4 text-text-secondary">Loading checkout...</p>
      </div>

      <!-- Empty Cart -->
      <div v-else-if="!items.length" class="bg-white shadow-card rounded-sm p-12 text-center">
        <svg width="96" height="96" class="w-24 h-24 mx-auto text-text-hint mb-4" fill="none" stroke="currentColor" 
             viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" 
                d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
        </svg>
        <h2 class="text-xl font-medium text-text-primary mb-2">Your cart is empty!</h2>
        <p class="text-text-secondary mb-6">Add items to proceed with checkout.</p>
        <RouterLink to="/products" class="btn btn-primary btn-lg">
          Shop Now
        </RouterLink>
      </div>

      <!-- Checkout Content -->
      <div v-else class="flex flex-col lg:flex-row gap-4">
        <!-- Left Column - Checkout Steps -->
        <div class="flex-1 min-w-0 space-y-4">
          <!-- Step 1: Delivery Address -->
          <div class="bg-white shadow-card rounded-sm">
            <div 
              :class="[
                'flex items-center gap-3 p-4',
                currentStep === 1 ? 'bg-loopymart-blue text-white' : 'border-b border-loopymart-gray-dark'
              ]"
            >
              <span 
                :class="[
                  'w-6 h-6 flex items-center justify-center rounded-sm text-sm font-medium',
                  currentStep === 1 ? 'bg-white text-loopymart-blue' : 'bg-loopymart-gray text-text-secondary'
                ]"
              >
                1
              </span>
              <span class="font-medium">DELIVERY ADDRESS</span>
              <span 
                v-if="currentStep > 1 && shippingAddress.full_name" 
                class="ml-auto text-sm text-loopymart-blue cursor-pointer"
                @click="currentStep = 1; error = ''"
              >
                Change
              </span>
            </div>

            <div v-if="currentStep === 1" class="p-4">
              <!-- Field error banner -->
              <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm">
                {{ error }}
              </div>

              <!-- Saved addresses selector -->
              <div v-if="savedAddresses.length" class="mb-5">
                <p class="form-label mb-2">Saved Addresses</p>
                <div class="space-y-2">
                  <label
                    v-for="addr in savedAddresses"
                    :key="addr.id"
                    :class="[
                      'flex items-start gap-3 p-3 border rounded-sm cursor-pointer transition-colors',
                      selectedSavedAddressId === addr.id
                        ? 'border-loopymart-blue bg-blue-50'
                        : 'border-loopymart-gray-dark hover:border-loopymart-blue'
                    ]"
                  >
                    <input
                      type="radio"
                      :value="addr.id"
                      v-model="selectedSavedAddressId"
                      @change="selectSavedAddress(addr)"
                      class="mt-0.5 text-loopymart-blue"
                    />
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2">
                        <span class="font-medium text-sm text-text-primary">{{ addr.full_name }}</span>
                        <span class="text-xs px-1.5 py-0.5 bg-loopymart-gray rounded text-text-secondary">
                          {{ addr.address_type }}
                        </span>
                        <span v-if="addr.is_default"
                              class="text-xs px-1.5 py-0.5 bg-loopymart-blue text-white rounded">
                          Default
                        </span>
                      </div>
                      <p class="text-xs text-text-secondary mt-0.5">
                        {{ addr.address_line1 }}<span v-if="addr.address_line2">, {{ addr.address_line2 }}</span>,
                        {{ addr.city }}, {{ addr.state }} &ndash; {{ addr.pincode }}
                      </p>
                      <p class="text-xs text-text-secondary">{{ addr.phone }}</p>
                    </div>
                  </label>
                </div>
                <div class="my-3 flex items-center gap-2">
                  <hr class="flex-1 border-loopymart-gray-dark" />
                  <span class="text-xs text-text-secondary">or enter a new address</span>
                  <hr class="flex-1 border-loopymart-gray-dark" />
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <!-- Full Name -->
                <div>
                  <label class="form-label">Full Name <span class="text-red-500">*</span></label>
                  <input
                    v-model="shippingAddress.full_name"
                    type="text"
                    placeholder="First and last name"
                    :class="['form-input', addressErrors.full_name ? 'border-red-400 focus:ring-red-300' : '']"
                  />
                  <p v-if="addressErrors.full_name" class="mt-1 text-xs text-red-500">{{ addressErrors.full_name }}</p>
                </div>

                <!-- Phone -->
                <div>
                  <label class="form-label">Mobile Number <span class="text-red-500">*</span></label>
                  <input
                    v-model="shippingAddress.phone"
                    type="tel"
                    placeholder="10-digit mobile number"
                    maxlength="10"
                    :class="['form-input', addressErrors.phone ? 'border-red-400 focus:ring-red-300' : '']"
                  />
                  <p v-if="addressErrors.phone" class="mt-1 text-xs text-red-500">{{ addressErrors.phone }}</p>
                </div>

                <!-- PIN Code -->
                <div>
                  <label class="form-label">PIN Code <span class="text-red-500">*</span></label>
                  <input
                    v-model="shippingAddress.pincode"
                    type="text"
                    placeholder="6-digit PIN code"
                    maxlength="6"
                    :class="['form-input', addressErrors.pincode ? 'border-red-400 focus:ring-red-300' : '']"
                  />
                  <p v-if="addressErrors.pincode" class="mt-1 text-xs text-red-500">{{ addressErrors.pincode }}</p>
                </div>

                <!-- Address Line 1 -->
                <div class="sm:col-span-2">
                  <label class="form-label">Address (House No., Building, Flat) <span class="text-red-500">*</span></label>
                  <input
                    v-model="shippingAddress.address_line1"
                    type="text"
                    placeholder="House no., Building, Company, Apartment"
                    :class="['form-input', addressErrors.address_line1 ? 'border-red-400 focus:ring-red-300' : '']"
                  />
                  <p v-if="addressErrors.address_line1" class="mt-1 text-xs text-red-500">{{ addressErrors.address_line1 }}</p>
                </div>

                <!-- Address Line 2 -->
                <div class="sm:col-span-2">
                  <label class="form-label">Area, Colony, Street, Sector, Village</label>
                  <input
                    v-model="shippingAddress.address_line2"
                    type="text"
                    placeholder="Area, Colony, Street, Sector, Village"
                    class="form-input"
                  />
                </div>

                <!-- Landmark -->
                <div class="sm:col-span-2">
                  <label class="form-label">Landmark <span class="text-xs text-text-secondary">(Optional)</span></label>
                  <input
                    v-model="shippingAddress.landmark"
                    type="text"
                    placeholder="E.g. Near Apollo Hospital, Behind City Mall"
                    class="form-input"
                  />
                </div>

                <!-- City -->
                <div>
                  <label class="form-label">Town / City <span class="text-red-500">*</span></label>
                  <input
                    v-model="shippingAddress.city"
                    type="text"
                    placeholder="Town or City"
                    :class="['form-input', addressErrors.city ? 'border-red-400 focus:ring-red-300' : '']"
                  />
                  <p v-if="addressErrors.city" class="mt-1 text-xs text-red-500">{{ addressErrors.city }}</p>
                </div>

                <!-- State -->
                <div>
                  <label class="form-label">State <span class="text-red-500">*</span></label>
                  <select
                    v-model="shippingAddress.state"
                    :class="['form-input bg-white', addressErrors.state ? 'border-red-400 focus:ring-red-300' : '']"
                  >
                    <option value="">Select State</option>
                    <option v-for="s in INDIA_STATES" :key="s" :value="s">{{ s }}</option>
                  </select>
                  <p v-if="addressErrors.state" class="mt-1 text-xs text-red-500">{{ addressErrors.state }}</p>
                </div>

                <!-- Country -->
                <div>
                  <label class="form-label">Country</label>
                  <input
                    v-model="shippingAddress.country"
                    type="text"
                    class="form-input bg-gray-50 text-text-secondary cursor-not-allowed"
                    readonly
                  />
                </div>
              </div>

              <!-- Address Type -->
              <div class="mt-5">
                <label class="form-label">Address Type</label>
                <div class="flex gap-3 mt-1">
                  <button
                    type="button"
                    @click="shippingAddress.address_type = 'Home'"
                    :class="[
                      'flex items-center gap-2 px-4 py-2 border rounded-sm text-sm font-medium transition-colors',
                      shippingAddress.address_type === 'Home'
                        ? 'border-loopymart-blue bg-blue-50 text-loopymart-blue'
                        : 'border-loopymart-gray-dark text-text-secondary hover:border-loopymart-blue'
                    ]"
                  >
                    🏠 Home
                  </button>
                  <button
                    type="button"
                    @click="shippingAddress.address_type = 'Work'"
                    :class="[
                      'flex items-center gap-2 px-4 py-2 border rounded-sm text-sm font-medium transition-colors',
                      shippingAddress.address_type === 'Work'
                        ? 'border-loopymart-blue bg-blue-50 text-loopymart-blue'
                        : 'border-loopymart-gray-dark text-text-secondary hover:border-loopymart-blue'
                    ]"
                  >
                    💼 Work
                  </button>
                </div>
              </div>

              <!-- Save for next time -->
              <div v-if="!selectedSavedAddressId" class="mt-4 flex items-center gap-2">
                <input
                  id="save-addr-checkout"
                  type="checkbox"
                  v-model="saveAddressForNextTime"
                  class="w-4 h-4 text-loopymart-blue"
                />
                <label for="save-addr-checkout" class="text-sm text-text-primary cursor-pointer">
                  Save this address for next time
                </label>
              </div>

              <button
                @click="proceedToPayment"
                class="btn btn-primary mt-6"
              >
                Deliver Here
              </button>
            </div>

            <div v-else-if="shippingAddress.full_name" class="p-4">
              <p class="text-sm font-medium text-text-primary">{{ shippingAddress.full_name }}</p>
              <p class="text-xs text-text-secondary mt-0.5">{{ shippingAddress.phone }}</p>
              <p class="text-sm text-text-primary mt-1">
                {{ shippingAddress.address_line1 }}<span v-if="shippingAddress.address_line2">, {{ shippingAddress.address_line2 }}</span>
                <span v-if="shippingAddress.landmark">, Near {{ shippingAddress.landmark }}</span>
              </p>
              <p class="text-sm text-text-primary">
                {{ shippingAddress.city }}, {{ shippingAddress.state }} &ndash; {{ shippingAddress.pincode }}
              </p>
              <span class="inline-block mt-2 px-2 py-0.5 bg-loopymart-gray text-xs font-medium
                            text-text-secondary rounded-sm uppercase tracking-wide">
                {{ shippingAddress.address_type }}
              </span>
            </div>
          </div>

          <!-- Step 2: Payment Options -->
          <div class="bg-white shadow-card rounded-sm">
            <div 
              :class="[
                'flex items-center gap-3 p-4',
                currentStep === 2 ? 'bg-loopymart-blue text-white' : 'border-b border-loopymart-gray-dark'
              ]"
            >
              <span 
                :class="[
                  'w-6 h-6 flex items-center justify-center rounded-sm text-sm font-medium',
                  currentStep === 2 ? 'bg-white text-loopymart-blue' : 'bg-loopymart-gray text-text-secondary'
                ]"
              >
                2
              </span>
              <span class="font-medium">PAYMENT OPTIONS</span>
              <span 
                v-if="currentStep > 2" 
                class="ml-auto text-sm text-loopymart-blue cursor-pointer"
                @click="currentStep = 2; error = ''"
              >
                Change
              </span>
            </div>

            <div v-if="currentStep === 2" class="p-4">
              <!-- Payment Methods -->
              <div class="space-y-3 mb-6">
                <label 
                  class="flex items-center gap-3 p-4 border rounded-sm cursor-pointer transition-colors"
                  :class="paymentMethod === 'wallet' ? 'border-loopymart-blue bg-blue-50' : 'border-loopymart-gray-dark hover:border-loopymart-blue'"
                >
                  <input type="radio" v-model="paymentMethod" value="wallet" class="text-loopymart-blue" />
                  <div class="flex-1">
                    <span class="font-medium text-text-primary">LoopyMart Wallet</span>
                    <span class="ml-2 text-sm text-loopymart-green">
                      (Balance: ₹{{ walletBalance.toLocaleString('en-IN') }})
                    </span>
                  </div>
                </label>

                <label 
                  class="flex items-center gap-3 p-4 border rounded-sm cursor-pointer transition-colors"
                  :class="paymentMethod === 'card' ? 'border-loopymart-blue bg-blue-50' : 'border-loopymart-gray-dark hover:border-loopymart-blue'"
                >
                  <input type="radio" v-model="paymentMethod" value="card" class="text-loopymart-blue" />
                  <div class="flex-1">
                    <span class="font-medium text-text-primary">Credit / Debit Card</span>
                  </div>
                  <div class="flex gap-1">
                    <div class="w-8 h-5 bg-blue-600 rounded-sm"></div>
                    <div class="w-8 h-5 bg-red-500 rounded-sm"></div>
                    <div class="w-8 h-5 bg-orange-500 rounded-sm"></div>
                  </div>
                </label>

                <label 
                  class="flex items-center gap-3 p-4 border rounded-sm cursor-pointer transition-colors"
                  :class="paymentMethod === 'upi' ? 'border-loopymart-blue bg-blue-50' : 'border-loopymart-gray-dark hover:border-loopymart-blue'"
                >
                  <input type="radio" v-model="paymentMethod" value="upi" class="text-loopymart-blue" />
                  <div class="flex-1">
                    <span class="font-medium text-text-primary">UPI</span>
                    <span class="ml-2 text-xs text-text-secondary">Google Pay, PhonePe, Paytm</span>
                  </div>
                </label>

                <label 
                  class="flex items-center gap-3 p-4 border rounded-sm cursor-pointer transition-colors"
                  :class="paymentMethod === 'cod' ? 'border-loopymart-blue bg-blue-50' : 'border-loopymart-gray-dark hover:border-loopymart-blue'"
                >
                  <input type="radio" v-model="paymentMethod" value="cod" class="text-loopymart-blue" />
                  <div class="flex-1">
                    <span class="font-medium text-text-primary">Cash on Delivery</span>
                    <span class="ml-2 text-xs text-text-secondary">+₹50 COD charges</span>
                  </div>
                </label>
              </div>

              <!-- Apply Coupon -->
              <div class="border-t border-loopymart-gray-dark pt-4">
                <h3 class="font-medium text-text-primary mb-3">Apply Coupon</h3>
                
                <div v-if="selectedCoupon" class="flex items-center justify-between p-3 
                                                   bg-green-50 border border-loopymart-green rounded-sm mb-4">
                  <div>
                    <span class="font-medium text-loopymart-green">{{ selectedCoupon.code }}</span>
                    <span class="text-sm text-text-primary ml-2">
                      - ₹{{ selectedCoupon.discount }} off
                    </span>
                  </div>
                  <button @click="removeCoupon" class="text-sm text-red-500 hover:underline">
                    Remove
                  </button>
                </div>

                <button 
                  v-else
                  @click="showCoupons = !showCoupons"
                  class="w-full p-3 border border-dashed border-loopymart-blue rounded-sm 
                         text-loopymart-blue font-medium hover:bg-blue-50 transition-colors"
                >
                  {{ showCoupons ? 'Hide Coupons' : 'View Available Coupons' }}
                </button>

                <div v-if="showCoupons && !selectedCoupon" class="mt-4 space-y-3">
                  <div 
                    v-for="coupon in coupons" 
                    :key="coupon.code"
                    :class="[
                      'p-4 border-2 border-dashed rounded-sm',
                      coupon.is_used 
                        ? 'border-loopymart-gray-dark bg-gray-50 opacity-60' 
                        : 'border-loopymart-blue bg-blue-50'
                    ]"
                  >
                    <div class="flex items-start justify-between">
                      <div>
                        <span class="font-bold text-loopymart-blue">{{ coupon.code }}</span>
                        <p class="text-sm text-text-secondary mt-1">{{ coupon.description }}</p>
                        <span class="inline-block mt-2 px-2 py-1 bg-loopymart-blue text-white 
                                     text-xs font-medium rounded-sm">
                          Save ₹{{ coupon.discount }}
                        </span>
                      </div>
                      <button
                        v-if="!coupon.is_used"
                        @click="applyCoupon(coupon)"
                        class="btn btn-primary btn-sm"
                      >
                        Apply
                      </button>
                      <span v-else class="text-sm text-text-hint font-medium">Used</span>
                    </div>
                  </div>
                </div>
              </div>

              <button
                @click="proceedToReview"
                class="btn btn-primary mt-6"
              >
                Continue
              </button>
            </div>

            <div v-else-if="currentStep > 2" class="p-4">
              <p class="text-sm text-text-primary">
                {{ paymentMethod === 'wallet' ? 'LoopyMart Wallet' : 
                   paymentMethod === 'card' ? 'Credit/Debit Card' :
                   paymentMethod === 'upi' ? 'UPI' : 'Cash on Delivery' }}
              </p>
            </div>
          </div>

          <!-- Step 3: Order Summary -->
          <div class="bg-white shadow-card rounded-sm">
            <div 
              :class="[
                'flex items-center gap-3 p-4',
                currentStep === 3 ? 'bg-loopymart-blue text-white' : 'border-b border-loopymart-gray-dark'
              ]"
            >
              <span 
                :class="[
                  'w-6 h-6 flex items-center justify-center rounded-sm text-sm font-medium',
                  currentStep === 3 ? 'bg-white text-loopymart-blue' : 'bg-loopymart-gray text-text-secondary'
                ]"
              >
                3
              </span>
              <span class="font-medium">ORDER SUMMARY</span>
            </div>

            <div v-if="currentStep === 3" class="p-4">
              <!-- Order Items -->
              <div class="space-y-4 mb-6">
                <div 
                  v-for="item in items" 
                  :key="item.id"
                  class="flex gap-4"
                >
                  <img
                    :src="imageUrl(item.product_image_url)"
                    :alt="item.product_name"
                    class="w-16 h-16 object-contain border border-loopymart-gray-dark rounded-sm"
                  />
                  <div class="flex-1 min-w-0">
                    <h4 class="text-sm text-text-primary line-clamp-1">{{ item.product_name }}</h4>
                    <p class="text-xs text-text-secondary mt-1">Qty: {{ item.quantity }}</p>
                    <p class="text-sm font-medium text-text-primary mt-1">
                      ₹{{ (item.product_price * item.quantity).toLocaleString('en-IN') }}
                    </p>
                  </div>
                </div>
              </div>

              <!-- Error Message -->
              <div 
                v-if="error" 
                class="p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm mb-4"
              >
                {{ error }}
              </div>

              <!-- Place Order Button -->
              <button
                @click="placeOrder"
                :disabled="submitting"
                class="w-full py-4 bg-loopymart-orange text-white text-lg font-medium 
                       rounded-sm hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {{ submitting ? 'Processing...' : `Pay ₹${total.toLocaleString('en-IN')}` }}
              </button>

              <p class="text-xs text-text-secondary text-center mt-4">
                By placing this order, you agree to LoopyMart's Terms of Use and Privacy Policy
              </p>
            </div>
          </div>
        </div>

        <!-- Right Column - Price Summary -->
        <div class="lg:w-96 flex-shrink-0">
          <div class="bg-white shadow-card rounded-sm sticky top-32">
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h2 class="text-text-secondary font-medium uppercase text-sm">Price Details</h2>
            </div>

            <div class="p-4 space-y-3">
              <div class="flex justify-between text-sm">
                <span class="text-text-primary">
                  Price ({{ totalItems }} {{ totalItems === 1 ? 'item' : 'items' }})
                </span>
                <span class="text-text-primary">₹{{ subtotal.toLocaleString('en-IN') }}</span>
              </div>

              <div class="flex justify-between text-sm">
                <span class="text-text-primary">Discount</span>
                <span class="text-loopymart-green">− ₹{{ discount.toLocaleString('en-IN') }}</span>
              </div>

              <div v-if="selectedCoupon" class="flex justify-between text-sm">
                <span class="text-text-primary">Coupon ({{ selectedCoupon.code }})</span>
                <span class="text-loopymart-green">− ₹{{ couponDiscount.toLocaleString('en-IN') }}</span>
              </div>

              <div class="flex justify-between text-sm">
                <span class="text-text-primary">Delivery Charges</span>
                <span v-if="deliveryCharges === 0" class="text-loopymart-green">FREE</span>
                <span v-else class="text-text-primary">₹{{ deliveryCharges }}</span>
              </div>

              <div class="pt-3 border-t border-dashed border-loopymart-gray-dark">
                <div class="flex justify-between">
                  <span class="font-medium text-text-primary">Total Amount</span>
                  <span class="font-medium text-text-primary">₹{{ total.toLocaleString('en-IN') }}</span>
                </div>
              </div>

              <div class="pt-3">
                <p class="text-sm text-loopymart-green font-medium">
                  You will save ₹{{ discount.toLocaleString('en-IN') }} on this order
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
