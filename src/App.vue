<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import CategoryNav from '@/components/CategoryNav.vue'
import AppFooter from '@/components/AppFooter.vue'

const route = useRoute()
const showHeader = computed(() => !route.meta.hideHeader)
const showCategoryNav = computed(() => !route.meta.hideHeader && !route.meta.hideCategoryNav)
const showFooter = computed(() => !route.meta.hideFooter)
</script>

<template>
  <div class="app min-h-screen flex flex-col bg-loopymart-gray">
    <AppHeader v-if="showHeader" />
    <CategoryNav v-if="showCategoryNav" />
    <main class="flex-1">
      <RouterView />
    </main>
    <AppFooter v-if="showFooter" />
  </div>
</template>
