<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const searchQuery = ref('')
const showUserMenu = ref(false)
const userMenuRef = ref(null)

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

function doSearch() {
  const q = searchQuery.value.trim()
  if (q) {
    router.push({ name: 'Products', query: { q } })
  } else {
    router.push({ name: 'Products' })
  }
  searchQuery.value = ''
}

function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value
}

function handleClickOutside(event) {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target)) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Close menu when route changes
watch(() => route.path, () => {
  showUserMenu.value = false
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
      <RouterLink to="/" class="logo">Clipkart</RouterLink>
      <div class="header-search">
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Search products..."
          class="header-search-input"
          @keyup.enter="doSearch"
        />
        <button type="button" class="header-search-btn" @click="doSearch">🔍</button>
      </div>
      <nav class="nav">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/products">Products</RouterLink>
        <RouterLink v-if="user?.is_admin === true" to="/admin">Admin</RouterLink>
        <RouterLink v-if="user" to="/cart" class="cart-link">
          Cart <span v-if="cartCount > 0" class="badge">{{ cartCount }}</span>
        </RouterLink>
        <template v-if="user">
          <div class="user-menu-wrapper" ref="userMenuRef">
            <button type="button" class="user-menu-btn" @click.stop="toggleUserMenu">
              <span class="user-avatar">{{ user.full_name?.charAt(0).toUpperCase() }}</span>
              <span class="user-name">{{ user.full_name }}</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            <div v-if="showUserMenu" class="user-dropdown">
              <RouterLink to="/profile">
                <span class="menu-icon">👤</span> My Profile
              </RouterLink>
              <RouterLink to="/orders">
                <span class="menu-icon">📦</span> Order History
              </RouterLink>
              <RouterLink to="/spin">
                <span class="menu-icon">🎡</span> Spin & Win
              </RouterLink>
              <RouterLink to="/support">
                <span class="menu-icon">💬</span> Support Chat
              </RouterLink>
              <div class="menu-divider"></div>
              <button type="button" @click="logout">
                <span class="menu-icon">🚪</span> Logout
              </button>
            </div>
          </div>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn btn-outline">Login</RouterLink>
          <RouterLink to="/register" class="btn btn-outline">Register</RouterLink>
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
.header-search {
  display: flex;
  flex: 1;
  max-width: 400px;
  margin: 0 1rem;
}
.header-search-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 4px 0 0 4px;
  font-size: 0.9rem;
}
.header-search-btn {
  padding: 0.5rem 0.75rem;
  background: #fff;
  border: none;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  font-size: 0.9rem;
}
.header-search-btn:hover {
  background: #f0f0f0;
}
@media (max-width: 600px) {
  .header-search {
    display: none;
  }
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
  background: #fff;
  color: #2874f0;
}
.btn-primary:hover {
  background: #f0f0f0;
  color: #1a5bc7;
}

/* User Menu Dropdown */
.user-menu-wrapper {
  position: relative;
}

.user-menu-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.user-menu-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.user-avatar {
  width: 28px;
  height: 28px;
  background: #fff;
  color: #2874f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
}

.dropdown-arrow {
  font-size: 0.6rem;
  opacity: 0.8;
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  z-index: 1000;
  overflow: hidden;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-dropdown a,
.user-dropdown button {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1rem;
  color: #333;
  text-decoration: none;
  font-size: 0.9rem;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}

.user-dropdown a:hover,
.user-dropdown button:hover {
  background: #f5f5f5;
}

.menu-icon {
  font-size: 1rem;
}

.menu-divider {
  height: 1px;
  background: #eee;
  margin: 0.25rem 0;
}
</style>
