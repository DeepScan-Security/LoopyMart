<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { wishlist as wishlistApi } from '@/api'
import { useWishlist } from '@/composables/useWishlist'

const {
  wishlists,
  loading,
  ensureLoaded,
  createWishlist,
  renameWishlist,
  deleteWishlist,
  removeFromWishlist,
} = useWishlist()

// ── Expanded / detail ────────────────────────────────────────────────────────
const expandedId = ref(null)
const expandedDetail = ref(null)
const expandLoading = ref(false)

async function toggleExpand(id) {
  if (expandedId.value === id) {
    expandedId.value = null
    expandedDetail.value = null
    return
  }
  expandedId.value = id
  expandLoading.value = true
  try {
    const res = await wishlistApi.get(id)
    expandedDetail.value = res.data
  } catch (_) {
    expandedDetail.value = null
  } finally {
    expandLoading.value = false
  }
}

async function handleRemoveItem(wishlistId, productId) {
  await removeFromWishlist(wishlistId, productId)
  // Refresh detail
  const res = await wishlistApi.get(wishlistId)
  expandedDetail.value = res.data
}

// ── Create ───────────────────────────────────────────────────────────────────
const newName = ref('')
const creating = ref(false)
async function handleCreate() {
  const n = newName.value.trim()
  if (!n) return
  creating.value = true
  try {
    await createWishlist(n)
    newName.value = ''
  } finally {
    creating.value = false
  }
}

// ── Rename ───────────────────────────────────────────────────────────────────
const renamingId = ref(null)
const renameValue = ref('')

function beginRename(list) {
  renamingId.value = list.id
  renameValue.value = list.name
}

async function commitRename(id) {
  const n = renameValue.value.trim()
  if (!n) return
  await renameWishlist(id, n)
  if (expandedDetail.value?.id === id) {
    expandedDetail.value = { ...expandedDetail.value, name: n }
  }
  renamingId.value = null
}

// ── Delete ───────────────────────────────────────────────────────────────────
const deletingId = ref(null)
async function handleDelete(id) {
  if (!confirm('Delete this wishlist?')) return
  deletingId.value = id
  try {
    await deleteWishlist(id)
    if (expandedId.value === id) {
      expandedId.value = null
      expandedDetail.value = null
    }
  } finally {
    deletingId.value = null
  }
}

// ── Share Preview (CTF SSTI) ─────────────────────────────────────────────────
const shareId = ref(null)
const shareTemplate = ref(
  `<h1>{{ wishlist.name }}</h1>\n<p>Saved by {{ user.name }} &mdash; {{ wishlist.item_count }} item(s)</p>\n<ul>{% for item in wishlist.items %}<li>{{ item.name }} &ndash; ₹{{ item.price }}</li>{% endfor %}</ul>`
)
const shareHtml = ref('')
const shareLoading = ref(false)
const shareError = ref('')

function openShare(id) {
  shareId.value = id
  shareHtml.value = ''
  shareError.value = ''
}

async function renderPreview() {
  if (!shareId.value) return
  shareLoading.value = true
  shareError.value = ''
  try {
    const res = await wishlistApi.sharePreview(shareId.value, shareTemplate.value)
    shareHtml.value = res.data
  } catch (e) {
    shareError.value = e.response?.data?.detail || 'Failed to render preview'
  } finally {
    shareLoading.value = false
  }
}

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  const staticUrl = import.meta.env.VITE_STATIC_URL || ''
  if (url.startsWith('/static/')) return staticUrl + url
  return url
}

onMounted(() => ensureLoaded(true))
</script>

