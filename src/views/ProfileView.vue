<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import client from '@/api/client'

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

// KYC data
const kyc = ref(null)
const kycForm = ref({
  document_type: 'AADHAR',
  document_number: '',
})
const kycDocument = ref(null)

// Active tab
const activeTab = ref('profile')

onMounted(async () => {
  try {
    const [userRes, kycRes] = await Promise.all([
      client.get('/auth/me'),
      client.get('/kyc/me').catch(() => ({ data: null })),
    ])
    user.value = userRes.data
    profile.value = {
      full_name: user.value.full_name || '',
      phone: user.value.phone || '',
      address: user.value.address || '',
    }
    kyc.value = kycRes.data
  } catch (e) {
    error.value = 'Failed to load profile'
  } finally {
    loading.value = false
  }
})

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
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to upload picture'
  }
}

async function createKYC() {
  error.value = ''
  success.value = ''
  try {
    const res = await client.post('/kyc', kycForm.value)
    kyc.value = res.data
    success.value = 'KYC record created! Now upload your document.'
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to create KYC'
  }
}

function handleKYCDocumentChange(e) {
  kycDocument.value = e.target.files[0]
}

async function uploadKYCDocument() {
  if (!kycDocument.value) {
    error.value = 'Please select a document'
    return
  }
  
  error.value = ''
  success.value = ''
  const formData = new FormData()
  formData.append('file', kycDocument.value)
  
  try {
    const res = await client.post('/kyc/upload-document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    kyc.value = res.data
    success.value = 'KYC document uploaded successfully!'
    kycDocument.value = null
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to upload document'
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

const tabs = [
  { id: 'profile', label: 'My Profile', icon: 'user' },
  { id: 'picture', label: 'Profile Picture', icon: 'camera' },
  { id: 'orders', label: 'My Orders', icon: 'package' },
  { id: 'kyc', label: 'KYC Verification', icon: 'shield' },
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
                  :src="user.profile_picture_url" 
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
                <path v-if="tab.icon === 'shield'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                <path v-if="tab.icon === 'crown'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M5 3l3.5 5.5L12 5l3.5 3.5L19 3v13a2 2 0 01-2 2H7a2 2 0 01-2-2V3z"/>
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
                    :src="profilePicturePreview || user.profile_picture_url" 
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

          <!-- KYC Tab -->
          <div v-if="activeTab === 'kyc'" class="bg-white shadow-card rounded-sm">
            <div class="p-4 border-b border-loopymart-gray-dark">
              <h2 class="font-medium text-text-primary">KYC Verification</h2>
            </div>
            <div class="p-6">
              <div v-if="!kyc">
                <form @submit.prevent="createKYC" class="space-y-4 max-w-md">
                  <div>
                    <label class="form-label">Document Type</label>
                    <select v-model="kycForm.document_type" class="form-input">
                      <option value="AADHAR">Aadhar Card</option>
                      <option value="PAN">PAN Card</option>
                    </select>
                  </div>
                  <div>
                    <label class="form-label">Document Number</label>
                    <input v-model="kycForm.document_number" type="text" required class="form-input"
                           placeholder="Enter document number" />
                  </div>
                  <button type="submit" class="btn btn-primary">Submit KYC</button>
                </form>
              </div>

              <div v-else class="space-y-6">
                <div class="flex items-center gap-4 p-4 bg-loopymart-gray rounded-sm">
                  <div class="flex-1">
                    <p class="text-sm text-text-secondary">Document Type</p>
                    <p class="font-medium">{{ kyc.document_type }}</p>
                  </div>
                  <div class="flex-1">
                    <p class="text-sm text-text-secondary">Document Number</p>
                    <p class="font-medium">{{ kyc.document_number }}</p>
                  </div>
                  <div>
                    <span :class="[
                      'px-3 py-1 rounded-full text-sm font-medium',
                      kyc.status === 'VERIFIED' ? 'bg-loopymart-green text-white' :
                      kyc.status === 'PENDING' ? 'bg-loopymart-orange text-white' :
                      'bg-red-500 text-white'
                    ]">
                      {{ kyc.status }}
                    </span>
                  </div>
                </div>

                <div v-if="!kyc.document_image_url">
                  <h3 class="font-medium text-text-primary mb-3">Upload Document</h3>
                  <input type="file" accept="image/*,application/pdf" @change="handleKYCDocumentChange"
                         id="kyc-upload" class="hidden" />
                  <label for="kyc-upload" class="btn cursor-pointer inline-flex items-center gap-2">
                    <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                    </svg>
                    Choose Document
                  </label>
                  <button v-if="kycDocument" @click="uploadKYCDocument" class="btn btn-primary ml-3">
                    Upload
                  </button>
                </div>
                <div v-else class="p-4 bg-green-50 border border-loopymart-green rounded-sm">
                  <p class="text-loopymart-green font-medium flex items-center gap-2">
                    <svg width="20" height="20" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                    </svg>
                    Document uploaded and under review
                  </p>
                </div>
              </div>
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
