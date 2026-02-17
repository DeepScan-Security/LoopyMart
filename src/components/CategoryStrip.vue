<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { categories } from '@/api'

const categoryList = ref([])

// Fallback gradients for categories without images
const categoryGradients = {
  electronics: 'from-blue-400 to-blue-600',
  fashion: 'from-pink-400 to-rose-500',
  home: 'from-amber-400 to-orange-500',
  books: 'from-green-400 to-teal-500',
  sports: 'from-purple-400 to-indigo-500',
  beauty: 'from-red-400 to-pink-500',
  default: 'from-gray-400 to-gray-600'
}

function getCategoryGradient(slug) {
  const normalizedSlug = slug?.toLowerCase() || ''
  if (normalizedSlug.includes('electronic')) return categoryGradients.electronics
  if (normalizedSlug.includes('fashion')) return categoryGradients.fashion
  if (normalizedSlug.includes('home') || normalizedSlug.includes('kitchen')) return categoryGradients.home
  if (normalizedSlug.includes('book')) return categoryGradients.books
  if (normalizedSlug.includes('sport') || normalizedSlug.includes('fitness')) return categoryGradients.sports
  if (normalizedSlug.includes('beauty') || normalizedSlug.includes('personal')) return categoryGradients.beauty
  return categoryGradients.default
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
              'w-20 h-20 rounded-full flex items-center justify-center overflow-hidden',
              'shadow-sm group-hover:shadow-md transition-all group-hover:scale-105',
              category.image_url ? 'bg-flipkart-gray' : 'bg-gradient-to-br ' + getCategoryGradient(category.slug)
            ]"
          >
            <!-- Show image if available -->
            <img 
              v-if="category.image_url"
              :src="category.image_url"
              :alt="category.name"
              class="w-12 h-12 object-contain"
            />
            <!-- Fallback to letter if no image -->
            <span v-else class="text-2xl text-white font-bold">
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
