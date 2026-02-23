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
  list: (params = {}) => {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') searchParams.set(k, String(v))
    })
    const qs = searchParams.toString()
    return client.get(qs ? `/products?${qs}` : '/products')
  },
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
  createPayment: (data) => client.post('/orders/create-payment', data),
  verifyPayment: (data) => client.post('/orders/verify-payment', data),
  generateInvoice: (orderId) =>
    client.get(`/orders/${orderId}/invoice`, { responseType: 'blob' }),
}

export const wallet = {
  get: () => client.get('/wallet'),
  redeem: () => client.post('/wallet/redeem'),
  getFlagStore: () => client.get('/wallet/flag-store'),
  purchaseFlag: (itemId) => client.post('/wallet/purchase-flag', { item_id: itemId }),
}

export const wishlist = {
  list: () => client.get('/wishlist'),
  create: (name) => client.post('/wishlist', { name }),
  get: (id) => client.get(`/wishlist/${id}`),
  rename: (id, name) => client.patch(`/wishlist/${id}`, { name }),
  delete: (id) => client.delete(`/wishlist/${id}`),
  addItem: (id, productId) => client.post(`/wishlist/${id}/items`, { product_id: productId }),
  removeItem: (id, productId) => client.delete(`/wishlist/${id}/items/${productId}`),
  checkProduct: (productId) => client.get(`/wishlist/check/${productId}`),
  sharePreview: (id, shareTemplate) =>
    client.post(`/wishlist/${id}/share-preview`, { share_template: shareTemplate }),
}

export const tickets = {
  create: (data) => client.post('/tickets', data),
  mine: () => client.get('/tickets/mine'),
  getByUuid: (uuid) => client.get(`/tickets/${uuid}`),
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
  listOrders: () => client.get('/admin/orders'),
  // Seller applications
  listSellerApplications: () => client.get('/admin/seller-applications'),
  updateSellerApplicationStatus: (id, data) => client.put(`/admin/seller-applications/${id}/status`, data),
  // KYC
  listKYC: () => client.get('/admin/kyc'),
  updateKYCStatus: (id, data) => client.put(`/admin/kyc/${id}/status`, data),
}

export const seller = {
  apply: (data) => client.post('/seller/apply', data),
  getMyApplication: () => client.get('/seller/me'),
}

export const kyc = {
  getMe: () => client.get('/kyc/me'),
  create: (data) => client.post('/kyc', data),
  uploadDocument: (file) => {
    const form = new FormData()
    form.append('file', file)
    return client.post('/kyc/upload-document', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
