<script setup>
import { RouterLink } from 'vue-router'

const footerLinks = {
  about: [
    { label: 'Contact Us', to: '#' },
    { label: 'About Us', to: '#' },
    { label: 'Careers', to: '#' },
    { label: 'Press', to: '#' },
    { label: 'Corporate Information', to: '#' },
  ],
  help: [
    { label: 'Payments', to: '#' },
    { label: 'Shipping', to: '#' },
    { label: 'Cancellation & Returns', to: '#' },
    { label: 'FAQ', to: '#' },
    { label: 'Report Infringement', to: '#' },
  ],
  policy: [
    { label: 'Return Policy', to: '#' },
    { label: 'Terms Of Use', to: '#' },
    { label: 'Security', to: '#' },
    { label: 'Privacy', to: '#' },
    { label: 'Sitemap', to: '#' },
  ],
  social: [
    { label: 'Facebook', to: '#' },
    { label: 'Twitter', to: '#' },
    { label: 'YouTube', to: '#' },
  ],
}
</script>

<template>
  <footer class="bg-[#172337] text-white mt-auto">
    <!-- Main Footer -->
    <div class="max-w-container mx-auto px-4 py-10">
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-8">
        <!-- About Section -->
        <div>
          <h3 class="text-xs text-text-hint uppercase tracking-wider mb-4">About</h3>
          <ul class="space-y-2">
            <li v-for="link in footerLinks.about" :key="link.label">
              <a :href="link.to" class="text-xs text-white/70 hover:text-white transition-colors">
                {{ link.label }}
              </a>
            </li>
          </ul>
        </div>

        <!-- Help Section -->
        <div>
          <h3 class="text-xs text-text-hint uppercase tracking-wider mb-4">Help</h3>
          <ul class="space-y-2">
            <li v-for="link in footerLinks.help" :key="link.label">
              <a :href="link.to" class="text-xs text-white/70 hover:text-white transition-colors">
                {{ link.label }}
              </a>
            </li>
          </ul>
        </div>

        <!-- Consumer Policy -->
        <div>
          <h3 class="text-xs text-text-hint uppercase tracking-wider mb-4">Consumer Policy</h3>
          <ul class="space-y-2">
            <li v-for="link in footerLinks.policy" :key="link.label">
              <a :href="link.to" class="text-xs text-white/70 hover:text-white transition-colors">
                {{ link.label }}
              </a>
            </li>
          </ul>
        </div>

        <!-- Social -->
        <div>
          <h3 class="text-xs text-text-hint uppercase tracking-wider mb-4">Social</h3>
          <ul class="space-y-2">
            <li v-for="link in footerLinks.social" :key="link.label">
              <a :href="link.to" class="text-xs text-white/70 hover:text-white transition-colors">
                {{ link.label }}
              </a>
            </li>
          </ul>
        </div>

        <!-- Contact & Address -->
        <div class="col-span-2 lg:col-span-2 lg:border-l lg:border-white/10 lg:pl-8">
          <div class="mb-6">
            <h3 class="text-xs text-text-hint uppercase tracking-wider mb-4">Mail Us:</h3>
            <p class="text-xs text-white/70 leading-relaxed">
              LoopyMart Internet Private Limited,<br />
              Buildings Alyssa, Begonia &<br />
              Clove Embassy Tech Village,<br />
              Outer Ring Road, Devarabeesanahalli Village,<br />
              Bengaluru, 560103,<br />
              Karnataka, India
            </p>
          </div>

          <div>
            <h3 class="text-xs text-text-hint uppercase tracking-wider mb-4">Registered Office:</h3>
            <p class="text-xs text-white/70 leading-relaxed">
              LoopyMart Internet Private Limited,<br />
              Buildings Alyssa, Begonia &<br />
              Clove Embassy Tech Village,<br />
              Outer Ring Road, Devarabeesanahalli Village,<br />
              Bengaluru, 560103,<br />
              Karnataka, India<br />
              CIN: U51109KA2012PTC066107<br />
              Telephone: 044-45614700
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Bar -->
    <div class="border-t border-white/10">
      <div class="max-w-container mx-auto px-4 py-6">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <!-- Left Side - Icons -->
          <div class="flex flex-wrap items-center gap-6">
            <div class="flex items-center gap-2">
              <svg width="20" height="20" class="w-5 h-5 text-loopymart-yellow" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 2a4 4 0 00-4 4v1H5a1 1 0 00-.994.89l-1 9A1 1 0 004 18h12a1 1 0 00.994-1.11l-1-9A1 1 0 0015 7h-1V6a4 4 0 00-4-4zm2 5V6a2 2 0 10-4 0v1h4zm-6 3a1 1 0 112 0 1 1 0 01-2 0zm7-1a1 1 0 100 2 1 1 0 000-2z"/>
              </svg>
              <span class="text-xs text-white/70">Become a Seller</span>
            </div>
            <div class="flex items-center gap-2">
              <svg width="20" height="20" class="w-5 h-5 text-loopymart-yellow" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"/>
              </svg>
              <span class="text-xs text-white/70">Advertise</span>
            </div>
            <div class="flex items-center gap-2">
              <svg width="20" height="20" class="w-5 h-5 text-loopymart-yellow" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z"/>
              </svg>
              <span class="text-xs text-white/70">Gift Cards</span>
            </div>
            <div class="flex items-center gap-2">
              <svg width="20" height="20" class="w-5 h-5 text-loopymart-yellow" fill="currentColor" viewBox="0 0 20 20">
                <path d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"/>
              </svg>
              <span class="text-xs text-white/70">Help Center</span>
            </div>
          </div>

          <!-- Right Side - Copyright -->
          <div class="text-xs text-white/50">
            © 2024-{{ new Date().getFullYear() }} LoopyMart.com
          </div>
        </div>

        <!-- Payment Partners -->
        <div class="mt-6 pt-6 border-t border-white/10 flex flex-wrap items-center gap-4">
          <span class="text-xs text-text-hint">Payment Methods:</span>
          <div class="flex items-center gap-3">
            <div class="w-10 h-6 bg-white/10 rounded-sm flex items-center justify-center text-[8px] text-white/70">
              VISA
            </div>
            <div class="w-10 h-6 bg-white/10 rounded-sm flex items-center justify-center text-[8px] text-white/70">
              MC
            </div>
            <div class="w-10 h-6 bg-white/10 rounded-sm flex items-center justify-center text-[8px] text-white/70">
              UPI
            </div>
            <div class="w-10 h-6 bg-white/10 rounded-sm flex items-center justify-center text-[8px] text-white/70">
              PAYTM
            </div>
            <div class="w-10 h-6 bg-white/10 rounded-sm flex items-center justify-center text-[8px] text-white/70">
              COD
            </div>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>
