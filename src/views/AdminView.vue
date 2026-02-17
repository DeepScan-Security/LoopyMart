<script setup>
import { ref, onMounted, computed } from 'vue'
import { categories, products, admin } from '@/api'

const categoriesList = ref([])
const productsList = ref([])
const ordersList = ref([])
const ordersError = ref('')
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const tab = ref('dashboard')
const showProductForm = ref(false)
const editingProduct = ref(null)
const showCategoryForm = ref(false)
const editingCategory = ref(null)

const productForm = ref({
  name: '',
  description: '',
  price: '',
  image_url: '',
  stock: 0,
  category_id: null,
})
const categoryForm = ref({ name: '', slug: '' })
const uploadFile = ref(null)

onMounted(load)

async function load() {
  loading.value = true
  categoriesList.value = []
  productsList.value = []
  ordersList.value = []
  ordersError.value = ''
  try {
    const [catRes, prodRes, ordRes] = await Promise.allSettled([
      categories.list(),
      products.list({ limit: 100 }),
      admin.listOrders(),
    ])
    if (catRes.status === 'fulfilled' && catRes.value?.data != null) {
      categoriesList.value = catRes.value.data
    }
    if (prodRes.status === 'fulfilled' && prodRes.value?.data != null) {
      productsList.value = prodRes.value.data
    }
    if (ordRes.status === 'fulfilled' && ordRes.value?.data != null) {
      ordersList.value = Array.isArray(ordRes.value.data) ? ordRes.value.data : []
    } else if (ordRes.status === 'rejected') {
      const statusCode = ordRes.reason?.response?.status
      if (statusCode === 403) {
        ordersError.value = 'Admin access required to view orders.'
      } else if (statusCode === 401) {
        ordersError.value = 'Please log in as admin to see orders.'
      } else {
        ordersError.value = ordRes.reason?.response?.data?.detail || 'Failed to load orders.'
      }
    }
  } catch (e) {
    // fallback
  } finally {
    loading.value = false
  }
}

// Dashboard stats
const stats = computed(() => ({
  totalProducts: productsList.value.length,
  totalCategories: categoriesList.value.length,
  totalOrders: ordersList.value.length,
  totalRevenue: ordersList.value.reduce((sum, o) => sum + (o.total || 0), 0),
  pendingOrders: ordersList.value.filter(o => o.status === 'pending').length,
  deliveredOrders: ordersList.value.filter(o => o.status === 'delivered').length,
}))

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  const staticUrl = import.meta.env.VITE_STATIC_URL || ''
  if (url.startsWith('/static/')) return staticUrl + url
  return url
}

async function openAddProduct() {
  if (categoriesList.value.length === 0) {
    try {
      const catRes = await categories.list()
      categoriesList.value = catRes.data ?? []
    } catch (_) {}
  }
  editingProduct.value = null
  productForm.value = {
    name: '',
    description: '',
    price: '',
    image_url: '/dummy-product.png',
    stock: 0,
    category_id: categoriesList.value[0]?.id ?? null,
  }
  showProductForm.value = true
  error.value = ''
  success.value = ''
}

function openEditProduct(p) {
  editingProduct.value = p
  productForm.value = {
    name: p.name,
    description: p.description || '',
    price: p.price,
    image_url: p.image_url || '',
    stock: p.stock,
    category_id: p.category_id,
  }
  showProductForm.value = true
  error.value = ''
  success.value = ''
}

async function saveProduct() {
  if (!productForm.value.name || productForm.value.price == null || productForm.value.category_id == null) {
    error.value = 'Name, price and category are required'
    return
  }
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    if (uploadFile.value?.files?.[0]) {
      const up = await admin.uploadImage(uploadFile.value.files[0])
      productForm.value.image_url = up.data.url
    }
    const payload = {
      name: productForm.value.name,
      description: productForm.value.description || null,
      price: parseFloat(productForm.value.price),
      image_url: productForm.value.image_url || null,
      stock: parseInt(productForm.value.stock, 10) || 0,
      category_id: productForm.value.category_id,
    }
    if (editingProduct.value) {
      await admin.updateProduct(editingProduct.value.id, payload)
      success.value = 'Product updated'
    } else {
      await admin.createProduct(payload)
      success.value = 'Product created'
    }
    await load()
    showProductForm.value = false
    editingProduct.value = null
    productForm.value = {
      name: '',
      description: '',
      price: '',
      image_url: '',
      stock: 0,
      category_id: categoriesList.value[0]?.id ?? null,
    }
    if (uploadFile.value) uploadFile.value.value = ''
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to save product'
  } finally {
    saving.value = false
  }
}

async function deleteProduct(id) {
  if (!confirm('Delete this product?')) return
  try {
    await admin.deleteProduct(id)
    await load()
  } catch (_) {}
}

