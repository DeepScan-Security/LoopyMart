<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import client from '@/api/client'
import { addresses as addressesApi } from '@/api'

const user = ref(null)
const loading = ref(true)
const error = ref('')
const success = ref('')

// Profile data
const profile = ref({
  full_name: '',
  phone: '',
  address: '',
})

// Profile picture
const profilePicture = ref(null)
const profilePicturePreview = ref(null)
// Blob URL created by fetching the protected endpoint via axios (carries the JWT)
const profilePictureBlobUrl = ref(null)

// Active tab
const activeTab = ref('profile')

onMounted(async () => {
  try {
    const [userRes] = await Promise.all([
      client.get('/auth/me'),
      loadAddresses(),
    ])
    user.value = userRes.data
    profile.value = {
      full_name: user.value.full_name || '',
      phone: user.value.phone || '',
      address: user.value.address || '',
    }
    // Fetch profile picture through the authenticated endpoint so the JWT is
    // included in the request (plain <img src> would fail with 401).
    if (user.value.profile_picture_url) {
      await loadProfilePictureBlobUrl()
    }
  } catch (e) {
    error.value = 'Failed to load profile'
  } finally {
    loading.value = false
  }
})

/**
 * Fetch the profile picture via the authenticated download endpoint and store
 * the result as a local blob URL so the <img> tag can display it without
 * making a separate unauthenticated browser request.
 *
 * The endpoint path — GET /auth/profile-picture?filename=<name> — is the
 * CTF path-traversal sink.  Fetching through axios ensures the JWT is sent.
 */
async function loadProfilePictureBlobUrl() {
  if (!user.value?.profile_picture_url) return
  const filename = user.value.profile_picture_url.split('/').pop()
  try {
    const res = await client.get('/auth/profile-picture', {
      params: { filename },
      responseType: 'blob',
    })
    // Revoke the previous object URL to avoid memory leaks
    if (profilePictureBlobUrl.value) URL.revokeObjectURL(profilePictureBlobUrl.value)
    profilePictureBlobUrl.value = URL.createObjectURL(res.data)
  } catch {
    profilePictureBlobUrl.value = null
  }
}

function handleProfilePictureChange(e) {
  const file = e.target.files[0]
  if (file) {
    profilePicture.value = file
    profilePicturePreview.value = URL.createObjectURL(file)
  }
}

async function updateProfile() {
  error.value = ''
  success.value = ''
  try {
    const res = await client.put('/auth/profile', profile.value)
    user.value = res.data
    success.value = 'Profile updated successfully!'
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to update profile'
  }
}

