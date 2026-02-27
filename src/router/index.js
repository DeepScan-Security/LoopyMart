import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/HomeView.vue'), meta: { title: 'Home' } },
  { path: '/products', name: 'Products', component: () => import('@/views/ProductsView.vue'), meta: { title: 'Products', hideCategoryNav: true } },
  { path: '/products/:id', name: 'ProductDetail', component: () => import('@/views/ProductDetailView.vue'), meta: { title: 'Product', hideCategoryNav: true } },
  { path: '/cart', name: 'Cart', component: () => import('@/views/CartView.vue'), meta: { title: 'Cart', auth: true, hideCategoryNav: true } },
  { path: '/wishlist', name: 'Wishlist', component: () => import('@/views/WishlistView.vue'), meta: { title: 'Wishlist', auth: true, hideCategoryNav: true } },
  { path: '/checkout', name: 'Checkout', component: () => import('@/views/CheckoutView.vue'), meta: { title: 'Checkout', auth: true, hideCategoryNav: true } },
  { path: '/orders', name: 'Orders', component: () => import('@/views/OrdersView.vue'), meta: { title: 'Order History', auth: true, hideCategoryNav: true } },
  { path: '/login', name: 'Login', component: () => import('@/views/LoginView.vue'), meta: { title: 'Login', hideHeader: true, hideFooter: true } },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterView.vue'), meta: { title: 'Register', hideHeader: true, hideFooter: true } },
  { path: '/forgot-password', name: 'ForgotPassword', component: () => import('@/views/ForgotPasswordView.vue'), meta: { title: 'Forgot Password', hideHeader: true, hideFooter: true } },
  { path: '/profile', name: 'Profile', component: () => import('@/views/ProfileView.vue'), meta: { title: 'Profile', auth: true, hideCategoryNav: true } },
  { path: '/seller', name: 'BecomeSeller', component: () => import('@/views/BecomeSellerView.vue'), meta: { title: 'Become a Seller', auth: true, hideCategoryNav: true } },
  { path: '/support', name: 'Support', component: () => import('@/views/ChatView.vue'), meta: { title: 'Support Chat', auth: true, hideCategoryNav: true } },
  { path: '/tickets', name: 'SupportTickets', component: () => import('@/views/SupportTicketsView.vue'), meta: { title: 'Support Tickets', auth: true, hideCategoryNav: true } },
  { path: '/spin', name: 'SpinWheel', component: () => import('@/views/SpinWheelView.vue'), meta: { title: 'Spin & Win', auth: true, hideCategoryNav: true } },
  { path: '/wallet', name: 'Wallet', component: () => import('@/views/WalletView.vue'), meta: { title: 'Wallet & Rewards', auth: true, hideCategoryNav: true } },
  { path: '/admin', name: 'Admin', component: () => import('@/views/AdminView.vue'), meta: { title: 'Admin', admin: true, hideHeader: true, hideFooter: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  document.title = to.meta.title ? `${to.meta.title} | LoopyMart` : 'LoopyMart'
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')
  const isAdmin = user?.is_admin === true
  if (to.meta.auth && !token) return next({ name: 'Login', query: { redirect: to.fullPath } })
  if (to.meta.admin && (!token || !isAdmin)) return next({ name: 'Login', query: { redirect: to.fullPath } })
  next()
})

export default router
