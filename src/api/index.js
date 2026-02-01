import client from './client'

export const auth = {
  register: (data) => client.post('/auth/register', data),
  login: (data) => client.post('/auth/login', data),
  me: () => client.get('/auth/me'),
}

export const categories = {
  list: () => client.get('/categories'),
  getBySlug: (slug) => client.get(`/categories/${slug}`),
}

export const products = {
  list: (params) => client.get('/products', { params }),
  get: (id) => client.get(`/products/${id}`),
}

export const cart = {
  list: () => client.get('/cart'),
  add: (data) => client.post('/cart', data),
  update: (id, data) => client.patch(`/cart/${id}`, data),
  remove: (id) => client.delete(`/cart/${id}`),
}

export const orders = {
  list: () => client.get('/orders'),
  get: (id) => client.get(`/orders/${id}`),
  create: (data) => client.post('/orders', data),
}

export const admin = {
  createCategory: (data) => client.post('/admin/categories', data),
  updateCategory: (id, data) => client.put(`/admin/categories/${id}`, data),
  deleteCategory: (id) => client.delete(`/admin/categories/${id}`),
  createProduct: (data) => client.post('/admin/products', data),
  updateProduct: (id, data) => client.put(`/admin/products/${id}`, data),
  deleteProduct: (id) => client.delete(`/admin/products/${id}`),
  uploadImage: (file) => {
    const form = new FormData()
    form.append('file', file)
    return client.post('/admin/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
