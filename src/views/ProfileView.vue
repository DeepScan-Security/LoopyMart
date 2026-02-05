<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import client from '@/api/client'

const router = useRouter()
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
    success.value = 'Welcome to Flipkart Black! 🎉'
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to upgrade'
  }
}
</script>

<template>
  <div class="profile-page">
    <h1>My Profile</h1>
    
    <div v-if="loading" class="loading">Loading...</div>
    
    <div v-else class="profile-container">
      <!-- Profile Header -->
      <div class="profile-header card">
        <div class="profile-avatar">
          <img 
            v-if="user.profile_picture_url" 
            :src="user.profile_picture_url" 
            alt="Profile" 
          />
          <div v-else class="avatar-placeholder">
            {{ user.full_name.charAt(0).toUpperCase() }}
          </div>
        </div>
        <div class="profile-info">
          <h2>{{ user.full_name }}</h2>
          <p>{{ user.email }}</p>
          <div class="badges">
            <span v-if="user.is_black_member" class="badge badge-black">
              👑 Flipkart Black
            </span>
            <span v-if="kyc && kyc.status === 'VERIFIED'" class="badge badge-verified">
              ✓ KYC Verified
            </span>
          </div>
          <div class="wallet-balance">
            Wallet: ₹{{ user.wallet_balance.toLocaleString('en-IN') }}
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button 
          @click="activeTab = 'profile'" 
          :class="{ active: activeTab === 'profile' }">
          Profile
        </button>
        <button 
          @click="activeTab = 'picture'" 
          :class="{ active: activeTab === 'picture' }">
          Picture
        </button>
        <button 
          @click="activeTab = 'kyc'" 
          :class="{ active: activeTab === 'kyc' }">
          KYC
        </button>
        <button 
          @click="activeTab = 'membership'" 
          :class="{ active: activeTab === 'membership' }">
          Membership
        </button>
      </div>

      <!-- Messages -->
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="success" class="success">{{ success }}</div>

      <!-- Profile Tab -->
      <div v-if="activeTab === 'profile'" class="tab-content card">
        <h3>Update Profile</h3>
        <form @submit.prevent="updateProfile" class="form">
          <div class="form-group">
            <label>Full Name</label>
            <input v-model="profile.full_name" type="text" required />
          </div>
          <div class="form-group">
            <label>Phone</label>
            <input v-model="profile.phone" type="tel" />
          </div>
          <div class="form-group">
            <label>Address</label>
            <textarea v-model="profile.address" rows="3"></textarea>
          </div>
          <button type="submit" class="btn btn-primary">Update Profile</button>
        </form>
      </div>

      <!-- Picture Tab -->
      <div v-if="activeTab === 'picture'" class="tab-content card">
        <h3>Profile Picture</h3>
        <div class="picture-upload">
          <input 
            type="file" 
            accept="image/*" 
            @change="handleProfilePictureChange"
            id="picture-upload"
          />
          <label for="picture-upload" class="btn btn-secondary">Choose Picture</label>
          <img 
            v-if="profilePicturePreview" 
            :src="profilePicturePreview" 
            class="picture-preview" 
            alt="Preview"
          />
          <button 
            v-if="profilePicture" 
            @click="uploadProfilePicture" 
            class="btn btn-primary">
            Upload Picture
          </button>
        </div>
      </div>

      <!-- KYC Tab -->
      <div v-if="activeTab === 'kyc'" class="tab-content card">
        <h3>KYC Verification</h3>
        
        <div v-if="!kyc">
          <form @submit.prevent="createKYC" class="form">
            <div class="form-group">
              <label>Document Type</label>
              <select v-model="kycForm.document_type">
                <option value="AADHAR">Aadhar Card</option>
                <option value="PAN">PAN Card</option>
              </select>
            </div>
            <div class="form-group">
              <label>Document Number</label>
              <input v-model="kycForm.document_number" type="text" required />
            </div>
            <button type="submit" class="btn btn-primary">Submit KYC</button>
          </form>
        </div>
        
        <div v-else class="kyc-status">
          <div class="kyc-info">
            <p><strong>Document Type:</strong> {{ kyc.document_type }}</p>
            <p><strong>Document Number:</strong> {{ kyc.document_number }}</p>
            <p><strong>Status:</strong> 
              <span :class="'status-' + kyc.status.toLowerCase()">
                {{ kyc.status }}
              </span>
            </p>
          </div>
          
          <div v-if="!kyc.document_image_url" class="document-upload">
            <h4>Upload Document</h4>
            <input 
              type="file" 
              accept="image/*,application/pdf" 
              @change="handleKYCDocumentChange"
              id="kyc-upload"
            />
            <label for="kyc-upload" class="btn btn-secondary">Choose Document</label>
            <button 
              v-if="kycDocument" 
              @click="uploadKYCDocument" 
              class="btn btn-primary">
              Upload Document
            </button>
          </div>
          
          <div v-else class="document-uploaded">
            <p>✓ Document uploaded and under review</p>
          </div>
        </div>
      </div>

      <!-- Membership Tab -->
      <div v-if="activeTab === 'membership'" class="tab-content card">
        <h3>Flipkart Black Membership</h3>
        
        <div v-if="!user.is_black_member" class="membership-offer">
          <div class="membership-benefits">
            <h4>Benefits of Flipkart Black:</h4>
            <ul>
              <li>👑 Exclusive badge on your profile</li>
              <li>🚚 Free express delivery on all orders</li>
              <li>🎁 Early access to sales and offers</li>
              <li>💎 Special discounts for members</li>
            </ul>
          </div>
          <button @click="upgradeToBlack" class="btn btn-primary btn-upgrade">
            Upgrade to Flipkart Black
          </button>
        </div>
        
        <div v-else class="membership-active">
          <p class="membership-message">
            🎉 You are a Flipkart Black member!
          </p>
          <p>Member since: {{ new Date(user.black_member_since).toLocaleDateString() }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page h1 {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
}

.loading {
  padding: 2rem;
  text-align: center;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.profile-avatar img,
.avatar-placeholder {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2874f0;
  color: white;
  font-size: 2.5rem;
  font-weight: 700;
}

.profile-info h2 {
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
}

.profile-info p {
  margin: 0 0 0.75rem;
  color: #666;
}

.badges {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.badge-black {
  background: #000;
  color: #ffd700;
}

.badge-verified {
  background: #10b981;
  color: white;
}

.wallet-balance {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2874f0;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #e5e7eb;
}

.tabs button {
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  font-weight: 600;
  color: #666;
  transition: all 0.2s;
}

.tabs button.active {
  color: #2874f0;
  border-bottom-color: #2874f0;
}

.tab-content {
  padding: 1.5rem;
}

.tab-content h3 {
  margin: 0 0 1.5rem;
  font-size: 1.2rem;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
}

.picture-upload {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: flex-start;
}

.picture-upload input[type="file"] {
  display: none;
}

.picture-preview {
  max-width: 200px;
  border-radius: 8px;
}

.kyc-status {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.kyc-info p {
  margin: 0.5rem 0;
}

.status-pending {
  color: #f59e0b;
  font-weight: 600;
}

.status-verified {
  color: #10b981;
  font-weight: 600;
}

.status-rejected {
  color: #ef4444;
  font-weight: 600;
}

.document-upload {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: flex-start;
}

.document-upload input[type="file"] {
  display: none;
}

.document-uploaded {
  padding: 1rem;
  background: #d1fae5;
  border-radius: 6px;
  color: #065f46;
  font-weight: 600;
}

.membership-offer {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.membership-benefits ul {
  list-style: none;
  padding: 0;
}

.membership-benefits li {
  padding: 0.5rem 0;
  font-size: 1rem;
}

.btn-upgrade {
  align-self: flex-start;
  font-size: 1rem;
  padding: 0.75rem 2rem;
}

.membership-active {
  text-align: center;
  padding: 2rem;
}

.membership-message {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.error {
  padding: 0.75rem;
  background: #fee;
  color: #e53e3e;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.success {
  padding: 0.75rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 4px;
  margin-bottom: 1rem;
}
</style>
