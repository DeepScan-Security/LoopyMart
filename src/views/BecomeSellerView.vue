<script setup>
import { ref, onMounted } from 'vue'
import client from '@/api/client'

const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const success = ref('')

const sellerApp = ref(null)
const kycRecord = ref(null)

// Application form
const form = ref({
  store_name: '',
  store_description: '',
  phone: '',
  email: '',
  address: '',
  business_type: 'Individual',
  gst_number: '',
  pan_number: '',
  bank_account_number: '',
  bank_ifsc: '',
  bank_account_name: '',
})

// KYC form
const kycForm = ref({ document_type: 'AADHAR', document_number: '' })
const kycDocument = ref(null)
const kycSubmitting = ref(false)
const kycError = ref('')
const kycSuccess = ref('')

onMounted(loadData)

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [appRes, kycRes] = await Promise.allSettled([
      client.get('/seller/me'),
      client.get('/kyc/me').catch(() => ({ data: null })),
    ])
    if (appRes.status === 'fulfilled') sellerApp.value = appRes.value.data
    if (kycRes.status === 'fulfilled') kycRecord.value = kycRes.value.data
  } catch (e) {
    error.value = 'Failed to load seller data.'
  } finally {
    loading.value = false
  }
}

async function submitApplication() {
  error.value = ''
  success.value = ''
  submitting.value = true
  const payload = {
    ...form.value,
    gst_number: form.value.gst_number || null,
  }
  try {
    const res = await client.post('/seller/apply', payload)
    sellerApp.value = res.data
    success.value = 'Application submitted! Our team will review it shortly.'
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to submit application.'
  } finally {
    submitting.value = false
  }
}

async function createKYC() {
  kycError.value = ''
  kycSuccess.value = ''
  kycSubmitting.value = true
  try {
    const res = await client.post('/kyc', kycForm.value)
    kycRecord.value = res.data
    kycSuccess.value = 'KYC details saved! Now upload your document.'
  } catch (e) {
    kycError.value = e.response?.data?.detail || 'Failed to save KYC details.'
  } finally {
    kycSubmitting.value = false
  }
}

function handleKYCDocumentChange(e) {
  kycDocument.value = e.target.files[0] || null
}

