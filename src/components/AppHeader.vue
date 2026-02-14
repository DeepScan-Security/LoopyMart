<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const searchQuery = ref('')
const showUserMenu = ref(false)
const showMoreMenu = ref(false)
const userMenuRef = ref(null)
const moreMenuRef = ref(null)

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
  showMoreMenu.value = false
}

function toggleMoreMenu() {
  showMoreMenu.value = !showMoreMenu.value
  showUserMenu.value = false
}

function handleClickOutside(event) {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target)) {
    showUserMenu.value = false
  }
  if (moreMenuRef.value && !moreMenuRef.value.contains(event.target)) {
    showMoreMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

watch(() => route.path, () => {
  showUserMenu.value = false
  showMoreMenu.value = false
})

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  sessionStorage.removeItem('cartCount')
  window.location.href = '/'
}
</script>

<template>
  <header class="bg-flipkart-blue shadow-header sticky top-0 z-50">
    <div class="max-w-container mx-auto px-4">
      <!-- Main Header Row -->
      <div class="flex items-center gap-4 py-2.5">
        <!-- Logo Section -->
        <RouterLink to="/" class="flex flex-col items-start flex-shrink-0">
          <span class="text-white text-xl font-bold italic tracking-tight">Clipkart</span>
          <span class="text-[10px] text-white/70 italic -mt-0.5">
            Explore <span class="text-flipkart-yellow">Plus</span>
            <svg width="10" height="10" class="inline w-2.5 h-2.5 ml-0.5" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0l2.5 5.5L16 6.5l-4 4 1 5.5L8 13l-5 3 1-5.5-4-4 5.5-1z"/>
            </svg>
          </span>
        </RouterLink>

        <!-- Search Bar -->
        <div class="flex-1 max-w-2xl">
          <div class="relative flex items-center bg-white rounded-sm">
            <input
              v-model="searchQuery"
              type="search"
              placeholder="Search for products, brands and more"
              class="w-full py-2.5 pl-4 pr-12 text-sm text-text-primary placeholder:text-text-hint
                     rounded-sm border-none outline-none"
              @keyup.enter="doSearch"
            />
            <button
              type="button"
              class="absolute right-0 h-full px-4 text-flipkart-blue hover:bg-gray-50
                     transition-colors rounded-r-sm"
              @click="doSearch"
            >
              <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Navigation Items -->
        <nav class="flex items-center gap-1">
          <!-- Login/User Dropdown -->
          <div class="relative" ref="userMenuRef">
            <button
              type="button"
              class="flex items-center gap-2 px-4 py-2 text-white font-medium text-sm
                     hover:bg-white/10 rounded-sm transition-colors"
              @click.stop="toggleUserMenu"
            >
              <template v-if="user">
                <div class="w-6 h-6 bg-white text-flipkart-blue rounded-full flex items-center 
                            justify-center text-xs font-bold">
                  {{ user.full_name?.charAt(0).toUpperCase() }}
                </div>
                <span class="hidden md:inline max-w-[100px] truncate">{{ user.full_name }}</span>
              </template>
              <template v-else>
                <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
                <span>Login</span>
              </template>
              <svg width="12" height="12" class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/>
              </svg>
            </button>

            <!-- Dropdown Menu -->
            <div
              v-if="showUserMenu"
              class="absolute top-full right-0 mt-1 w-56 bg-white rounded-sm shadow-dropdown 
                     animate-fadeIn z-50"
            >
              <template v-if="!user">
                <div class="p-4 border-b border-flipkart-gray-dark">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-text-primary">New customer?</span>
                    <RouterLink to="/register" class="text-flipkart-blue text-sm font-medium">
                      Sign Up
                    </RouterLink>
                  </div>
                  <RouterLink
                    to="/login"
                    class="block w-full py-2 text-center bg-flipkart-blue text-white 
                           rounded-sm text-sm font-medium hover:bg-flipkart-blue-dark"
                  >
                    Login
                  </RouterLink>
                </div>
              </template>

              <div class="py-2">
                <template v-if="user">
                  <RouterLink
                    to="/profile"
                    class="flex items-center gap-3 px-4 py-2.5 text-sm text-text-primary 
                           hover:bg-flipkart-gray transition-colors"
                  >
                    <svg width="16" height="16" class="w-4 h-4 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                    My Profile
                  </RouterLink>
                </template>

                <RouterLink
                  to="/orders"
                  class="flex items-center gap-3 px-4 py-2.5 text-sm text-text-primary 
                         hover:bg-flipkart-gray transition-colors"
                >
                  <svg width="16" height="16" class="w-4 h-4 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                  </svg>
                  Orders
                </RouterLink>

                <RouterLink
                  to="/spin"
                  class="flex items-center gap-3 px-4 py-2.5 text-sm text-text-primary 
                         hover:bg-flipkart-gray transition-colors"
                >
                  <svg width="16" height="16" class="w-4 h-4 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"/>
                  </svg>
                  Spin & Win
                </RouterLink>

                <RouterLink
                  to="/support"
                  class="flex items-center gap-3 px-4 py-2.5 text-sm text-text-primary 
                         hover:bg-flipkart-gray transition-colors"
                >
                  <svg width="16" height="16" class="w-4 h-4 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                  </svg>
                  Support Chat
                </RouterLink>

                <template v-if="user?.is_admin">
                  <div class="border-t border-flipkart-gray-dark my-1"></div>
                  <RouterLink
                    to="/admin"
                    class="flex items-center gap-3 px-4 py-2.5 text-sm text-text-primary 
                           hover:bg-flipkart-gray transition-colors"
                  >
                    <svg width="16" height="16" class="w-4 h-4 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    </svg>
                    Admin Dashboard
                  </RouterLink>
                </template>

                <template v-if="user">
                  <div class="border-t border-flipkart-gray-dark my-1"></div>
                  <button
                    type="button"
                    class="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-text-primary 
                           hover:bg-flipkart-gray transition-colors text-left"
                    @click="logout"
                  >
                    <svg width="16" height="16" class="w-4 h-4 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                    </svg>
                    Logout
                  </button>
                </template>
              </div>
            </div>
          </div>

          <!-- Cart -->
          <RouterLink
            to="/cart"
            class="flex items-center gap-2 px-4 py-2 text-white font-medium text-sm
                   hover:bg-white/10 rounded-sm transition-colors relative"
          >
            <div class="relative">
              <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
              <span
                v-if="cartCount > 0"
                class="absolute -top-1.5 -right-1.5 w-4 h-4 bg-flipkart-yellow text-flipkart-blue 
                       text-[10px] font-bold rounded-full flex items-center justify-center"
              >
                {{ cartCount > 9 ? '9+' : cartCount }}
              </span>
            </div>
            <span class="hidden md:inline">Cart</span>
          </RouterLink>

          <!-- Become a Seller -->
          <a
            href="#"
            class="hidden lg:flex items-center gap-2 px-4 py-2 text-white font-medium text-sm
                   hover:bg-white/10 rounded-sm transition-colors"
          >
            <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
            </svg>
            <span>Become a Seller</span>
          </a>

          <!-- More Dropdown -->
          <div class="relative" ref="moreMenuRef">
            <button
              type="button"
              class="flex items-center gap-1 px-3 py-2 text-white font-medium text-sm
                     hover:bg-white/10 rounded-sm transition-colors"
              @click.stop="toggleMoreMenu"
            >
              <svg width="20" height="20" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
              </svg>
            </button>

            <div
              v-if="showMoreMenu"
              class="absolute top-full right-0 mt-1 w-48 bg-white rounded-sm shadow-dropdown 
                     animate-fadeIn z-50"
            >
              <div class="py-2">
                <a
                  href="#"
                  class="flex items-center gap-3 px-4 py-2.5 text-sm text-text-primary 
                         hover:bg-flipkart-gray transition-colors"
                >
                  <svg width="16" height="16" class="w-4 h-4 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
                  </svg>
                  Notification Preferences
                </a>
                <a
                  href="#"
                  class="flex items-center gap-3 px-4 py-2.5 text-sm text-text-primary 
                         hover:bg-flipkart-gray transition-colors"
                >
                  <svg width="16" height="16" class="w-4 h-4 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  24x7 Customer Care
                </a>
                <a
                  href="#"
                  class="flex items-center gap-3 px-4 py-2.5 text-sm text-text-primary 
                         hover:bg-flipkart-gray transition-colors"
                >
                  <svg width="16" height="16" class="w-4 h-4 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"/>
                  </svg>
                  Advertise
                </a>
                <a
                  href="#"
                  class="flex items-center gap-3 px-4 py-2.5 text-sm text-text-primary 
                         hover:bg-flipkart-gray transition-colors"
                >
                  <svg width="16" height="16" class="w-4 h-4 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                  </svg>
                  Download App
                </a>
              </div>
            </div>
          </div>
        </nav>
      </div>
    </div>
  </header>
</template>
