<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { categories } from '@/api'

const categoryList = ref([])
const activeCategory = ref(null)

// Category icons mapping - SVGs with inline styles for sizing
const categoryIcons = {
  electronics: `<svg style="width: 100%; height: 100%" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="8" y="12" width="48" height="32" rx="2" stroke="currentColor" stroke-width="2"/>
    <rect x="24" y="44" width="16" height="4" fill="currentColor"/>
    <rect x="20" y="48" width="24" height="2" fill="currentColor"/>
    <circle cx="32" cy="28" r="8" stroke="currentColor" stroke-width="2"/>
  </svg>`,
  fashion: `<svg style="width: 100%; height: 100%" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 16L32 12L44 16V52H20V16Z" stroke="currentColor" stroke-width="2"/>
    <path d="M20 16C20 20 24 24 32 24C40 24 44 20 44 16" stroke="currentColor" stroke-width="2"/>
    <circle cx="32" cy="32" r="4" fill="currentColor"/>
  </svg>`,
  mobiles: `<svg style="width: 100%; height: 100%" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="18" y="8" width="28" height="48" rx="4" stroke="currentColor" stroke-width="2"/>
    <line x1="18" y1="16" x2="46" y2="16" stroke="currentColor" stroke-width="2"/>
    <line x1="18" y1="48" x2="46" y2="48" stroke="currentColor" stroke-width="2"/>
    <circle cx="32" cy="52" r="2" fill="currentColor"/>
  </svg>`,
  home: `<svg style="width: 100%; height: 100%" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 28L32 8L56 28V56H8V28Z" stroke="currentColor" stroke-width="2"/>
    <rect x="24" y="36" width="16" height="20" stroke="currentColor" stroke-width="2"/>
  </svg>`,
  appliances: `<svg style="width: 100%; height: 100%" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="12" y="8" width="40" height="48" rx="2" stroke="currentColor" stroke-width="2"/>
    <rect x="16" y="12" width="32" height="24" stroke="currentColor" stroke-width="2"/>
    <circle cx="24" cy="46" r="3" fill="currentColor"/>
    <circle cx="40" cy="46" r="3" fill="currentColor"/>
  </svg>`,
  beauty: `<svg style="width: 100%; height: 100%" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="32" cy="40" rx="16" ry="16" stroke="currentColor" stroke-width="2"/>
    <rect x="28" y="8" width="8" height="16" stroke="currentColor" stroke-width="2"/>
    <circle cx="32" cy="40" r="6" fill="currentColor"/>
  </svg>`,
  grocery: `<svg style="width: 100%; height: 100%" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 20H12L20 48H52L56 20" stroke="currentColor" stroke-width="2"/>
    <circle cx="24" cy="54" r="4" fill="currentColor"/>
    <circle cx="48" cy="54" r="4" fill="currentColor"/>
    <rect x="24" y="28" width="20" height="12" stroke="currentColor" stroke-width="2"/>
  </svg>`,
  default: `<svg style="width: 100%; height: 100%" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="8" y="8" width="20" height="20" rx="2" stroke="currentColor" stroke-width="2"/>
    <rect x="36" y="8" width="20" height="20" rx="2" stroke="currentColor" stroke-width="2"/>
    <rect x="8" y="36" width="20" height="20" rx="2" stroke="currentColor" stroke-width="2"/>
    <rect x="36" y="36" width="20" height="20" rx="2" stroke="currentColor" stroke-width="2"/>
  </svg>`
}

function getCategoryIcon(slug) {
  const normalizedSlug = slug?.toLowerCase() || ''
  if (normalizedSlug.includes('electronic')) return categoryIcons.electronics
  if (normalizedSlug.includes('fashion') || normalizedSlug.includes('cloth')) return categoryIcons.fashion
  if (normalizedSlug.includes('mobile') || normalizedSlug.includes('phone')) return categoryIcons.mobiles
  if (normalizedSlug.includes('home') || normalizedSlug.includes('furniture')) return categoryIcons.home
  if (normalizedSlug.includes('appliance') || normalizedSlug.includes('tv')) return categoryIcons.appliances
  if (normalizedSlug.includes('beauty') || normalizedSlug.includes('cosmetic')) return categoryIcons.beauty
  if (normalizedSlug.includes('grocery') || normalizedSlug.includes('food')) return categoryIcons.grocery
  return categoryIcons.default
}