function openAddCategory() {
  editingCategory.value = null
  categoryForm.value = { name: '', slug: '' }
  showCategoryForm.value = true
  error.value = ''
  success.value = ''
}

function openEditCategory(c) {
  editingCategory.value = c
  categoryForm.value = { name: c.name, slug: c.slug }
  showCategoryForm.value = true
  error.value = ''
  success.value = ''
}

async function saveCategory() {
  if (!categoryForm.value.name?.trim() || !categoryForm.value.slug?.trim()) {
    error.value = 'Name and slug are required'
    return
  }
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const payload = {
      name: categoryForm.value.name.trim(),
      slug: categoryForm.value.slug.trim().toLowerCase().replace(/\s+/g, '-'),
    }
    if (editingCategory.value) {
      await admin.updateCategory(editingCategory.value.id, payload)
      success.value = 'Category updated'
    } else {
      await admin.createCategory(payload)
      success.value = 'Category created'
    }
    await load()
    showCategoryForm.value = false
    categoryForm.value = { name: '', slug: '' }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to save category'
  } finally {
    saving.value = false
  }
}

async function deleteCategory(id) {
  if (!confirm('Delete this category? Products in it may be affected.')) return
  try {
    await admin.deleteCategory(id)
    await load()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to delete'
  }
}

const tabs = [
  { id: 'dashboard', label: 'Dashboard', icon: 'chart' },
  { id: 'products', label: 'Products', icon: 'box' },
  { id: 'categories', label: 'Categories', icon: 'folder' },
  { id: 'orders', label: 'Orders', icon: 'truck' },
]
</script>

