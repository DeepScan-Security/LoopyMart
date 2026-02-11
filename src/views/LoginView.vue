<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { auth } from '@/api'

const route = useRoute()
const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const res = await auth.login({ email: email.value, password: password.value })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    try {
      const cartRes = await (await import('@/api')).cart.list()
      const count = cartRes.data.reduce((s, i) => s + i.quantity, 0)
      sessionStorage.setItem('cartCount', String(count))
    } catch (_) {
      sessionStorage.setItem('cartCount', '0')
    }
    const redirect = route.query.redirect || '/'
    window.location.href = redirect
  } catch (e) {
    error.value = e.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card card">
      <h1>Login</h1>
      <form @submit.prevent="submit">
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
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
        <p class="forgot-link">
          <router-link to="/forgot-password">Forgot your password?</router-link>
        </p>
      </form>
      <p class="footer">
        Don't have an account? <router-link to="/register">Register</router-link>
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
.forgot-link {
  margin-top: 0.75rem;
  text-align: right;
  font-size: 0.9rem;
}
.forgot-link a {
  color: #2874f0;
  text-decoration: none;
}
.forgot-link a:hover {
  text-decoration: underline;
}
</style>