async function uploadProfilePicture() {
  if (!profilePicture.value) {
    error.value = 'Please select a picture'
    return
  }
  
  error.value = ''
  success.value = ''
  const formData = new FormData()
  formData.append('file', profilePicture.value)
  
  try {
    const res = await client.post('/auth/profile-picture', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    user.value = res.data
    success.value = 'Profile picture updated!'
    profilePicture.value = null
    profilePicturePreview.value = null
    // Reload the blob URL so the sidebar avatar refreshes immediately
    await loadProfilePictureBlobUrl()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to upload picture'
  }
}

async function upgradeToBlack() {
  error.value = ''
  success.value = ''
  try {
    const res = await client.post('/auth/upgrade-black')
    user.value = res.data
    success.value = 'Welcome to LoopyMart Black!'
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to upgrade'
  }
}

// ── Saved Addresses ──────────────────────────────────────────────────────────
const INDIA_STATES = [
  'Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar',
  'Chandigarh', 'Chhattisgarh', 'Dadra and Nagar Haveli and Daman and Diu', 'Delhi',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jammu and Kashmir', 'Jharkhand',
  'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep', 'Madhya Pradesh', 'Maharashtra',
  'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry', 'Punjab',
  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh',
  'Uttarakhand', 'West Bengal',
]

const addressList = ref([])
const showAddressForm = ref(false)
const editingAddressId = ref(null)
const addressForm = ref({
  full_name: '', phone: '', pincode: '', address_line1: '', address_line2: '',
  landmark: '', city: '', state: '', country: 'India', address_type: 'Home', is_default: false,
})
const addressFormErrors = ref({})
const addressSubmitting = ref(false)
const addressError = ref('')
const addressSuccess = ref('')

async function loadAddresses() {
  try {
    const res = await addressesApi.list()
    addressList.value = res.data
  } catch (_) {
    addressList.value = []
  }
}

function openAddressForm(addr = null) {
  addressFormErrors.value = {}
  addressError.value = ''
  if (addr) {
    editingAddressId.value = addr.id
    addressForm.value = {
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
      is_default: addr.is_default || false,
    }
  } else {
    editingAddressId.value = null
    addressForm.value = {
      full_name: '', phone: '', pincode: '', address_line1: '', address_line2: '',
      landmark: '', city: '', state: '', country: 'India', address_type: 'Home', is_default: false,
    }
  }
  showAddressForm.value = true
}

function closeAddressForm() {
  showAddressForm.value = false
  editingAddressId.value = null
  addressFormErrors.value = {}
}

function validateAddressForm() {
  const errs = {}
  const f = addressForm.value
  if (!f.full_name.trim()) errs.full_name = 'Full name is required'
  if (!/^\d{10}$/.test(f.phone.trim())) errs.phone = 'Enter a valid 10-digit phone number'
  if (!/^\d{6}$/.test(f.pincode.trim())) errs.pincode = 'Enter a valid 6-digit PIN code'
  if (!f.address_line1.trim()) errs.address_line1 = 'Address line 1 is required'
  if (!f.city.trim()) errs.city = 'City is required'
  if (!f.state.trim()) errs.state = 'State is required'
  addressFormErrors.value = errs
  return Object.keys(errs).length === 0
}

async function submitAddressForm() {
  if (!validateAddressForm()) return
  addressSubmitting.value = true
  addressError.value = ''
  addressSuccess.value = ''
  try {
    if (editingAddressId.value) {
      const res = await addressesApi.update(editingAddressId.value, addressForm.value)
      const idx = addressList.value.findIndex(a => a.id === editingAddressId.value)
      if (idx !== -1) addressList.value[idx] = res.data
      // Refresh to get correct is_default propagation
      await loadAddresses()
      addressSuccess.value = 'Address updated successfully!'
    } else {
      await addressesApi.create(addressForm.value)
      await loadAddresses()
      addressSuccess.value = 'Address added successfully!'
    }
    closeAddressForm()
  } catch (e) {
    addressError.value = e.response?.data?.detail || 'Failed to save address'
  } finally {
    addressSubmitting.value = false
  }
}

async function confirmDeleteAddress(id) {
  if (!confirm('Delete this address?')) return
  addressError.value = ''
  addressSuccess.value = ''
  try {
    await addressesApi.delete(id)
    addressList.value = addressList.value.filter(a => a.id !== id)
    // Re-fetch so default flag is consistent if the deleted one was default
    await loadAddresses()
    addressSuccess.value = 'Address deleted.'
  } catch (e) {
    addressError.value = e.response?.data?.detail || 'Failed to delete address'
  }
}

async function setAddressDefault(id) {
  addressError.value = ''
  addressSuccess.value = ''
  try {
    await addressesApi.setDefault(id)
    await loadAddresses()
    addressSuccess.value = 'Default address updated.'
  } catch (e) {
    addressError.value = e.response?.data?.detail || 'Failed to update default'
  }
}

const tabs = [
  { id: 'profile', label: 'My Profile', icon: 'user' },
  { id: 'picture', label: 'Profile Picture', icon: 'camera' },
  { id: 'addresses', label: 'My Addresses', icon: 'location' },
  { id: 'orders', label: 'My Orders', icon: 'package' },
  { id: 'membership', label: 'LoopyMart Plus', icon: 'crown' },
]
</script>

<template>
  <div class="min-h-screen bg-loopymart-gray py-4">
    <div class="max-w-container mx-auto px-4">
      <!-- Loading -->
      <div v-if="loading" class="bg-white shadow-card rounded-sm p-12 text-center">
        <div class="inline-block w-8 h-8 border-4 border-loopymart-blue border-t-transparent 
                    rounded-full animate-spin"></div>
        <p class="mt-4 text-text-secondary">Loading profile...</p>
      </div>

      <div v-else class="flex flex-col lg:flex-row gap-4">
        <!-- Left Sidebar -->
        <aside class="lg:w-72 flex-shrink-0">
          <!-- User Info Card -->
          <div class="bg-white shadow-card rounded-sm p-4 mb-4">
            <div class="flex items-center gap-4">
              <div class="w-14 h-14 flex-shrink-0">
                <img 
                  v-if="user.profile_picture_url" 
                  :src="profilePictureBlobUrl" 
                  alt="Profile"
                  class="w-full h-full rounded-full object-cover"
                />
                <div 
                  v-else 
                  class="w-full h-full bg-loopymart-blue text-white rounded-full 
                         flex items-center justify-center text-2xl font-bold"
                >
                  {{ user.full_name.charAt(0).toUpperCase() }}
                </div>
              </div>
              <div>
                <p class="text-xs text-text-secondary">Hello,</p>
                <p class="font-medium text-text-primary">{{ user.full_name }}</p>
              </div>
            </div>
          </div>

          <!-- Navigation -->
          <nav class="bg-white shadow-card rounded-sm overflow-hidden">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
                activeTab === tab.id 
                  ? 'bg-loopymart-gray border-l-4 border-loopymart-blue text-loopymart-blue' 
                  : 'text-text-primary hover:bg-loopymart-gray border-l-4 border-transparent'
              ]"
            >
              <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="tab.icon === 'user'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                <path v-if="tab.icon === 'camera'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
                <path v-if="tab.icon === 'camera'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
                <path v-if="tab.icon === 'package'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                <path v-if="tab.icon === 'crown'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M5 3l3.5 5.5L12 5l3.5 3.5L19 3v13a2 2 0 01-2 2H7a2 2 0 01-2-2V3z"/>
                <path v-if="tab.icon === 'location'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                <path v-if="tab.icon === 'location'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              <span class="text-sm font-medium">{{ tab.label }}</span>
            </button>
          </nav>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 min-w-0">
          <!-- Messages -->
          <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm">
            {{ error }}
          </div>
          <div v-if="success" class="mb-4 p-3 bg-green-50 border border-loopymart-green rounded-sm text-loopymart-green text-sm">
            {{ success }}
          </div>

          <!-- Profile Tab -->
          <div v-if="activeTab === 'profile'" class="bg-white shadow-card rounded-sm">
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h2 class="font-medium text-text-primary">Personal Information</h2>
            </div>
            <form @submit.prevent="updateProfile" class="p-6 space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="form-label">Full Name</label>
                  <input v-model="profile.full_name" type="text" required class="form-input" />
                </div>
                <div>
                  <label class="form-label">Email Address</label>
                  <input :value="user.email" type="email" disabled 
                         class="form-input bg-loopymart-gray cursor-not-allowed" />
                </div>
                <div>
                  <label class="form-label">Mobile Number</label>
                  <input v-model="profile.phone" type="tel" class="form-input" 
                         placeholder="Enter mobile number" />
                </div>
              </div>
              <div>
                <label class="form-label">Address</label>
                <textarea v-model="profile.address" rows="3" class="form-input resize-none"
                          placeholder="Enter your address"></textarea>
              </div>
              <div class="flex items-center gap-4">
                <button type="submit" class="btn btn-primary">Save Changes</button>
                <div class="flex items-center gap-2 text-sm">
                  <span class="text-text-secondary">Wallet Balance:</span>
                  <span class="font-medium text-loopymart-blue">
                    ₹{{ user.wallet_balance.toLocaleString('en-IN') }}
                  </span>
                </div>
              </div>
            </form>
          </div>

          <!-- Picture Tab -->
          <div v-if="activeTab === 'picture'" class="bg-white shadow-card rounded-sm">
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h2 class="font-medium text-text-primary">Profile Picture</h2>
            </div>
            <div class="p-6">
              <div class="flex items-center gap-6 mb-6">
                <div class="w-24 h-24 flex-shrink-0">
                  <img 
                    v-if="profilePicturePreview || user.profile_picture_url" 
                    :src="profilePicturePreview || profilePictureBlobUrl" 
                    alt="Profile"
                    class="w-full h-full rounded-full object-cover border-4 border-loopymart-gray"
                  />
                  <div 
                    v-else 
                    class="w-full h-full bg-loopymart-blue text-white rounded-full 
                           flex items-center justify-center text-3xl font-bold"
                  >
                    {{ user.full_name.charAt(0).toUpperCase() }}
                  </div>
                </div>
                <div>
                  <input type="file" accept="image/*" @change="handleProfilePictureChange"
                         id="picture-upload" class="hidden" />
                  <label for="picture-upload" class="btn cursor-pointer">
                    Choose Picture
                  </label>
                  <p class="text-xs text-text-secondary mt-2">
                    Recommended: Square image, at least 200x200px
                  </p>
                </div>
              </div>
              <button v-if="profilePicture" @click="uploadProfilePicture" class="btn btn-primary">
                Upload Picture
              </button>
            </div>
          </div>

          <!-- Addresses Tab -->
          <div v-if="activeTab === 'addresses'" class="space-y-4">
            <!-- Address-level messages -->
            <div v-if="addressError" class="p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm">
              {{ addressError }}
            </div>
            <div v-if="addressSuccess" class="p-3 bg-green-50 border border-loopymart-green rounded-sm text-loopymart-green text-sm">
              {{ addressSuccess }}
            </div>

            <!-- Address cards -->
            <div
              v-for="addr in addressList"
              :key="addr.id"
              :class="[
                'bg-white shadow-card rounded-sm p-4 border-l-4',
                addr.is_default ? 'border-loopymart-blue' : 'border-transparent'
              ]"
            >
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="font-medium text-text-primary">{{ addr.full_name }}</span>
                    <span class="text-xs px-2 py-0.5 bg-loopymart-gray rounded text-text-secondary">
                      {{ addr.address_type }}
                    </span>
                    <span v-if="addr.is_default"
                          class="text-xs px-2 py-0.5 bg-loopymart-blue text-white rounded">
                      Default
                    </span>
                  </div>
                  <p class="text-sm text-text-secondary">
                    {{ addr.address_line1 }}<span v-if="addr.address_line2">, {{ addr.address_line2 }}</span>
                  </p>
                  <p v-if="addr.landmark" class="text-sm text-text-secondary">Near {{ addr.landmark }}</p>
                  <p class="text-sm text-text-secondary">
                    {{ addr.city }}, {{ addr.state }} &ndash; {{ addr.pincode }}
                  </p>
                  <p class="text-sm text-text-secondary mt-1">Phone: {{ addr.phone }}</p>
                </div>
                <div class="flex flex-col gap-2 flex-shrink-0">
                  <button
                    v-if="!addr.is_default"
                    @click="setAddressDefault(addr.id)"
                    class="text-xs text-loopymart-blue hover:underline text-right"
                  >
                    Set Default
                  </button>
                  <button
                    @click="openAddressForm(addr)"
                    class="text-xs text-loopymart-blue hover:underline text-right"
                  >
                    Edit
                  </button>
                  <button
                    @click="confirmDeleteAddress(addr.id)"
                    class="text-xs text-red-500 hover:underline text-right"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div v-if="!addressList.length && !showAddressForm"
                 class="bg-white shadow-card rounded-sm p-8 text-center">
              <p class="text-text-secondary mb-4">No saved addresses yet.</p>
            </div>

            <!-- Add / Edit form -->
            <div v-if="showAddressForm" class="bg-white shadow-card rounded-sm">
              <div class="p-4 border-b border-loopymart-gray-dark flex items-center justify-between">
                <h3 class="font-medium text-text-primary">
                  {{ editingAddressId ? 'Edit Address' : 'Add New Address' }}
                </h3>
                <button @click="closeAddressForm"
                        class="text-text-secondary hover:text-text-primary">&times;</button>
              </div>
              <div v-if="addressError" class="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm">
                {{ addressError }}
              </div>
              <form @submit.prevent="submitAddressForm" class="p-4 space-y-4">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label class="form-label">Full Name <span class="text-red-500">*</span></label>
                    <input v-model="addressForm.full_name" type="text" placeholder="First and last name"
                           :class="['form-input', addressFormErrors.full_name ? 'border-red-400' : '']" />
                    <p v-if="addressFormErrors.full_name" class="mt-1 text-xs text-red-500">{{ addressFormErrors.full_name }}</p>
                  </div>
                  <div>
                    <label class="form-label">Mobile Number <span class="text-red-500">*</span></label>
                    <input v-model="addressForm.phone" type="tel" placeholder="10-digit number"
                           :class="['form-input', addressFormErrors.phone ? 'border-red-400' : '']" />
                    <p v-if="addressFormErrors.phone" class="mt-1 text-xs text-red-500">{{ addressFormErrors.phone }}</p>
                  </div>
                  <div>
                    <label class="form-label">PIN Code <span class="text-red-500">*</span></label>
                    <input v-model="addressForm.pincode" type="text" maxlength="6" placeholder="6-digit PIN code"
                           :class="['form-input', addressFormErrors.pincode ? 'border-red-400' : '']" />
                    <p v-if="addressFormErrors.pincode" class="mt-1 text-xs text-red-500">{{ addressFormErrors.pincode }}</p>
                  </div>
                  <div>
                    <label class="form-label">Address Type</label>
                    <select v-model="addressForm.address_type" class="form-input">
                      <option>Home</option>
                      <option>Work</option>
                      <option>Other</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label class="form-label">Address Line 1 <span class="text-red-500">*</span></label>
                  <input v-model="addressForm.address_line1" type="text" placeholder="House No., Building, Street"
                         :class="['form-input', addressFormErrors.address_line1 ? 'border-red-400' : '']" />
                  <p v-if="addressFormErrors.address_line1" class="mt-1 text-xs text-red-500">{{ addressFormErrors.address_line1 }}</p>
                </div>
                <div>
                  <label class="form-label">Address Line 2</label>
                  <input v-model="addressForm.address_line2" type="text" placeholder="Area, Colony (optional)" class="form-input" />
                </div>
                <div>
                  <label class="form-label">Landmark</label>
                  <input v-model="addressForm.landmark" type="text" placeholder="Nearby landmark (optional)" class="form-input" />
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label class="form-label">City / Town <span class="text-red-500">*</span></label>
                    <input v-model="addressForm.city" type="text" placeholder="City"
                           :class="['form-input', addressFormErrors.city ? 'border-red-400' : '']" />
                    <p v-if="addressFormErrors.city" class="mt-1 text-xs text-red-500">{{ addressFormErrors.city }}</p>
                  </div>
                  <div>
                    <label class="form-label">State <span class="text-red-500">*</span></label>
                    <select v-model="addressForm.state"
                            :class="['form-input', addressFormErrors.state ? 'border-red-400' : '']">
                      <option value="">Select State</option>
                      <option v-for="s in INDIA_STATES" :key="s" :value="s">{{ s }}</option>
                    </select>
                    <p v-if="addressFormErrors.state" class="mt-1 text-xs text-red-500">{{ addressFormErrors.state }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <input id="addr-default" type="checkbox" v-model="addressForm.is_default"
                         class="w-4 h-4 text-loopymart-blue" />
                  <label for="addr-default" class="text-sm text-text-primary cursor-pointer">
                    Set as default address
                  </label>
                </div>
                <div class="flex items-center gap-3">
                  <button type="submit" :disabled="addressSubmitting"
                          class="btn btn-primary">
                    {{ addressSubmitting ? 'Saving...' : (editingAddressId ? 'Update Address' : 'Save Address') }}
                  </button>
                  <button type="button" @click="closeAddressForm" class="btn">
                    Cancel
                  </button>
                </div>
              </form>
            </div>

            <!-- Add new button -->
            <div v-if="!showAddressForm" class="flex justify-end">
              <button @click="openAddressForm()" class="btn btn-primary">
                + Add New Address
              </button>
            </div>
          </div>

          <!-- Orders Tab -->
          <div v-if="activeTab === 'orders'" class="bg-white shadow-card rounded-sm">
            <div class="p-4 border-b border-loopymart-gray-dark flex items-center justify-between">
              <h2 class="font-medium text-text-primary">My Orders</h2>
              <RouterLink to="/orders" class="text-loopymart-blue text-sm hover:underline">
                View All Orders
              </RouterLink>
            </div>
            <div class="p-6 text-center">
              <RouterLink to="/orders" class="btn btn-primary">
                Go to Order History
              </RouterLink>
            </div>
          </div>

          <!-- Membership Tab -->
          <div v-if="activeTab === 'membership'" class="bg-white shadow-card rounded-sm">
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h2 class="font-medium text-text-primary">LoopyMart Plus Membership</h2>
            </div>
            <div class="p-6">
              <div v-if="!user.is_black_member">
                <div class="max-w-lg">
                  <h3 class="text-xl font-medium text-text-primary mb-4">
                    Upgrade to LoopyMart Plus
                  </h3>
                  <ul class="space-y-3 mb-6">
                    <li class="flex items-center gap-3">
                      <span class="w-8 h-8 bg-loopymart-blue/10 rounded-full flex items-center 
                                   justify-center text-loopymart-blue">
                        <svg width="20" height="20" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M5 3l3.5 5.5L12 5l3.5 3.5L19 3v13a2 2 0 01-2 2H7a2 2 0 01-2-2V3z"/>
                        </svg>
                      </span>
                      <span class="text-text-primary">Exclusive member badge</span>
                    </li>
                    <li class="flex items-center gap-3">
                      <span class="w-8 h-8 bg-loopymart-blue/10 rounded-full flex items-center 
                                   justify-center text-loopymart-blue">
                        <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
                        </svg>
                      </span>
                      <span class="text-text-primary">Free express delivery on all orders</span>
                    </li>
                    <li class="flex items-center gap-3">
                      <span class="w-8 h-8 bg-loopymart-blue/10 rounded-full flex items-center 
                                   justify-center text-loopymart-blue">
                        <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"/>
                        </svg>
                      </span>
                      <span class="text-text-primary">Early access to sales and offers</span>
                    </li>
                    <li class="flex items-center gap-3">
                      <span class="w-8 h-8 bg-loopymart-blue/10 rounded-full flex items-center 
                                   justify-center text-loopymart-blue">
                        <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                      </span>
                      <span class="text-text-primary">Special member-only discounts</span>
                    </li>
                  </ul>
                  <button @click="upgradeToBlack" class="btn btn-primary btn-lg">
                    Upgrade Now
                  </button>
                </div>
              </div>

              <div v-else class="text-center py-8">
                <div class="w-20 h-20 bg-gradient-to-r from-amber-400 to-yellow-500 rounded-full 
                            flex items-center justify-center mx-auto mb-4">
                  <svg width="40" height="40" class="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M5 3l3.5 5.5L12 5l3.5 3.5L19 3v13a2 2 0 01-2 2H7a2 2 0 01-2-2V3z"/>
                  </svg>
                </div>
                <h3 class="text-2xl font-bold text-text-primary mb-2">
                  You're a LoopyMart Plus Member!
                </h3>
                <p class="text-text-secondary">
                  Member since: {{ new Date(user.black_member_since).toLocaleDateString('en-IN', {
                    year: 'numeric', month: 'long', day: 'numeric'
                  }) }}
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>