<template>
  <div class="min-h-screen bg-flipkart-gray">
    <div class="flex">
      <!-- Sidebar -->
      <aside class="w-64 bg-[#1a1a2e] min-h-screen sticky top-0 flex-shrink-0 hidden lg:block">
        <div class="p-6">
          <h1 class="text-xl font-bold text-white">Admin Panel</h1>
          <p class="text-xs text-white/50 mt-1">Clipkart Dashboard</p>
        </div>

        <nav class="px-4 pb-6">
          <button
            v-for="t in tabs"
            :key="t.id"
            @click="tab = t.id"
            :class="[
              'w-full flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors text-left',
              tab === t.id 
                ? 'bg-flipkart-blue text-white' 
                : 'text-white/70 hover:bg-white/10 hover:text-white'
            ]"
          >
            <svg width="20" height="20" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="t.icon === 'chart'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              <path v-if="t.icon === 'box'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
              <path v-if="t.icon === 'folder'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
              <path v-if="t.icon === 'truck'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>
            </svg>
            <span class="font-medium text-sm">{{ t.label }}</span>
          </button>
        </nav>
      </aside>

      <!-- Main Content -->
      <main class="flex-1 p-6">
        <!-- Mobile Tab Selector -->
        <div class="lg:hidden mb-6 flex gap-2 overflow-x-auto scrollbar-hide">
          <button
            v-for="t in tabs"
            :key="t.id"
            @click="tab = t.id"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors',
              tab === t.id 
                ? 'bg-flipkart-blue text-white' 
                : 'bg-white text-text-primary'
            ]"
          >
            {{ t.label }}
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="bg-white shadow-card rounded-lg p-12 text-center">
          <div class="inline-block w-8 h-8 border-4 border-flipkart-blue border-t-transparent 
                      rounded-full animate-spin"></div>
          <p class="mt-4 text-text-secondary">Loading dashboard...</p>
        </div>

        <template v-else>
          <!-- Dashboard Tab -->
          <div v-if="tab === 'dashboard'">
            <h2 class="text-2xl font-bold text-text-primary mb-6">Dashboard Overview</h2>
            
            <!-- Stats Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div class="bg-white shadow-card rounded-lg p-6">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-text-secondary text-sm">Total Products</p>
                    <p class="text-3xl font-bold text-text-primary mt-1">{{ stats.totalProducts }}</p>
                  </div>
                  <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg width="24" height="24" class="w-6 h-6 text-flipkart-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                    </svg>
                  </div>
                </div>
              </div>

              <div class="bg-white shadow-card rounded-lg p-6">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-text-secondary text-sm">Categories</p>
                    <p class="text-3xl font-bold text-text-primary mt-1">{{ stats.totalCategories }}</p>
                  </div>
                  <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <svg width="24" height="24" class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
                    </svg>
                  </div>
                </div>
              </div>

              <div class="bg-white shadow-card rounded-lg p-6">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-text-secondary text-sm">Total Orders</p>
                    <p class="text-3xl font-bold text-text-primary mt-1">{{ stats.totalOrders }}</p>
                  </div>
                  <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg width="24" height="24" class="w-6 h-6 text-flipkart-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                    </svg>
                  </div>
                </div>
              </div>

              <div class="bg-white shadow-card rounded-lg p-6">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-text-secondary text-sm">Total Revenue</p>
                    <p class="text-3xl font-bold text-text-primary mt-1">
                      ₹{{ stats.totalRevenue.toLocaleString('en-IN') }}
                    </p>
                  </div>
                  <div class="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                    <svg width="24" height="24" class="w-6 h-6 text-flipkart-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            <!-- Quick Actions -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="bg-white shadow-card rounded-lg p-6">
                <h3 class="font-medium text-text-primary mb-4">Quick Actions</h3>
                <div class="flex flex-wrap gap-3">
                  <button @click="tab = 'products'; openAddProduct()" class="btn btn-primary">
                    Add Product
                  </button>
                  <button @click="tab = 'categories'; openAddCategory()" class="btn btn-secondary">
                    Add Category
                  </button>
                </div>
              </div>

              <div class="bg-white shadow-card rounded-lg p-6">
                <h3 class="font-medium text-text-primary mb-4">Order Status</h3>
                <div class="flex gap-6">
                  <div>
                    <p class="text-2xl font-bold text-flipkart-orange">{{ stats.pendingOrders }}</p>
                    <p class="text-sm text-text-secondary">Pending</p>
                  </div>
                  <div>
                    <p class="text-2xl font-bold text-flipkart-green">{{ stats.deliveredOrders }}</p>
                    <p class="text-sm text-text-secondary">Delivered</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Products Tab -->
          <div v-if="tab === 'products'">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-2xl font-bold text-text-primary">Products</h2>
              <button @click="openAddProduct" class="btn btn-primary">
                + Add Product
              </button>
            </div>

            <div class="bg-white shadow-card rounded-lg overflow-hidden">
              <div class="overflow-x-auto">
                <table class="w-full">
                  <thead class="bg-flipkart-gray">
                    <tr>
                      <th class="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase">Image</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase">Name</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase">Price</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase">Stock</th>
                      <th class="px-6 py-3 text-right text-xs font-medium text-text-secondary uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-flipkart-gray-dark">
                    <tr v-for="p in productsList" :key="p.id" class="hover:bg-flipkart-gray/50">
                      <td class="px-6 py-4">
                        <img :src="imageUrl(p.image_url)" :alt="p.name" 
                             class="w-12 h-12 object-contain bg-flipkart-gray rounded" />
                      </td>
                      <td class="px-6 py-4">
                        <p class="font-medium text-text-primary">{{ p.name }}</p>
                      </td>
                      <td class="px-6 py-4 text-text-primary">
                        ₹{{ p.price.toLocaleString('en-IN') }}
                      </td>
                      <td class="px-6 py-4">
                        <span :class="[
                          'px-2 py-1 rounded-full text-xs font-medium',
                          p.stock > 10 ? 'bg-green-100 text-flipkart-green' :
                          p.stock > 0 ? 'bg-orange-100 text-flipkart-orange' :
                          'bg-red-100 text-red-600'
                        ]">
                          {{ p.stock }}
                        </span>
                      </td>
                      <td class="px-6 py-4 text-right">
                        <button @click="openEditProduct(p)" class="btn btn-sm mr-2">Edit</button>
                        <button @click="deleteProduct(p.id)" class="btn btn-sm btn-danger">Delete</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- Categories Tab -->
          <div v-if="tab === 'categories'">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-2xl font-bold text-text-primary">Categories</h2>
              <button @click="openAddCategory" class="btn btn-primary">
                + Add Category
              </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div 
                v-for="c in categoriesList" 
                :key="c.id"
                class="bg-white shadow-card rounded-lg p-4 flex items-center justify-between"
              >
                <div>
                  <p class="font-medium text-text-primary">{{ c.name }}</p>
                  <p class="text-sm text-text-secondary">{{ c.slug }}</p>
                </div>
                <div class="flex gap-2">
                  <button @click="openEditCategory(c)" class="btn btn-sm">Edit</button>
                  <button @click="deleteCategory(c.id)" class="btn btn-sm btn-danger">Delete</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Orders Tab -->
          <div v-if="tab === 'orders'">
            <h2 class="text-2xl font-bold text-text-primary mb-6">Orders</h2>

            <div v-if="ordersError" class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600 mb-4">
              {{ ordersError }}
            </div>

            <div v-else-if="ordersList.length === 0" class="bg-white shadow-card rounded-lg p-12 text-center">
              <p class="text-text-secondary">No orders yet.</p>
            </div>

            <div v-else class="bg-white shadow-card rounded-lg overflow-hidden">
              <div class="overflow-x-auto">
                <table class="w-full">
                  <thead class="bg-flipkart-gray">
                    <tr>
                      <th class="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase">Order ID</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase">Customer</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase">Status</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase">Total</th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase">Items</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-flipkart-gray-dark">
                    <tr v-for="order in ordersList" :key="order.id" class="hover:bg-flipkart-gray/50">
                      <td class="px-6 py-4 font-medium text-text-primary">
                        #{{ order.id.slice(0, 8) }}
                      </td>
                      <td class="px-6 py-4">
                        <p class="text-text-primary">{{ order.user_email || '—' }}</p>
                        <p v-if="order.user_name" class="text-xs text-text-secondary">{{ order.user_name }}</p>
                      </td>
                      <td class="px-6 py-4">
                        <span :class="[
                          'px-2 py-1 rounded-full text-xs font-medium uppercase',
                          order.status === 'delivered' ? 'bg-green-100 text-flipkart-green' :
                          order.status === 'shipped' ? 'bg-blue-100 text-flipkart-blue' :
                          order.status === 'processing' ? 'bg-orange-100 text-flipkart-orange' :
                          'bg-yellow-100 text-yellow-600'
                        ]">
                          {{ order.status }}
                        </span>
                      </td>
                      <td class="px-6 py-4 font-medium text-text-primary">
                        ₹{{ order.total.toLocaleString('en-IN') }}
                      </td>
                      <td class="px-6 py-4">
                        <ul class="text-sm text-text-secondary">
                          <li v-for="item in order.items.slice(0, 2)" :key="item.id">
                            {{ item.product_name }} × {{ item.quantity }}
                          </li>
                          <li v-if="order.items.length > 2" class="text-text-hint">
                            +{{ order.items.length - 2 }} more
                          </li>
                        </ul>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </template>
      </main>
    </div>

    <!-- Product Modal -->
    <Teleport to="body">
      <div v-if="showProductForm" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/50" @click="showProductForm = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
          <div class="p-6 border-b border-flipkart-gray-dark">
            <h2 class="text-xl font-bold text-text-primary">
              {{ editingProduct ? 'Edit Product' : 'Add Product' }}
            </h2>
          </div>
          <div class="p-6 space-y-4">
            <div v-if="error" class="p-3 bg-red-50 text-red-600 rounded text-sm">{{ error }}</div>
            <div v-if="success" class="p-3 bg-green-50 text-flipkart-green rounded text-sm">{{ success }}</div>
            
            <div>
              <label class="form-label">Name</label>
              <input v-model="productForm.name" type="text" required class="form-input" />
            </div>
            <div>
              <label class="form-label">Description</label>
              <textarea v-model="productForm.description" rows="2" class="form-input resize-none"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="form-label">Price</label>
                <input v-model.number="productForm.price" type="number" step="0.01" min="0" required class="form-input" />
              </div>
              <div>
                <label class="form-label">Stock</label>
                <input v-model.number="productForm.stock" type="number" min="0" class="form-input" />
              </div>
            </div>
            <div>
              <label class="form-label">Category</label>
              <select v-model="productForm.category_id" required class="form-input">
                <option v-for="c in categoriesList" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div>
              <label class="form-label">Image URL</label>
              <input v-model="productForm.image_url" type="text" class="form-input" placeholder="/dummy-product.png" />
            </div>
            <div>
              <label class="form-label">Or Upload Image</label>
              <input ref="uploadFile" type="file" accept="image/*" class="form-input" />
            </div>
          </div>
          <div class="p-6 border-t border-flipkart-gray-dark flex gap-3 justify-end">
            <button @click="showProductForm = false" class="btn">Cancel</button>
            <button @click="saveProduct" :disabled="saving" class="btn btn-primary">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Category Modal -->
    <Teleport to="body">
      <div v-if="showCategoryForm" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/50" @click="showCategoryForm = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl w-full max-w-md">
          <div class="p-6 border-b border-flipkart-gray-dark">
            <h2 class="text-xl font-bold text-text-primary">
              {{ editingCategory ? 'Edit Category' : 'Add Category' }}
            </h2>
          </div>
          <div class="p-6 space-y-4">
            <div v-if="error" class="p-3 bg-red-50 text-red-600 rounded text-sm">{{ error }}</div>
            <div v-if="success" class="p-3 bg-green-50 text-flipkart-green rounded text-sm">{{ success }}</div>
            
            <div>
              <label class="form-label">Name</label>
              <input v-model="categoryForm.name" type="text" required class="form-input" />
            </div>
            <div>
              <label class="form-label">Slug</label>
              <input v-model="categoryForm.slug" type="text" required class="form-input" placeholder="electronics" />
            </div>
          </div>
          <div class="p-6 border-t border-flipkart-gray-dark flex gap-3 justify-end">
            <button @click="showCategoryForm = false" class="btn">Cancel</button>
            <button @click="saveCategory" :disabled="saving" class="btn btn-primary">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
