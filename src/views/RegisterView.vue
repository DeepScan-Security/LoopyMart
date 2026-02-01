<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '@/api'

const router = useRouter()
const email = ref('')
const password = ref('')
const fullName = ref('')
const error = ref('')
const loading = ref(false)

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
  <div class="auth-page">
    <div class="auth-card card">
      <h1>Register</h1>
      <form @submit.prevent="submit">
        <div class="form-group">
          <label for="name">Full Name</label>
          <input id="name" v-model="fullName" type="text" required />
        </div>
        <div class="form-group">
          <label for="email">Email</label>
          <input id="email" v-model="email" type="email" required />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input id="password" v-model="password" type="password" required />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          {{ loading ? 'Registering...' : 'Register' }}
        </button>
      </form>
      <p class="footer">
        Already have an account? <router-link to="/login">Login</router-link>
      </p>
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
  max-width: 380px;
  padding: 1.5rem;
}
.auth-card h1 {
  font-size: 1.5rem;
  margin-bottom: 1.25rem;
}
.error {
  color: #e53e3e;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}
.btn-block {
  width: 100%;
  margin-top: 0.5rem;
}
.footer {
  margin-top: 1rem;
  font-size: 0.95rem;
  text-align: center;
}
</style>
