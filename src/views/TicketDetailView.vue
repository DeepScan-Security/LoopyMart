<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { tickets } from '@/api'

const route  = useRoute()

const ticket  = ref(null)
const loading = ref(false)
const error   = ref('')

async function fetchTicket(uuid) {
  if (!uuid) return
  loading.value = true
  error.value   = ''
  ticket.value  = null
  try {
    const res    = await tickets.getByUuid(uuid)
    ticket.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail ?? 'Ticket not found.'
  } finally {
    loading.value = false
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

onMounted(() => fetchTicket(route.params.uuid))

watch(() => route.params.uuid, (uuid) => fetchTicket(uuid))
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 py-8 space-y-6">

    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-800 mb-1">Ticket Details</h1>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center gap-2 text-sm text-gray-400 py-2">
      <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
      </svg>
      Fetching ticket…
    </div>

    <!-- Error -->
    <div
      v-else-if="error"
      class="bg-red-50 border border-red-200 rounded-2xl p-5 text-sm text-red-700"
    >
      <p class="font-semibold mb-1">Not found</p>
      <p>{{ error }}</p>
    </div>

    <!-- Ticket detail card -->
    <div
      v-else-if="ticket"
      class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
    >
      <!-- Card header -->
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between gap-4">
        <div class="flex items-center gap-2 min-w-0">
          <span class="text-sm font-semibold text-gray-800 truncate">{{ ticket.subject }}</span>
        </div>
        <span class="text-xs text-gray-400 whitespace-nowrap flex-shrink-0">
          {{ formatDate(ticket.created_at) }}
        </span>
      </div>

      <!-- Card body -->
      <div class="px-6 py-5 space-y-4">

        <!-- Message -->
        <div>
          <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">Message</p>
          <p class="text-sm text-gray-700 leading-relaxed">{{ ticket.message }}</p>
        </div>

        <!-- UUID -->
        <div>
          <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">UUID</p>
          <span class="font-mono text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded select-all break-all">
            {{ ticket.ticket_uuid }}
          </span>
        </div>

        <!-- Internal note — shown when present on system tickets -->
        <div
          v-if="ticket.flag"
          class="bg-gray-50 border border-gray-200 rounded-xl px-5 py-4"
        >
          <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Internal Note</p>
          <p class="font-mono text-sm text-gray-800 bg-white border border-gray-200 px-3 py-2 rounded-lg select-all break-all">
            {{ ticket.flag }}
          </p>
        </div>

      </div>
    </div>

    <!-- Back link -->
    <router-link
      to="/tickets"
      class="inline-flex items-center gap-1 text-sm text-loopymart-blue hover:underline"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
      </svg>
      Back to My Tickets
    </router-link>

  </div>
</template>
