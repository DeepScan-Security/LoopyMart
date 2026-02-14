<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { categories } from '@/api'

const categoryList = ref([])

// Category images (placeholder gradients for demo)
const categoryImages = {
  electronics: 'from-blue-400 to-blue-600',
  fashion: 'from-pink-400 to-rose-500',
  mobiles: 'from-green-400 to-teal-500',
  home: 'from-amber-400 to-orange-500',
  appliances: 'from-purple-400 to-indigo-500',
  beauty: 'from-red-400 to-pink-500',
  grocery: 'from-yellow-400 to-amber-500',
  default: 'from-gray-400 to-gray-600'
}

function getCategoryGradient(slug) {
  const normalizedSlug = slug?.toLowerCase() || ''
  if (normalizedSlug.includes('electronic')) return categoryImages.electronics
  if (normalizedSlug.includes('fashion') || normalizedSlug.includes('cloth')) return categoryImages.fashion
  if (normalizedSlug.includes('mobile') || normalizedSlug.includes('phone')) return categoryImages.mobiles
  if (normalizedSlug.includes('home') || normalizedSlug.includes('furniture')) return categoryImages.home
  if (normalizedSlug.includes('appliance') || normalizedSlug.includes('tv')) return categoryImages.appliances
  if (normalizedSlug.includes('beauty') || normalizedSlug.includes('cosmetic')) return categoryImages.beauty
  if (normalizedSlug.includes('grocery') || normalizedSlug.includes('food')) return categoryImages.grocery
  return categoryImages.default
}

onMounted(async () => {
  try {
    const res = await categories.list()
    categoryList.value = res.data
  } catch (_) {
    categoryList.value = []
  }
})
</script>

<template>
  <section class="bg-white shadow-sm py-4">
    <div class="max-w-container mx-auto px-4">
      <div class="flex items-center justify-around gap-4 overflow-x-auto scrollbar-hide">
        <RouterLink
          v-for="category in categoryList"
          :key="category.id"
          :to="{ name: 'Products', query: { category: category.slug } }"
          class="flex flex-col items-center gap-2 min-w-[100px] text-center group"
        >
          <!-- Category Image Circle -->
          <div 
            :class="[
              'w-20 h-20 rounded-full bg-gradient-to-br flex items-center justify-center',
              'shadow-sm group-hover:shadow-md transition-shadow',
              getCategoryGradient(category.slug)
            ]"
          >
            <span class="text-2xl text-white font-bold">
              {{ category.name?.charAt(0).toUpperCase() }}
            </span>
          </div>
          <span class="text-sm font-medium text-text-primary group-hover:text-flipkart-blue 
                       transition-colors whitespace-nowrap">
            {{ category.name }}
          </span>
        </RouterLink>
      </div>
    </div>
  </section>
</template>
