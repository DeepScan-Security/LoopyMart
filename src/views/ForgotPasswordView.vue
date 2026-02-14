<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import client from '@/api/client'

const route = useRoute()
const router = useRouter()

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
  <div class="auth-page">
    <div class="auth-card card">
      <!-- Request Password Reset -->
      <template v-if="mode === 'request'">
        <h1>Forgot Password</h1>
        
        <div v-if="requestSuccess" class="success-message">
          <div class="success-icon">✓</div>
          <h2>Check Your Email</h2>
          <p>
            If an account exists for <strong>{{ email }}</strong>, 
            you will receive a password reset link shortly.
          </p>
          <p class="note">
            Note: In this demo, the reset token is logged to the server console.
          </p>
          <router-link to="/login" class="btn btn-primary">
            Back to Login
          </router-link>
        </div>
        
        <form v-else @submit.prevent="requestReset">
          <p class="description">
            Enter your email address and we'll send you a link to reset your password.
          </p>
          
          <div class="form-group">
            <label for="email">Email Address</label>
            <input 
              id="email" 
              v-model="email" 
              type="email" 
              placeholder="Enter your email"
              required 
            />
          </div>
          
          <p v-if="error" class="error">{{ error }}</p>
          
          <button type="submit" class="btn btn-primary btn-block" :disabled="requestLoading">
            {{ requestLoading ? 'Sending...' : 'Send Reset Link' }}
          </button>
        </form>
        
        <p class="footer">
          Remember your password? <router-link to="/login">Login</router-link>
        </p>
      </template>

      <!-- Reset Password -->
      <template v-else>
        <h1>Reset Password</h1>
        
        <div v-if="resetSuccess" class="success-message">
          <div class="success-icon">✓</div>
          <h2>Password Reset Successful!</h2>
          <p>Your password has been reset successfully.</p>
          <router-link to="/login" class="btn btn-primary">
            Login with New Password
          </router-link>
        </div>
        
        <form v-else @submit.prevent="resetPassword">
          <p class="description">
            Enter your new password below.
          </p>
          
          <div class="form-group">
            <label for="new-password">New Password</label>
            <input 
              id="new-password" 
              v-model="newPassword" 
              type="password" 
              placeholder="Enter new password"
              required 
            />
          </div>
          
          <div class="form-group">
            <label for="confirm-password">Confirm Password</label>
            <input 
              id="confirm-password" 
              v-model="confirmPassword" 
              type="password" 
              placeholder="Confirm new password"
              required 
            />
          </div>
          
          <p v-if="error" class="error">{{ error }}</p>
          
          <button type="submit" class="btn btn-primary btn-block" :disabled="resetLoading">
            {{ resetLoading ? 'Resetting...' : 'Reset Password' }}
          </button>
        </form>
        
        <p class="footer">
          <router-link to="/forgot-password">Request new reset link</router-link>
        </p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  padding: 2rem 0;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 2rem;
}

.auth-card h1 {
  font-size: 1.5rem;
  margin-bottom: 1.25rem;
  text-align: center;
}

.description {
  color: #666;
  margin-bottom: 1.5rem;
  text-align: center;
  font-size: 0.95rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  font-family: inherit;
}

.form-group input:focus {
  outline: none;
  border-color: #2874f0;
}

.error {
  color: #e53e3e;
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background: #fee;
  border-radius: 4px;
}

.btn-block {
  width: 100%;
  margin-top: 0.5rem;
}

.footer {
  margin-top: 1.25rem;
  font-size: 0.95rem;
  text-align: center;
}

.footer a {
  color: #2874f0;
  text-decoration: none;
}

.footer a:hover {
  text-decoration: underline;
}

.success-message {
  text-align: center;
  padding: 1rem 0;
}

.success-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 1rem;
  background: #10b981;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
}

.success-message h2 {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
}

.success-message p {
  color: #666;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.success-message .note {
  font-size: 0.85rem;
  color: #999;
  font-style: italic;
}

.success-message .btn {
  margin-top: 1rem;
}
</style>
