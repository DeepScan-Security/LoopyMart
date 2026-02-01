<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
})

const cartCount = computed(() => {
  try {
    const cart = JSON.parse(sessionStorage.getItem('cartCount') || '0')
    return typeof cart === 'number' ? cart : 0
  } catch {
    return 0
  }
})

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  sessionStorage.removeItem('cartCount')
  window.location.href = '/'
}
</script>

<template>
  <header class="header">
    <div class="header-inner">
      <RouterLink to="/" class="logo">Flipkart Clone</RouterLink>
      <nav class="nav">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/products">Products</RouterLink>
        <RouterLink v-if="user" to="/orders">Orders</RouterLink>
        <RouterLink v-if="user?.is_admin" to="/admin">Admin</RouterLink>
        <RouterLink v-if="user" to="/cart" class="cart-link">
          Cart <span v-if="cartCount > 0" class="badge">{{ cartCount }}</span>
        </RouterLink>
        <template v-if="user">
          <span class="user-name">{{ user.full_name }}</span>
          <button type="button" class="btn btn-outline" @click="logout">Logout</button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn btn-outline">Login</RouterLink>
          <RouterLink to="/register" class="btn btn-primary">Register</RouterLink>
        </template>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.header {
  background: #2874f0;
  color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}
.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.logo {
  font-size: 1.35rem;
  font-weight: 700;
  color: #fff;
  text-decoration: none;
}
.nav {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}
.nav a {
  color: rgba(255, 255, 255, 0.95);
  text-decoration: none;
  font-weight: 500;
}
.nav a.router-link-active {
  text-decoration: underline;
}
.cart-link {
  position: relative;
}
.badge {
  background: #ff6161;
  color: #fff;
  font-size: 0.7rem;
  padding: 0.1em 0.4em;
  border-radius: 10px;
  margin-left: 0.2em;
}
.user-name {
  font-size: 0.9rem;
  opacity: 0.95;
}
.btn {
  padding: 0.4rem 0.9rem;
  border-radius: 4px;
  font-weight: 500;
  text-decoration: none;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
}
.btn-outline {
  background: transparent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.8);
}
.btn-primary {
  background: #ffe11b;
  color: #2874f0;
}
.btn-primary:hover {
  background: #f7d700;
  color: #1a5bc7;
}
</style>
