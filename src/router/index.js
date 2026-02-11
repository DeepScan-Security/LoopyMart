import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/HomeView.vue'), meta: { title: 'Home' } },
  { path: '/products', name: 'Products', component: () => import('@/views/ProductsView.vue'), meta: { title: 'Products' } },
  { path: '/products/:id', name: 'ProductDetail', component: () => import('@/views/ProductDetailView.vue'), meta: { title: 'Product' } },
  { path: '/cart', name: 'Cart', component: () => import('@/views/CartView.vue'), meta: { title: 'Cart', auth: true } },
  { path: '/checkout', name: 'Checkout', component: () => import('@/views/CheckoutView.vue'), meta: { title: 'Checkout', auth: true } },
  { path: '/orders', name: 'Orders', component: () => import('@/views/OrdersView.vue'), meta: { title: 'Order History', auth: true } },
  { path: '/login', name: 'Login', component: () => import('@/views/LoginView.vue'), meta: { title: 'Login' } },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterView.vue'), meta: { title: 'Register' } },
  { path: '/forgot-password', name: 'ForgotPassword', component: () => import('@/views/ForgotPasswordView.vue'), meta: { title: 'Forgot Password' } },
  { path: '/profile', name: 'Profile', component: () => import('@/views/ProfileView.vue'), meta: { title: 'Profile', auth: true } },
  { path: '/support', name: 'Support', component: () => import('@/views/ChatView.vue'), meta: { title: 'Support Chat', auth: true } },
  { path: '/spin', name: 'SpinWheel', component: () => import('@/views/SpinWheelView.vue'), meta: { title: 'Spin & Win', auth: true } },
  { path: '/admin', name: 'Admin', component: () => import('@/views/AdminView.vue'), meta: { title: 'Admin', admin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  document.title = to.meta.title ? `${to.meta.title} | Flipkart Clone` : 'Flipkart Clone'
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')
  // Only treat boolean `true` as admin. This prevents `"false"` (string) from being truthy.
  const isAdmin = user?.is_admin === true
  if (to.meta.auth && !token) return next({ name: 'Login', query: { redirect: to.fullPath } })
  if (to.meta.admin && (!token || !isAdmin)) return next({ name: 'Login', query: { redirect: to.fullPath } })
  next()
})

export default router
