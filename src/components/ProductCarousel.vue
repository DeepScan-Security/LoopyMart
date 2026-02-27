<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import ProductCard from './ProductCard.vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  products: {
    type: Array,
    required: true
  },
  viewAllLink: {
    type: String,
    default: '/products'
  },
  bgColor: {
    type: String,
    default: 'bg-white'
  }
})

const scrollContainer = ref(null)

function scrollLeft() {
  if (scrollContainer.value) {
    scrollContainer.value.scrollBy({
      left: -400,
      behavior: 'smooth'
    })
  }
}

function scrollRight() {
  if (scrollContainer.value) {
    scrollContainer.value.scrollBy({
      left: 400,
      behavior: 'smooth'
    })
  }
}
</script>

<template>
  <section :class="['shadow-sm', bgColor]">
    <!-- Header -->
    <div class="flex items-center justify-between p-4 border-b border-loopymart-gray-dark">
      <div class="flex items-center gap-4">
        <h2 class="text-xl font-semibold text-text-primary">{{ title }}</h2>
        <RouterLink 
          :to="viewAllLink"
          class="px-4 py-1.5 bg-loopymart-blue text-white text-sm font-medium rounded-sm
                 hover:bg-loopymart-blue-dark transition-colors"
        >
          View All
        </RouterLink>
      </div>
    </div>

    <!-- Products Scroll Container -->
    <div class="relative group">
      <!-- Left Arrow -->
      <button
        class="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-10 h-24 bg-white/95 
               shadow-md flex items-center justify-center opacity-0 group-hover:opacity-100
               transition-opacity rounded-r-sm hover:bg-white"
        @click="scrollLeft"
      >
        <svg width="24" height="24" class="w-6 h-6 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>

      <!-- Scrollable Products -->
      <div 
        ref="scrollContainer"
        class="flex overflow-x-auto scrollbar-hide gap-0 px-2"
      >
        <ProductCard
          v-for="product in products"
          :key="product.id"
          :product="product"
          variant="horizontal"
        />
      </div>

      <!-- Right Arrow -->
      <button
        class="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-10 h-24 bg-white/95 
               shadow-md flex items-center justify-center opacity-0 group-hover:opacity-100
               transition-opacity rounded-l-sm hover:bg-white"
        @click="scrollRight"
      >
        <svg width="24" height="24" class="w-6 h-6 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
        </svg>
      </button>
    </div>
  </section>
</template>
