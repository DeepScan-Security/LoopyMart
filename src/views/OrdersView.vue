<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { orders } from '@/api'

const list = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await orders.list()
    list.value = res.data
  } catch (_) {
    list.value = []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="orders-page">
    <h1>Order History</h1>
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="!list.length" class="empty">
      <p>You have no orders yet.</p>
      <RouterLink to="/products" class="btn btn-primary">Shop now</RouterLink>
    </div>
    <div v-else class="order-list">
      <div v-for="order in list" :key="order.id" class="order-card card">
        <div class="order-header">
          <span class="order-id">Order #{{ order.id }}</span>
          <span class="order-status">{{ order.status }}</span>
          <span class="order-total">₹{{ order.total.toLocaleString('en-IN') }}</span>
        </div>
        <p class="order-address">{{ order.shipping_address }}</p>
        <ul class="order-items">
          <li v-for="item in order.items" :key="item.id">
            {{ item.product_name }} × {{ item.quantity }} — ₹{{ (item.price_at_order * item.quantity).toLocaleString('en-IN') }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.orders-page h1 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}
.loading, .empty {
  padding: 2rem;
  text-align: center;
}
.empty .btn {
  margin-top: 1rem;
}
.order-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.order-card {
  padding: 1.25rem;
}
.order-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}
.order-id {
  font-weight: 600;
}
.order-status {
  text-transform: capitalize;
  font-size: 0.9rem;
  color: #666;
}
.order-total {
  margin-left: auto;
  font-weight: 700;
  color: #2874f0;
}
.order-address {
  font-size: 0.9rem;
  color: #555;
  margin-bottom: 0.75rem;
}
.order-items {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 0.9rem;
}
.order-items li {
  padding: 0.2rem 0;
}
</style>
