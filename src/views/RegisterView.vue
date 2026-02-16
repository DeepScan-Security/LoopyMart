<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { auth } from '@/api'

const router = useRouter()
const email = ref('')
const password = ref('')
const fullName = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await auth.register({
      email: email.value,
      password: password.value,
      full_name: fullName.value,
    })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    sessionStorage.setItem('cartCount', '0')
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-flipkart-gray flex items-center justify-center py-8 px-4">
    <div class="w-full max-w-4xl bg-white shadow-card rounded-sm overflow-hidden flex">
      <!-- Left Panel - Blue Section -->
      <div class="hidden md:flex w-[40%] bg-flipkart-blue p-10 flex-col justify-between">
        <div>
          <h1 class="text-3xl font-bold text-white mb-4">Looks like you're new here!</h1>
          <p class="text-white/80 text-lg leading-relaxed">
            Sign up with your email to get started
          </p>
        </div>
        <div class="mt-auto">
          <svg width="192" height="192" class="w-48 h-48 mx-auto text-white/20" viewBox="0 0 200 200" fill="currentColor">
            <rect x="40" y="30" width="120" height="80" rx="10" />
            <circle cx="100" cy="150" r="30" />
            <rect x="70" y="110" width="60" height="40" />
          </svg>
        </div>
      </div>

      <!-- Right Panel - Form Section -->
      <div class="flex-1 p-8 md:p-10">
        <!-- Mobile Header -->
        <div class="md:hidden text-center mb-8">
          <h1 class="text-2xl font-bold text-flipkart-blue mb-2">Create Account</h1>
          <p class="text-text-secondary text-sm">
            Sign up with your email to get started
          </p>
        </div>

        <form @submit.prevent="submit" class="space-y-6">
          <!-- Full Name Field -->
          <div>
            <label for="name" class="block text-sm text-text-secondary mb-2">
              Enter Full Name
            </label>
            <input
              id="name"
              v-model="fullName"
              type="text"
              required
              class="w-full px-0 py-2 border-0 border-b-2 border-flipkart-gray-dark 
                     focus:border-flipkart-blue focus:ring-0 text-text-primary
                     placeholder:text-text-hint transition-colors"
              placeholder="Enter your full name"
            />
          </div>

          <!-- Email Field -->
          <div>
            <label for="email" class="block text-sm text-text-secondary mb-2">
              Enter Email
            </label>
            <input
              id="email"
              v-model="email"
              type="email"
              required
              class="w-full px-0 py-2 border-0 border-b-2 border-flipkart-gray-dark 
                     focus:border-flipkart-blue focus:ring-0 text-text-primary
                     placeholder:text-text-hint transition-colors"
              placeholder="Enter your email"
            />
          </div>

          <!-- Password Field -->
          <div>
            <label for="password" class="block text-sm text-text-secondary mb-2">
              Enter Password
            </label>
            <div class="relative">
              <input
                id="password"
                v-model="password"
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

          <!-- Terms Text -->
          <p class="text-xs text-text-secondary">
            By continuing, you agree to Clipkart's 
            <a href="#" class="text-flipkart-blue hover:underline">Terms of Use</a> and 
            <a href="#" class="text-flipkart-blue hover:underline">Privacy Policy</a>.
          </p>

          <!-- Error Message -->
          <div 
            v-if="error" 
            class="p-3 bg-red-50 border border-red-200 rounded-sm text-red-600 text-sm"
          >
            {{ error }}
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3 bg-flipkart-orange text-white font-medium rounded-sm
                   hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {{ loading ? 'Creating Account...' : 'Continue' }}
          </button>
        </form>

        <!-- Login Link -->
        <div class="mt-8 pt-6 border-t border-flipkart-gray-dark text-center">
          <p class="text-text-secondary">
            Existing User? 
            <RouterLink 
              to="/login" 
              class="text-flipkart-blue font-medium hover:underline"
            >
              Log in
            </RouterLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