<template>
  <div class="min-h-screen bg-loopymart-gray py-4">
    <div class="max-w-container mx-auto px-4">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <h1 class="text-xl font-semibold text-text-primary flex items-center gap-2">
          <svg width="22" height="22" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
          </svg>
          My Wishlists
        </h1>
        <!-- Create inline form -->
        <div class="flex items-center gap-2">
          <input
            v-model="newName"
            type="text"
            placeholder="New wishlist name…"
            maxlength="60"
            class="px-3 py-2 border border-loopymart-gray-dark rounded-sm text-sm
                   focus:outline-none focus:border-loopymart-blue w-52"
            @keyup.enter="handleCreate"
          />
          <button
            :disabled="!newName.trim() || creating"
            class="px-4 py-2 bg-loopymart-blue text-white rounded-sm text-sm font-medium
                   disabled:opacity-50 hover:opacity-90 transition"
            @click="handleCreate"
          >
            {{ creating ? '…' : '+ Create' }}
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="bg-white shadow-card rounded-sm p-12 text-center">
        <div class="inline-block w-8 h-8 border-4 border-loopymart-blue border-t-transparent
                    rounded-full animate-spin"></div>
        <p class="mt-4 text-text-secondary">Loading wishlists…</p>
      </div>

      <!-- Empty state -->
      <div
        v-else-if="!wishlists.length"
        class="bg-white shadow-card rounded-sm p-12 text-center"
      >
        <svg width="64" height="64" class="w-16 h-16 mx-auto text-text-hint mb-4" fill="none"
             stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
        </svg>
        <h2 class="text-lg font-medium text-text-primary mb-2">No wishlists yet</h2>
        <p class="text-text-secondary mb-4">
          Create a wishlist and save products you love.
        </p>
        <RouterLink to="/products" class="btn btn-primary">Start Shopping</RouterLink>
      </div>

      <!-- Wishlists grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="list in wishlists"
          :key="list.id"
          class="bg-white shadow-card rounded-sm overflow-hidden"
        >
          <!-- Card header -->
          <div class="flex items-center gap-2 px-4 py-3 border-b border-loopymart-gray-dark">
            <!-- Rename input or title -->
            <template v-if="renamingId === list.id">
              <input
                v-model="renameValue"
                type="text"
                maxlength="60"
                class="flex-1 text-sm px-2 py-1 border border-loopymart-blue rounded focus:outline-none"
                @keyup.enter="commitRename(list.id)"
                @keyup.esc="renamingId = null"
                autofocus
              />
              <button
                class="text-xs text-loopymart-blue font-medium hover:underline"
                @click="commitRename(list.id)"
              >Save</button>
              <button
                class="text-xs text-text-secondary hover:text-text-primary"
                @click="renamingId = null"
              >✕</button>
            </template>
            <template v-else>
              <button
                class="flex-1 text-left text-sm font-medium text-text-primary hover:text-loopymart-blue
                       flex items-center gap-1.5 truncate"
                @click="toggleExpand(list.id)"
              >
                <svg width="14" height="14"
                  :fill="expandedId === list.id ? 'currentColor' : 'none'"
                  stroke="currentColor" viewBox="0 0 24 24"
                  class="text-red-500 flex-shrink-0"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                </svg>
                <span class="truncate">{{ list.name }}</span>
              </button>
              <span class="text-xs text-text-secondary flex-shrink-0">{{ list.item_count }} items</span>
              <!-- Actions -->
              <button
                class="text-text-secondary hover:text-loopymart-blue transition p-1 flex-shrink-0"
                title="Rename"
                @click="beginRename(list)"
              >
                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
                </svg>
              </button>
              <button
                class="text-text-secondary hover:text-loopymart-blue transition p-1 flex-shrink-0"
                title="Share Preview"
                @click="openShare(list.id)"
              >
                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/>
                </svg>
              </button>
              <button
                class="text-text-secondary hover:text-red-500 transition p-1 flex-shrink-0"
                title="Delete"
                :disabled="deletingId === list.id"
                @click="handleDelete(list.id)"
              >
                <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </template>
          </div>

          <!-- Expanded product items -->
          <div v-if="expandedId === list.id">
            <div v-if="expandLoading" class="p-6 text-center text-sm text-text-secondary">
              Loading items…
            </div>
            <div
              v-else-if="expandedDetail && !expandedDetail.items?.length"
              class="p-6 text-center text-sm text-text-secondary"
            >
              This wishlist is empty.
              <RouterLink to="/products" class="text-loopymart-blue hover:underline ml-1">
                Browse products
              </RouterLink>
            </div>
            <div v-else-if="expandedDetail" class="divide-y divide-loopymart-gray-dark">
              <div
                v-for="item in expandedDetail.items"
                :key="item.product_id"
                class="flex items-center gap-3 px-4 py-3"
              >
                <RouterLink
                  :to="{ name: 'ProductDetail', params: { id: item.product_id } }"
                  class="w-12 h-12 flex-shrink-0 border border-loopymart-gray-dark rounded-sm p-1"
                >
                  <img
                    :src="imageUrl(item.product_image_url)"
                    :alt="item.product_name"
                    class="w-full h-full object-contain"
                  />
                </RouterLink>
                <div class="flex-1 min-w-0">
                  <RouterLink
                    :to="{ name: 'ProductDetail', params: { id: item.product_id } }"
                    class="text-sm text-text-primary hover:text-loopymart-blue line-clamp-1 block"
                  >
                    {{ item.product_name }}
                  </RouterLink>
                  <p class="text-xs text-text-secondary">
                    ₹{{ item.product_price?.toLocaleString('en-IN') }}
                  </p>
                </div>
                <button
                  class="text-text-secondary hover:text-red-500 transition p-1 flex-shrink-0"
                  title="Remove"
                  @click="handleRemoveItem(list.id, item.product_id)"
                >
                  <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Share Preview Modal (CTF SSTI Challenge) -->
    <Teleport to="body">
      <div
        v-if="shareId"
        class="fixed inset-0 z-[200] flex items-start justify-center pt-12 px-4"
        @click.self="shareId = null; shareHtml = ''"
      >
        <div class="absolute inset-0 bg-black/40" @click="shareId = null; shareHtml = ''"></div>
        <div class="relative bg-white rounded-lg shadow-xl w-full max-w-2xl z-10 overflow-hidden">
          <!-- Header -->
          <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200">
            <div>
              <h2 class="text-base font-semibold text-gray-800">Share Preview</h2>
              <p class="text-xs text-gray-500 mt-0.5">
                Customise the template, then render &amp; share your wishlist.
              </p>
            </div>
            <button
              class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100"
              @click="shareId = null; shareHtml = ''"
            >
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <!-- Hint banner -->
          <div class="px-5 py-2 bg-yellow-50 border-b border-yellow-200 text-xs text-yellow-800">
            <strong>Beta feature:</strong> Your template is rendered on the server.
            Use <code class="bg-yellow-100 px-1 rounded">&#123;&#123; wishlist.name &#125;&#125;</code>,
            <code class="bg-yellow-100 px-1 rounded">&#123;&#123; wishlist.items &#125;&#125;</code>,
            <code class="bg-yellow-100 px-1 rounded">&#123;&#123; user.name &#125;&#125;</code> as variables.
          </div>

          <div class="p-5 space-y-4">
            <!-- Template editor -->
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Template</label>
              <textarea
                v-model="shareTemplate"
                rows="5"
                class="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono
                       focus:outline-none focus:border-loopymart-blue resize-y"
              ></textarea>
            </div>

            <!-- Render button -->
            <button
              class="w-full py-2 bg-loopymart-blue text-white rounded text-sm font-medium
                     hover:opacity-90 transition disabled:opacity-50"
              :disabled="shareLoading"
              @click="renderPreview"
            >
              {{ shareLoading ? 'Rendering…' : 'Render Preview' }}
            </button>

            <!-- Error -->
            <p v-if="shareError" class="text-sm text-red-500">{{ shareError }}</p>

            <!-- Rendered output -->
            <div v-if="shareHtml" class="border border-gray-200 rounded overflow-auto max-h-80">
              <!-- v-html renders server output — intentionally vulnerable for CTF -->
              <div class="text-sm p-4 prose max-w-none" v-html="shareHtml"></div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
