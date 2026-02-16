<script setup>
import { ref, computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import client from '@/api/client'

const route = useRoute()

// Mode: 'request' for forgot password, 'reset' for reset password
const mode = computed(() => route.query.token ? 'reset' : 'request')

// Request mode
const email = ref('')
const requestLoading = ref(false)
const requestSuccess = ref(false)

// Reset mode
const token = computed(() => route.query.token || '')
const newPassword = ref('')
const confirmPassword = ref('')
const resetLoading = ref(false)
const resetSuccess = ref(false)
const showPassword = ref(false)

const error = ref('')

async function requestReset() {
  if (!email.value) {
    error.value = 'Please enter your email'
    return
  }
  
  error.value = ''
  requestLoading.value = true
  
  try {
    await client.post('/auth/forgot-password', { email: email.value })
    requestSuccess.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to send reset email'
  } finally {
    requestLoading.value = false
  }
}

async function resetPassword() {
  if (!newPassword.value || !confirmPassword.value) {
    error.value = 'Please fill in all fields'
    return
  }
  
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  
  if (newPassword.value.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }
  
  error.value = ''
  resetLoading.value = true
  
  try {
    await client.post('/auth/reset-password', {
      token: token.value,
      new_password: newPassword.value,
    })
    resetSuccess.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to reset password'
  } finally {
    resetLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-flipkart-gray flex items-center justify-center py-8 px-4">
    <div class="w-full max-w-4xl bg-white shadow-card rounded-sm overflow-hidden flex">
      <!-- Left Panel - Blue Section -->
      <div class="hidden md:flex w-[40%] bg-flipkart-blue p-10 flex-col justify-between">
        <div>
          <h1 class="text-3xl font-bold text-white mb-4">
            {{ mode === 'request' ? 'Forgot Password?' : 'Reset Password' }}
          </h1>
          <p class="text-white/80 text-lg leading-relaxed">
            {{ mode === 'request' 
              ? "Don't worry! We'll help you recover your account." 
              : 'Create a new secure password for your account.' 
            }}
          </p>
        </div>
        <div class="mt-auto">
          <svg width="192" height="192" class="w-48 h-48 mx-auto text-white/20" viewBox="0 0 200 200" fill="currentColor">
            <rect x="50" y="60" width="100" height="80" rx="10" />
            <circle cx="100" cy="100" r="20" />
            <rect x="95" y="40" width="10" height="30" />
            <path d="M70,60 Q70,30 100,30 Q130,30 130,60" fill="none" stroke="currentColor" 
                  stroke-width="15" stroke-linecap="round"/>
          </svg>
        </div>
      </div>

      <!-- Right Panel - Form Section -->
      <div class="flex-1 p-8 md:p-10">
        <!-- Request Password Reset Mode -->
        <template v-if="mode === 'request'">
          <!-- Mobile Header -->
          <div class="md:hidden text-center mb-8">
            <h1 class="text-2xl font-bold text-flipkart-blue mb-2">Forgot Password?</h1>
            <p class="text-text-secondary text-sm">
              Don't worry! We'll help you recover your account.
            </p>
          </div>

          <!-- Success State -->
          <div v-if="requestSuccess" class="text-center py-8">
            <div class="w-16 h-16 bg-flipkart-green rounded-full flex items-center justify-center 
                        mx-auto mb-4">
              <svg width="32" height="32" class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <h2 class="text-xl font-medium text-text-primary mb-3">Check Your Email</h2>
            <p class="text-text-secondary mb-2">
              If an account exists for <strong class="text-text-primary">{{ email }}</strong>, 
              you will receive a password reset link shortly.
            </p>
            <p class="text-xs text-text-hint mb-6">
              Note: In this demo, the reset token is logged to the server console.
            </p>
            <RouterLink to="/login" class="btn btn-primary">
              Back to Login
            </RouterLink>
          </div>

          <!-- Request Form -->
          <form v-else @submit.prevent="requestReset" class="space-y-6">
            <p class="text-text-secondary text-sm text-center md:text-left">
              Enter your email address and we'll send you a link to reset your password.
            </p>

            <div>
              <label for="email" class="block text-sm text-text-secondary mb-2">
                Email Address
              </label>
              <input
                id="email"
                v-model="email"
                type="email"
                required
                class="w-full px-0 py-2 border-0 border-b-2 border-flipkart-gray-dark 
                       focus:border-flipkart-blue focus:ring-0 text-text-primary
                       placeholder:text-text-hint transition-colors"
                placeholder="Enter your registered email"
              />
            </div>

            <!-- Error Message -->
            <div 
              v-if="error" 
              class="p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm"
            >
              {{ error }}
            </div>

            <button
              type="submit"
              :disabled="requestLoading"
              class="w-full py-3 bg-flipkart-orange text-white font-medium rounded-sm
                     hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {{ requestLoading ? 'Sending...' : 'Send Reset Link' }}
            </button>
          </form>

          <div v-if="!requestSuccess" class="mt-8 pt-6 border-t border-flipkart-gray-dark text-center">
            <p class="text-text-secondary">
              Remember your password? 
              <RouterLink to="/login" class="text-flipkart-blue font-medium hover:underline">
                Login
              </RouterLink>
            </p>
          </div>
        </template>

        <!-- Reset Password Mode -->
        <template v-else>
          <!-- Mobile Header -->
          <div class="md:hidden text-center mb-8">
            <h1 class="text-2xl font-bold text-flipkart-blue mb-2">Reset Password</h1>
            <p class="text-text-secondary text-sm">
              Create a new secure password for your account.
            </p>
          </div>

          <!-- Success State -->
          <div v-if="resetSuccess" class="text-center py-8">
            <div class="w-16 h-16 bg-flipkart-green rounded-full flex items-center justify-center 
                        mx-auto mb-4">
              <svg width="32" height="32" class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <h2 class="text-xl font-medium text-text-primary mb-3">Password Reset Successful!</h2>
            <p class="text-text-secondary mb-6">
              Your password has been reset successfully.
            </p>
            <RouterLink to="/login" class="btn btn-primary">
              Login with New Password
            </RouterLink>
          </div>

          <!-- Reset Form -->
          <form v-else @submit.prevent="resetPassword" class="space-y-6">
            <p class="text-text-secondary text-sm text-center md:text-left">
              Enter your new password below.
            </p>

            <div>
              <label for="new-password" class="block text-sm text-text-secondary mb-2">
                New Password
              </label>
              <div class="relative">
                <input
                  id="new-password"
                  v-model="newPassword"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  minlength="6"
                  class="w-full px-0 py-2 border-0 border-b-2 border-flipkart-gray-dark 
                         focus:border-flipkart-blue focus:ring-0 text-text-primary
                         placeholder:text-text-hint transition-colors pr-10"
                  placeholder="Minimum 6 characters"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-0 top-1/2 -translate-y-1/2 text-text-secondary 
                         hover:text-flipkart-blue"
                >
                  <svg v-if="showPassword" width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" 
                       viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                  </svg>
                  <svg v-else width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                  </svg>
                </button>
              </div>
            </div>

            <div>
              <label for="confirm-password" class="block text-sm text-text-secondary mb-2">
                Confirm Password
              </label>
              <input
                id="confirm-password"
                v-model="confirmPassword"
                type="password"
                required
                class="w-full px-0 py-2 border-0 border-b-2 border-flipkart-gray-dark 
                       focus:border-flipkart-blue focus:ring-0 text-text-primary
                       placeholder:text-text-hint transition-colors"
                placeholder="Confirm new password"
              />
            </div>

            <!-- Error Message -->
            <div 
              v-if="error" 
              class="p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm"
            >
              {{ error }}
            </div>

            <button
              type="submit"
              :disabled="resetLoading"
              class="w-full py-3 bg-flipkart-orange text-white font-medium rounded-sm
                     hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {{ resetLoading ? 'Resetting...' : 'Reset Password' }}
            </button>
          </form>

          <div v-if="!resetSuccess" class="mt-8 pt-6 border-t border-flipkart-gray-dark text-center">
            <RouterLink to="/forgot-password" class="text-flipkart-blue hover:underline">
              Request new reset link
            </RouterLink>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