onMounted(async () => {
  try {
    const res = await categories.list()
    categoryList.value = res.data
  } catch (_) {
    categoryList.value = []
  }
})

function setActiveCategory(category) {
  activeCategory.value = category
}

function clearActiveCategory() {
  activeCategory.value = null
}
</script>

<template>
  <nav class="bg-white shadow-sm border-b border-loopymart-gray-dark">
    <div class="max-w-container mx-auto px-4">
      <div class="flex items-center justify-center gap-4 overflow-x-auto scrollbar-hide py-2">
        <!-- All Products -->
        <RouterLink
          to="/products"
          class="flex flex-col items-center gap-1 px-4 py-2 min-w-[80px] text-center
                 hover:text-loopymart-blue transition-colors group"
          @mouseenter="clearActiveCategory"
        >
          <div class="w-16 h-16 flex items-center justify-center text-text-secondary 
                      group-hover:text-loopymart-blue transition-colors"
               v-html="categoryIcons.default">
          </div>
          <span class="text-xs font-medium text-text-primary group-hover:text-loopymart-blue 
                       whitespace-nowrap">
            All Products
          </span>
        </RouterLink>

        <!-- Category Items -->
        <div
          v-for="category in categoryList"
          :key="category.id"
          class="relative"
          @mouseenter="setActiveCategory(category)"
          @mouseleave="clearActiveCategory"
        >
          <RouterLink
            :to="{ name: 'Products', query: { category: category.slug } }"
            class="flex flex-col items-center gap-1 px-4 py-2 min-w-[80px] text-center
                   hover:text-loopymart-blue transition-colors group"
          >
            <div class="w-16 h-16 flex items-center justify-center text-text-secondary 
                        group-hover:text-loopymart-blue transition-colors"
                 v-html="getCategoryIcon(category.slug)">
            </div>
            <span class="text-xs font-medium text-text-primary group-hover:text-loopymart-blue 
                         whitespace-nowrap flex items-center gap-1">
              {{ category.name }}
              <svg width="10" height="10" class="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/>
              </svg>
            </span>
          </RouterLink>

          <!-- Dropdown (placeholder for subcategories) -->
          <div
            v-if="activeCategory?.id === category.id"
            class="absolute top-full left-1/2 -translate-x-1/2 mt-0 w-64 bg-white rounded-sm 
                   shadow-dropdown animate-fadeIn z-40"
          >
            <div class="p-4">
              <RouterLink
                :to="{ name: 'Products', query: { category: category.slug } }"
                class="block py-2 text-sm text-text-primary hover:text-loopymart-blue 
                       font-medium transition-colors"
              >
                All {{ category.name }}
              </RouterLink>
              <div class="border-t border-loopymart-gray-dark mt-2 pt-2">
                <p class="text-xs text-text-secondary mb-2">Popular in {{ category.name }}</p>
                <RouterLink
                  :to="{ name: 'Products', query: { category: category.slug } }"
                  class="block py-1.5 text-sm text-text-primary hover:text-loopymart-blue 
                         transition-colors"
                >
                  Best Sellers
                </RouterLink>
                <RouterLink
                  :to="{ name: 'Products', query: { category: category.slug } }"
                  class="block py-1.5 text-sm text-text-primary hover:text-loopymart-blue 
                         transition-colors"
                >
                  New Arrivals
                </RouterLink>
                <RouterLink
                  :to="{ name: 'Products', query: { category: category.slug } }"
                  class="block py-1.5 text-sm text-text-primary hover:text-loopymart-blue 
                         transition-colors"
                >
                  Top Deals
                </RouterLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

