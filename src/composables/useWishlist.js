/**
 * Global composable for wishlist state management.
 * Keeps wishlists cached, exposes picker modal state, and wraps all API calls.
 */
import { ref, computed } from 'vue'
import { wishlist as wishlistApi } from '@/api'

// ── Shared reactive state (module-level singleton) ─────────────────────────
const wishlists = ref([])
const loaded = ref(false)
const loading = ref(false)

// Picker modal
const pickerVisible = ref(false)
const pickerProductId = ref(null)
const pickerProductName = ref('')

// ── Helpers ─────────────────────────────────────────────────────────────────
const isLoggedIn = () => !!localStorage.getItem('token')

export function useWishlist() {
  // ── Loading ──────────────────────────────────────────────────────────────

  async function ensureLoaded(force = false) {
    if ((loaded.value && !force) || loading.value) return
    if (!isLoggedIn()) return
    loading.value = true
    try {
      const res = await wishlistApi.list()
      wishlists.value = res.data
      loaded.value = true
    } catch (_) {
      wishlists.value = []
    } finally {
      loading.value = false
    }
  }

  // ── Wishlist CRUD ────────────────────────────────────────────────────────

  async function createWishlist(name) {
    const res = await wishlistApi.create(name)
    wishlists.value.unshift(res.data)
    return res.data
  }

  async function renameWishlist(id, name) {
    const res = await wishlistApi.rename(id, name)
    const idx = wishlists.value.findIndex((w) => w.id === id)
    if (idx !== -1) wishlists.value[idx] = res.data
    return res.data
  }

  async function deleteWishlist(id) {
    await wishlistApi.delete(id)
    wishlists.value = wishlists.value.filter((w) => w.id !== id)
  }

  // ── Item management ──────────────────────────────────────────────────────

  async function addToWishlist(wishlistId, productId) {
    const res = await wishlistApi.addItem(wishlistId, productId)
    const idx = wishlists.value.findIndex((w) => w.id === wishlistId)
    if (idx !== -1) wishlists.value[idx] = res.data
    return res.data
  }

  async function removeFromWishlist(wishlistId, productId) {
    const res = await wishlistApi.removeItem(wishlistId, productId)
    const idx = wishlists.value.findIndex((w) => w.id === wishlistId)
    if (idx !== -1) wishlists.value[idx] = res.data
    return res.data
  }

  // ── Derived helpers ──────────────────────────────────────────────────────

  /** Returns true if productId exists in ANY wishlist. */
  function isInAnyWishlist(productId) {
    return wishlists.value.some((w) =>
      (w.items || []).some((i) => i.product_id === productId)
    )
  }

  /** Returns IDs of wishlists that contain the productId. */
  function wishlistIdsContaining(productId) {
    return wishlists.value
      .filter((w) => (w.items || []).some((i) => i.product_id === productId))
      .map((w) => w.id)
  }

  // ── Picker modal ─────────────────────────────────────────────────────────

  function openPicker(productId, productName = '') {
    if (!isLoggedIn()) {
      window.location.href = '/login'
      return
    }
    ensureLoaded()
    pickerProductId.value = productId
    pickerProductName.value = productName
    pickerVisible.value = true
  }

  function closePicker() {
    pickerVisible.value = false
    pickerProductId.value = null
    pickerProductName.value = ''
  }

  // ── Expose ───────────────────────────────────────────────────────────────
  return {
    wishlists,
    loaded,
    loading,
    pickerVisible,
    pickerProductId,
    pickerProductName,

    ensureLoaded,
    createWishlist,
    renameWishlist,
    deleteWishlist,
    addToWishlist,
    removeFromWishlist,

    isInAnyWishlist,
    wishlistIdsContaining,

    openPicker,
    closePicker,
  }
}
