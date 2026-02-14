<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  autoPlay: {
    type: Boolean,
    default: true
  },
  interval: {
    type: Number,
    default: 4000
  }
})

// Demo banners - in production, these would come from an API
const banners = ref([
  {
    id: 1,
    title: 'Big Billion Days Sale',
    subtitle: 'Up to 80% Off on Electronics',
    bgColor: 'from-blue-600 to-purple-600',
    textColor: 'text-white',
    cta: 'Shop Now'
  },
  {
    id: 2,
    title: 'Fashion Fiesta',
    subtitle: 'Min 50% Off on Top Brands',
    bgColor: 'from-pink-500 to-rose-500',
    textColor: 'text-white',
    cta: 'Explore'
  },
  {
    id: 3,
    title: 'Mobile Bonanza',
    subtitle: 'Exchange Offers + Extra Discounts',
    bgColor: 'from-green-500 to-teal-500',
    textColor: 'text-white',
    cta: 'Buy Now'
  },
  {
    id: 4,
    title: 'Home Appliances',
    subtitle: 'Starting at ₹999',
    bgColor: 'from-orange-500 to-amber-500',
    textColor: 'text-white',
    cta: 'View Offers'
  }
])

const currentIndex = ref(0)
let intervalId = null

function nextSlide() {
  currentIndex.value = (currentIndex.value + 1) % banners.value.length
}

function prevSlide() {
  currentIndex.value = (currentIndex.value - 1 + banners.value.length) % banners.value.length
}

function goToSlide(index) {
  currentIndex.value = index
}

function startAutoPlay() {
  if (props.autoPlay && !intervalId) {
    intervalId = setInterval(nextSlide, props.interval)
  }
}

function stopAutoPlay() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

onMounted(() => {
  startAutoPlay()
})

onUnmounted(() => {
  stopAutoPlay()
})
</script>

<template>
  <div 
    class="relative overflow-hidden bg-white shadow-sm"
    @mouseenter="stopAutoPlay"
    @mouseleave="startAutoPlay"
  >
    <!-- Slides Container -->
    <div 
      class="flex transition-transform duration-500 ease-out"
      :style="{ transform: `translateX(-${currentIndex * 100}%)` }"
    >
      <div
        v-for="banner in banners"
        :key="banner.id"
        class="w-full flex-shrink-0"
      >
        <div 
          :class="[
            'h-48 md:h-64 lg:h-72 bg-gradient-to-r flex items-center',
            banner.bgColor
          ]"
        >
          <div class="max-w-container mx-auto px-8 md:px-16 w-full">
            <div class="max-w-lg">
              <h2 :class="['text-2xl md:text-4xl font-bold mb-2', banner.textColor]">
                {{ banner.title }}
              </h2>
              <p :class="['text-lg md:text-xl mb-4 opacity-90', banner.textColor]">
                {{ banner.subtitle }}
              </p>
              <button 
                class="px-6 py-2.5 bg-white text-flipkart-blue font-medium rounded-sm
                       hover:bg-gray-100 transition-colors shadow-sm"
              >
                {{ banner.cta }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation Arrows -->
    <button
      class="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-20 bg-white/90 
             hover:bg-white shadow-md flex items-center justify-center
             transition-colors rounded-r-sm"
      @click="prevSlide"
    >
      <svg width="24" height="24" class="w-6 h-6 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
      </svg>
    </button>
    <button
      class="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-20 bg-white/90 
             hover:bg-white shadow-md flex items-center justify-center
             transition-colors rounded-l-sm"
      @click="nextSlide"
    >
      <svg width="24" height="24" class="w-6 h-6 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
      </svg>
    </button>

    <!-- Dots Indicator -->
    <div class="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
      <button
        v-for="(banner, index) in banners"
        :key="banner.id"
        :class="[
          'w-2.5 h-2.5 rounded-full transition-all duration-300',
          currentIndex === index 
            ? 'bg-white w-6' 
            : 'bg-white/50 hover:bg-white/75'
        ]"
        @click="goToSlide(index)"
      />
    </div>
  </div>
</template>