async function uploadKYCDocument() {
  if (!kycDocument.value) { kycError.value = 'Please select a document file.'; return }
  kycError.value = ''
  kycSuccess.value = ''
  kycSubmitting.value = true
  const formData = new FormData()
  formData.append('file', kycDocument.value)
  try {
    const res = await client.post('/kyc/upload-document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    kycRecord.value = res.data
    kycSuccess.value = 'Document uploaded! Under review by our team.'
    kycDocument.value = null
  } catch (e) {
    kycError.value = e.response?.data?.detail || 'Failed to upload document.'
  } finally {
    kycSubmitting.value = false
  }
}

const statusMeta = {
  PENDING:  { label: 'Under Review',  bg: 'bg-yellow-100 text-yellow-800 border-yellow-200',  icon: '⏳' },
  APPROVED: { label: 'Approved',      bg: 'bg-green-100  text-green-800  border-green-200',   icon: '✅' },
  REJECTED: { label: 'Rejected',      bg: 'bg-red-100    text-red-800    border-red-200',      icon: '❌' },
}

const kycStatusMeta = {
  PENDING:  { label: 'Pending Review', cls: 'bg-yellow-500 text-white' },
  VERIFIED: { label: 'Verified',       cls: 'bg-green-600  text-white' },
  REJECTED: { label: 'Rejected',       cls: 'bg-red-500    text-white' },
}
</script>

<template>
  <div class="min-h-screen bg-loopymart-gray">
    <!-- Hero Banner -->
    <div class="bg-loopymart-blue text-white py-12">
      <div class="max-w-container mx-auto px-4 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-white/10 rounded-full mb-4">
          <svg width="32" height="32" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5
                     M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
          </svg>
        </div>
        <h1 class="text-3xl font-bold mb-2">Become a Seller on LoopyMart</h1>
        <p class="text-white/80 max-w-xl mx-auto">
          Join thousands of sellers and grow your business with LoopyMart's
          nationwide customer base, logistics support, and seller tools.
        </p>
        <!-- Benefits -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 max-w-3xl mx-auto">
          <div v-for="b in [
            { icon: '🌐', title: 'Nationwide Reach', desc: 'Sell across India' },
            { icon: '🚚', title: 'Easy Logistics', desc: 'Hassle-free shipping' },
            { icon: '💰', title: 'Weekly Payouts', desc: 'Fast & reliable payments' },
            { icon: '📊', title: 'Seller Dashboard', desc: 'Track your performance' },
          ]" :key="b.title"
            class="bg-white/10 rounded-lg p-4 text-center backdrop-blur-sm">
            <div class="text-2xl mb-1">{{ b.icon }}</div>
            <p class="font-medium text-sm">{{ b.title }}</p>
            <p class="text-xs text-white/70">{{ b.desc }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-3xl mx-auto px-4 py-8">

      <!-- Loading -->
      <div v-if="loading" class="bg-white shadow-card rounded-sm p-12 text-center">
        <div class="inline-block w-8 h-8 border-4 border-loopymart-blue border-t-transparent rounded-full animate-spin"></div>
        <p class="mt-4 text-text-secondary">Loading...</p>
      </div>

      <template v-else>
        <!-- Global messages -->
        <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm">{{ error }}</div>
        <div v-if="success" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-sm text-green-700 text-sm font-medium">{{ success }}</div>

        <!-- ─── APPLICATION FORM (no existing application) ─── -->
        <div v-if="!sellerApp" class="bg-white shadow-card rounded-sm overflow-hidden">
          <div class="p-5 border-b border-loopymart-gray-dark">
            <h2 class="font-semibold text-text-primary text-lg">Seller Application</h2>
            <p class="text-text-secondary text-sm mt-0.5">Fill in your details to apply. Our team reviews applications within 2–3 business days.</p>
          </div>

          <form @submit.prevent="submitApplication" class="p-6 space-y-8">

            <!-- Section: Store Information -->
            <div>
              <h3 class="text-sm font-semibold text-loopymart-blue uppercase tracking-wide mb-4 flex items-center gap-2">
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                </svg>
                Store Information
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="form-label">Store / Business Name <span class="text-red-500">*</span></label>
                  <input v-model="form.store_name" type="text" required class="form-input" placeholder="e.g. My Electronics Store" />
                </div>
                <div>
                  <label class="form-label">Business Type <span class="text-red-500">*</span></label>
                  <select v-model="form.business_type" required class="form-input">
                    <option>Individual</option>
                    <option>Partnership</option>
                    <option>LLP</option>
                    <option>Company</option>
                  </select>
                </div>
                <div class="md:col-span-2">
                  <label class="form-label">Store Description <span class="text-red-500">*</span></label>
                  <textarea v-model="form.store_description" required rows="3" class="form-input resize-none"
                            placeholder="Briefly describe your store and the products you plan to sell…"></textarea>
                </div>
              </div>
            </div>

            <!-- Section: Contact Details -->
            <div>
              <h3 class="text-sm font-semibold text-loopymart-blue uppercase tracking-wide mb-4 flex items-center gap-2">
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"/>
                </svg>
                Contact Details
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="form-label">Contact Phone <span class="text-red-500">*</span></label>
                  <input v-model="form.phone" type="tel" required class="form-input" placeholder="+91 98765 43210" />
                </div>
                <div>
                  <label class="form-label">Business Email <span class="text-red-500">*</span></label>
                  <input v-model="form.email" type="email" required class="form-input" placeholder="seller@example.com" />
                </div>
                <div class="md:col-span-2">
                  <label class="form-label">Business Address <span class="text-red-500">*</span></label>
                  <textarea v-model="form.address" required rows="2" class="form-input resize-none"
                            placeholder="Full address including city, state and PIN code"></textarea>
                </div>
              </div>
            </div>

            <!-- Section: Tax & Identity -->
            <div>
              <h3 class="text-sm font-semibold text-loopymart-blue uppercase tracking-wide mb-4 flex items-center gap-2">
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                </svg>
                Tax &amp; Identity
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="form-label">PAN Number <span class="text-red-500">*</span></label>
                  <input v-model="form.pan_number" type="text" required class="form-input uppercase"
                         placeholder="ABCDE1234F" maxlength="10" />
                </div>
                <div>
                  <label class="form-label">GST Number <span class="text-text-hint text-xs">(optional)</span></label>
                  <input v-model="form.gst_number" type="text" class="form-input uppercase"
                         placeholder="22ABCDE1234F1Z5" maxlength="15" />
                </div>
              </div>
            </div>

            <!-- Section: Bank Details -->
            <div>
              <h3 class="text-sm font-semibold text-loopymart-blue uppercase tracking-wide mb-4 flex items-center gap-2">
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
                </svg>
                Bank Account Details
              </h3>
              <p class="text-xs text-text-secondary mb-3">Payouts will be credited to this account. Ensure details are accurate.</p>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="md:col-span-2">
                  <label class="form-label">Account Holder Name <span class="text-red-500">*</span></label>
                  <input v-model="form.bank_account_name" type="text" required class="form-input"
                         placeholder="Name as on bank account" />
                </div>
                <div>
                  <label class="form-label">Account Number <span class="text-red-500">*</span></label>
                  <input v-model="form.bank_account_number" type="text" required class="form-input"
                         placeholder="Enter account number" />
                </div>
                <div>
                  <label class="form-label">IFSC Code <span class="text-red-500">*</span></label>
                  <input v-model="form.bank_ifsc" type="text" required class="form-input uppercase"
                         placeholder="e.g. SBIN0001234" maxlength="11" />
                </div>
              </div>
            </div>

            <div class="pt-2 flex items-start gap-3">
              <button type="submit" :disabled="submitting"
                      class="btn btn-primary min-w-[160px] disabled:opacity-60 disabled:cursor-not-allowed">
                <span v-if="submitting">Submitting…</span>
                <span v-else>Submit Application</span>
              </button>
              <p class="text-xs text-text-secondary pt-2">
                By submitting, you agree to LoopyMart's Seller Terms &amp; Conditions.
                Our team will review your application within 2–3 business days.
              </p>
            </div>
          </form>
        </div>

        <!-- ─── STATUS CARD (existing application) ─── -->
        <template v-else>
          <div class="bg-white shadow-card rounded-sm overflow-hidden mb-6">
            <div class="p-5 border-b border-loopymart-gray-dark flex items-center justify-between">
              <h2 class="font-semibold text-text-primary text-lg">Application Status</h2>
              <span :class="[
                'px-3 py-1 rounded-full text-sm font-semibold border',
                statusMeta[sellerApp.status]?.bg ?? 'bg-gray-100 text-gray-800 border-gray-200'
              ]">
                {{ statusMeta[sellerApp.status]?.icon }} {{ statusMeta[sellerApp.status]?.label ?? sellerApp.status }}
              </span>
            </div>
            <div class="p-6 space-y-4">
              <!-- Status messages -->
              <div v-if="sellerApp.status === 'PENDING'"
                   class="p-4 bg-yellow-50 border border-yellow-200 rounded-sm text-yellow-800 text-sm">
                <strong>Your application is under review.</strong> We'll notify you once a decision is made.
                Typical review time is 2–3 business days.
              </div>
              <div v-else-if="sellerApp.status === 'APPROVED'"
                   class="p-4 bg-green-50 border border-green-200 rounded-sm text-green-800 text-sm">
                <strong>Congratulations! Your seller application has been approved.</strong>
                Complete your KYC verification below to activate your seller account.
              </div>
              <div v-else-if="sellerApp.status === 'REJECTED'"
                   class="p-4 bg-red-50 border border-red-200 rounded-sm text-red-800 text-sm">
                <strong>Your application was not approved.</strong>
                <span v-if="sellerApp.remarks"> Reason: {{ sellerApp.remarks }}</span>
              </div>

              <!-- Application Summary -->
              <div class="grid grid-cols-2 md:grid-cols-3 gap-4 pt-2">
                <div v-for="field in [
                  { label: 'Store Name', value: sellerApp.store_name },
                  { label: 'Business Type', value: sellerApp.business_type },
                  { label: 'Contact Phone', value: sellerApp.phone },
                  { label: 'Business Email', value: sellerApp.email },
                  { label: 'PAN Number', value: sellerApp.pan_number },
                  { label: 'GST Number', value: sellerApp.gst_number || '—' },
                ]" :key="field.label">
                  <p class="text-xs text-text-secondary">{{ field.label }}</p>
                  <p class="text-sm font-medium text-text-primary truncate">{{ field.value }}</p>
                </div>
              </div>
              <div>
                <p class="text-xs text-text-secondary">Address</p>
                <p class="text-sm text-text-primary">{{ sellerApp.address }}</p>
              </div>
              <p class="text-xs text-text-secondary mt-2">
                Submitted on {{ new Date(sellerApp.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' }) }}
              </p>
            </div>
          </div>

          <!-- ─── KYC SECTION (only for applicants) ─── -->
          <div class="bg-white shadow-card rounded-sm overflow-hidden">
            <div class="p-5 border-b border-loopymart-gray-dark flex items-center gap-3">
              <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" class="text-loopymart-blue">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
              <div>
                <h2 class="font-semibold text-text-primary">KYC Verification</h2>
                <p class="text-xs text-text-secondary mt-0.5">Required to activate your seller account</p>
              </div>
              <span v-if="kycRecord" :class="['ml-auto px-2.5 py-0.5 rounded-full text-xs font-semibold', kycStatusMeta[kycRecord.status]?.cls]">
                {{ kycStatusMeta[kycRecord.status]?.label ?? kycRecord.status }}
              </span>
            </div>

            <div class="p-6">
              <!-- KYC messages -->
              <div v-if="kycError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm">{{ kycError }}</div>
              <div v-if="kycSuccess" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-sm text-green-700 text-sm font-medium">{{ kycSuccess }}</div>

              <!-- Step 1: Submit KYC details -->
              <div v-if="!kycRecord" class="space-y-4 max-w-md">
                <p class="text-sm text-text-secondary">Submit your identity document details for verification.</p>
                <form @submit.prevent="createKYC" class="space-y-4">
                  <div>
                    <label class="form-label">Document Type <span class="text-red-500">*</span></label>
                    <select v-model="kycForm.document_type" class="form-input">
                      <option value="AADHAR">Aadhaar Card</option>
                      <option value="PAN">PAN Card</option>
                    </select>
                  </div>
                  <div>
                    <label class="form-label">Document Number <span class="text-red-500">*</span></label>
                    <input v-model="kycForm.document_number" type="text" required class="form-input"
                           placeholder="Enter document number" />
                  </div>
                  <button type="submit" :disabled="kycSubmitting" class="btn btn-primary disabled:opacity-60 disabled:cursor-not-allowed">
                    <span v-if="kycSubmitting">Saving…</span>
                    <span v-else>Save KYC Details</span>
                  </button>
                </form>
              </div>

              <!-- Step 2: Upload document image -->
              <div v-else class="space-y-6">
                <div class="flex flex-wrap gap-6 p-4 bg-loopymart-gray rounded-sm">
                  <div>
                    <p class="text-xs text-text-secondary">Document Type</p>
                    <p class="font-medium">{{ kycRecord.document_type }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-text-secondary">Document Number</p>
                    <p class="font-medium">{{ kycRecord.document_number }}</p>
                  </div>
                  <div>
                    <p class="text-xs text-text-secondary">Status</p>
                    <span :class="['px-2.5 py-0.5 rounded-full text-xs font-semibold', kycStatusMeta[kycRecord.status]?.cls]">
                      {{ kycStatusMeta[kycRecord.status]?.label ?? kycRecord.status }}
                    </span>
                  </div>
                </div>

                <div v-if="!kycRecord.document_image_url">
                  <h3 class="font-medium text-text-primary mb-3 text-sm">Upload Document Image</h3>
                  <p class="text-xs text-text-secondary mb-3">Upload a clear photo or scan of your {{ kycRecord.document_type }} card. Accepted: JPEG, PNG, PDF (max 10MB).</p>
                  <div class="flex items-center gap-3">
                    <input type="file" accept="image/*,application/pdf" id="kyc-doc-upload"
                           class="hidden" @change="handleKYCDocumentChange" />
                    <label for="kyc-doc-upload"
                           class="btn cursor-pointer inline-flex items-center gap-2">
                      <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                      </svg>
                      Choose File
                    </label>
                    <span v-if="kycDocument" class="text-sm text-text-secondary truncate max-w-[160px]">
                      {{ kycDocument.name }}
                    </span>
                    <button v-if="kycDocument" @click="uploadKYCDocument" :disabled="kycSubmitting"
                            class="btn btn-primary disabled:opacity-60 disabled:cursor-not-allowed">
                      <span v-if="kycSubmitting">Uploading…</span>
                      <span v-else>Upload</span>
                    </button>
                  </div>
                </div>

                <div v-else class="p-4 bg-green-50 border border-green-200 rounded-sm">
                  <p class="text-green-700 font-medium flex items-center gap-2 text-sm">
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                    </svg>
                    Document uploaded and under review.
                  </p>
                  <p class="text-xs text-green-600 mt-1">We'll update your KYC status after verification.</p>
                </div>
              </div>
            </div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>
