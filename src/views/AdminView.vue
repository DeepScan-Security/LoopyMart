<script setup>
import { ref, onMounted, computed } from 'vue'
import { categories, products, admin } from '@/api'

const categoriesList = ref([])
const productsList = ref([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const tab = ref('products')
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
  try {
    const [catRes, prodRes] = await Promise.all([
      categories.list(),
      products.list({ limit: 200 }),
    ])
    categoriesList.value = catRes.data
    productsList.value = prodRes.data
  } catch (_) {}
  finally {
    loading.value = false
  }
}

const categoryOptions = computed(() =>
  categoriesList.value.map((c) => ({ value: c.id, label: c.name }))
)

function imageUrl(url) {
  if (!url) return '/dummy-product.png'
  if (url.startsWith('http') || url.startsWith('//')) return url
  if (url.startsWith('/static/')) return (import.meta.env.DEV ? 'http://127.0.0.1:8001' : '') + url
  return url
}

function openAddProduct() {
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
</script>

<template>
  <div class="admin-page">
    <h1>Admin</h1>
    <div class="tabs">
      <button type="button" class="tab" :class="{ active: tab === 'products' }" @click="tab = 'products'">
        Products
      </button>
      <button type="button" class="tab" :class="{ active: tab === 'categories' }" @click="tab = 'categories'">
        Categories
      </button>
    </div>

    <div v-if="tab === 'products'" class="section">
      <button type="button" class="btn btn-primary" @click="openAddProduct">Add Product</button>
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else class="table-wrap card">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Image</th>
              <th>Name</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in productsList" :key="p.id">
              <td>
                <img :src="imageUrl(p.image_url)" :alt="p.name" class="thumb" />
              </td>
              <td>{{ p.name }}</td>
              <td>₹{{ p.price.toLocaleString('en-IN') }}</td>
              <td>{{ p.stock }}</td>
              <td>
                <button type="button" class="btn small" @click="openEditProduct(p)">Edit</button>
                <button type="button" class="btn btn-danger small" @click="deleteProduct(p.id)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="tab === 'categories'" class="section">
      <button type="button" class="btn btn-primary" @click="openAddCategory">Add Category</button>
      <div v-if="loading" class="loading">Loading...</div>
      <ul v-else class="category-list">
        <li v-for="c in categoriesList" :key="c.id" class="card category-item">
          <span>{{ c.name }}</span> <span class="slug">{{ c.slug }}</span>
          <button type="button" class="btn small" @click="openEditCategory(c)">Edit</button>
          <button type="button" class="btn btn-danger small" @click="deleteCategory(c.id)">Delete</button>
        </li>
      </ul>
    </div>

    <!-- Product modal -->
    <div v-if="showProductForm" class="modal" @click.self="showProductForm = false">
      <div class="modal-content card">
        <h2>{{ editingProduct ? 'Edit Product' : 'Add Product' }}</h2>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>
        <div class="form-group">
          <label>Name</label>
          <input v-model="productForm.name" type="text" required />
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea v-model="productForm.description" rows="2" />
        </div>
        <div class="form-group">
          <label>Price</label>
          <input v-model.number="productForm.price" type="number" step="0.01" min="0" required />
        </div>
        <div class="form-group">
          <label>Stock</label>
          <input v-model.number="productForm.stock" type="number" min="0" />
        </div>
        <div class="form-group">
          <label>Category</label>
          <select v-model="productForm.category_id" required>
            <option v-for="c in categoriesList" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>Image URL (or upload below)</label>
          <input v-model="productForm.image_url" type="text" placeholder="/dummy-product.png" />
        </div>
        <div class="form-group">
          <label>Upload image</label>
          <input ref="uploadFile" type="file" accept="image/*" />
        </div>
        <div class="modal-actions">
          <button type="button" class="btn" @click="showProductForm = false">Cancel</button>
          <button type="button" class="btn btn-primary" :disabled="saving" @click="saveProduct">
            {{ saving ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Category modal -->
    <div v-if="showCategoryForm" class="modal" @click.self="showCategoryForm = false">
      <div class="modal-content card">
        <h2>{{ editingCategory ? 'Edit Category' : 'Add Category' }}</h2>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>
        <div class="form-group">
          <label>Name</label>
          <input v-model="categoryForm.name" type="text" required />
        </div>
        <div class="form-group">
          <label>Slug</label>
          <input v-model="categoryForm.slug" type="text" placeholder="electronics" required />
        </div>
        <div class="modal-actions">
          <button type="button" class="btn" @click="showCategoryForm = false">Cancel</button>
          <button type="button" class="btn btn-primary" :disabled="saving" @click="saveCategory">
            {{ saving ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-page h1 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
.tab {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
.tab.active {
  background: #2874f0;
  color: #fff;
  border-color: #2874f0;
}
.section {
  margin-bottom: 2rem;
}
.section .btn-primary {
  margin-bottom: 1rem;
}
.loading {
  padding: 2rem;
  text-align: center;
}
.table-wrap {
  overflow-x: auto;
}
.admin-table {
  width: 100%;
  border-collapse: collapse;
}
.admin-table th,
.admin-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}
.admin-table .thumb {
  width: 48px;
  height: 48px;
  object-fit: contain;
  background: #f5f5f5;
}
.admin-table .small {
  padding: 0.3rem 0.6rem;
  font-size: 0.85rem;
  margin-right: 0.5rem;
}
.category-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.category-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
}
.category-item .slug {
  color: #666;
  font-size: 0.9rem;
}
.category-item .btn {
  margin-left: auto;
}
.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 1rem;
}
.modal-content {
  max-width: 440px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  padding: 1.5rem;
}
.modal-content h2 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
}
.error {
  color: #e53e3e;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}
.success {
  color: #0a0;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}
.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}
</style>
