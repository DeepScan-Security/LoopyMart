<template>
  <Teleport to="body">
    <div
      v-if="pickerVisible"
      class="fixed inset-0 z-[200] flex items-center justify-center"
      @click.self="closePicker"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/40" @click="closePicker"></div>

      <!-- Modal -->
      <div class="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 overflow-hidden z-10">
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <h2 class="text-base font-semibold text-gray-800">
            Save to Wishlist
          </h2>
          <button
            class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition"
            @click="closePicker"
          >
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <!-- Product name hint -->
        <p v-if="pickerProductName" class="px-5 pt-3 text-sm text-gray-500 truncate">
          Product: <span class="text-gray-800 font-medium">{{ pickerProductName }}</span>
        </p>

        <!-- Wishlists list -->
        <div class="px-5 py-3 max-h-72 overflow-y-auto space-y-2">
          <div v-if="loading" class="text-center py-4 text-gray-400 text-sm">Loading…</div>
          <div v-else-if="!wishlists.length" class="text-center py-4 text-gray-400 text-sm">
            No wishlists yet. Create one below.
          </div>
          <template v-else>
            <button
              v-for="list in wishlists"
              :key="list.id"
              class="w-full flex items-center justify-between px-3 py-2.5 rounded-md border text-sm transition"
              :class="listContains(list.id)
                ? 'border-loopymart-blue bg-blue-50 text-loopymart-blue'
                : 'border-gray-200 hover:border-loopymart-blue hover:bg-gray-50'"
              @click="toggleItem(list.id)"
            >
              <span class="flex items-center gap-2">
                <!-- Heart filled/empty -->
                <svg
                  width="16" height="16"
                  :fill="listContains(list.id) ? 'currentColor' : 'none'"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                </svg>
                <span class="font-medium truncate max-w-[200px]">{{ list.name }}</span>
              </span>
              <span class="text-xs text-gray-400">{{ list.item_count }} items</span>
            </button>
          </template>
        </div>

        <!-- Create new wishlist -->
        <div class="px-5 pb-5 pt-2 border-t border-gray-100">
          <p class="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
            Create new wishlist
          </p>
          <div class="flex gap-2">
            <input
              v-model="newName"
              type="text"
              placeholder="e.g. Birthday, Tech Wishlist…"
              maxlength="60"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm
                     focus:outline-none focus:border-loopymart-blue"
              @keyup.enter="createAndAdd"
            />
            <button
              :disabled="!newName.trim() || creating"
              class="px-4 py-2 bg-loopymart-blue text-white rounded-md text-sm font-medium
                     disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition"
              @click="createAndAdd"
            >
              {{ creating ? '…' : 'Create' }}
            </button>
          </div>
          <p v-if="errorMsg" class="mt-2 text-xs text-red-500">{{ errorMsg }}</p>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import { useWishlist } from '@/composables/useWishlist'

const {
  wishlists,
  loading,
  pickerVisible,
  pickerProductId,
  pickerProductName,
  closePicker,
  createWishlist,
  addToWishlist,
  removeFromWishlist,
  wishlistIdsContaining,
} = useWishlist()

const newName = ref('')
const creating = ref(false)
const errorMsg = ref('')

function listContains(wishlistId) {
  return wishlistIdsContaining(pickerProductId.value).includes(wishlistId)
}

async function toggleItem(wishlistId) {
  if (!pickerProductId.value) return
  errorMsg.value = ''
  try {
    if (listContains(wishlistId)) {
      await removeFromWishlist(wishlistId, pickerProductId.value)
    } else {
      await addToWishlist(wishlistId, pickerProductId.value)
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Something went wrong'
  }
}

async function createAndAdd() {
  const name = newName.value.trim()
  if (!name) return
  creating.value = true
  errorMsg.value = ''
  try {
    const newList = await createWishlist(name)
    newName.value = ''
    if (pickerProductId.value) {
      await addToWishlist(newList.id, pickerProductId.value)
    }
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Failed to create wishlist'
  } finally {
    creating.value = false
  }
}
</script>
