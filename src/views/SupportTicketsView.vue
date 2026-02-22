<script setup>
import { ref, onMounted } from 'vue'
import client from '@/api/client'

const form = ref({ subject: '', message: '' })
const creating = ref(false)
const createError = ref('')
const createSuccess = ref('')
const myTickets = ref([])
const loading = ref(false)
const fetchError = ref('')

async function createTicket() {
  creating.value = true
  createError.value = ''
  createSuccess.value = ''
  try {
    const res = await client.post('/tickets', form.value)
    createSuccess.value = res.data.ticket_uuid
    form.value = { subject: '', message: '' }
    await fetchMyTickets()
  } catch (err) {
    createError.value = err.response?.data?.detail ?? 'Failed to create ticket.'
  } finally {
    creating.value = false
  }
}

async function fetchMyTickets() {
  loading.value = true
  fetchError.value = ''
  try {
    const res = await client.get('/tickets/mine')
    myTickets.value = res.data
  } catch (err) {
    fetchError.value = err.response?.data?.detail ?? 'Failed to load tickets.'
  } finally {
    loading.value = false
  }
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

onMounted(fetchMyTickets)
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold mb-1 text-gray-800">Support Tickets</h1>
    <p class="text-sm text-gray-500 mb-8">
      Submit a support request and track your open tickets below.
    </p>

    <!-- Create Ticket Form -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-8">
      <h2 class="text-base font-semibold mb-4 text-gray-700">New Ticket</h2>
      <form @submit.prevent="createTicket" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">Subject</label>
          <input
            v-model="form.subject"
            type="text"
            required
            maxlength="120"
            placeholder="e.g. My order hasn't arrived"
            class="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm
                   focus:outline-none focus:ring-2 focus:ring-loopymart-blue/40"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">Message</label>
          <textarea
            v-model="form.message"
            required
            rows="4"
            maxlength="2000"
            placeholder="Describe your issue in detail..."
            class="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm
                   focus:outline-none focus:ring-2 focus:ring-loopymart-blue/40 resize-none"
          />
        </div>
        <div class="flex items-center gap-4">
          <button
            type="submit"
            :disabled="creating"
            class="bg-loopymart-blue hover:bg-loopymart-blue-dark text-white text-sm
                   font-medium px-6 py-2 rounded-lg transition disabled:opacity-50"
          >
            {{ creating ? 'Submitting…' : 'Submit Ticket' }}
          </button>
          <p v-if="createError" class="text-red-500 text-sm">{{ createError }}</p>
        </div>

        <!-- Success banner -->
        <div
          v-if="createSuccess"
          class="bg-green-50 border border-green-200 rounded-lg px-4 py-3"
        >
          <p class="text-sm text-green-700 font-medium">Ticket submitted successfully!</p>
          <p class="text-xs text-green-600 mt-1">
            Ticket ID:
            <span class="font-mono bg-green-100 px-1.5 py-0.5 rounded select-all">
              {{ createSuccess }}
            </span>
          </p>
        </div>
      </form>
    </div>

    <!-- Ticket List -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h2 class="text-base font-semibold mb-4 text-gray-700">My Tickets</h2>

      <div v-if="loading" class="flex items-center gap-2 text-sm text-gray-400 py-4">
        <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
        </svg>
        Loading tickets…
      </div>

      <p v-else-if="fetchError" class="text-sm text-red-500 py-4">{{ fetchError }}</p>

      <div
        v-else-if="myTickets.length === 0"
        class="flex flex-col items-center py-12 text-center"
      >
        <svg class="w-12 h-12 text-gray-200 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"/>
        </svg>
        <p class="text-sm text-gray-400">No tickets yet. Create your first one above.</p>
      </div>

      <ul v-else class="divide-y divide-gray-100">
        <li
          v-for="ticket in myTickets"
          :key="ticket.ticket_uuid"
          class="py-4 first:pt-0 last:pb-0"
        >
          <div class="flex items-start justify-between gap-4 mb-1">
            <span class="font-medium text-gray-800 text-sm leading-snug">
              {{ ticket.subject }}
            </span>
            <span class="text-xs text-gray-400 whitespace-nowrap flex-shrink-0">
              {{ formatDate(ticket.created_at) }}
            </span>
          </div>
          <p class="text-sm text-gray-500 mb-2 line-clamp-2">{{ ticket.message }}</p>
          <span class="inline-block font-mono text-xs bg-gray-100 text-gray-500
                       px-2 py-0.5 rounded select-all">
            {{ ticket.ticket_uuid }}
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>
