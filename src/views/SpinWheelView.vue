<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import client from '@/api/client'

const router = useRouter()
const user = ref(null)
const loading = ref(true)
const spinning = ref(false)
const spinsRemaining = ref(5)
const reward = ref(null)
const rotation = ref(0)
const error = ref('')
const totalRotation = ref(0) // Track cumulative rotation for multiple spins

// Wheel segments with colors
const segments = [
  { label: '₹10', color: '#ff6b6b', reward: 'wallet' },
  { label: 'Mystery', color: '#9b59b6', reward: 'mystery' },
  { label: '₹50', color: '#45b7d1', reward: 'wallet' },
  { label: 'Coupon', color: '#96ceb4', reward: 'coupon' },
  { label: '₹25', color: '#ffeaa7', reward: 'wallet' },
  { label: 'Try Again', color: '#dfe6e9', reward: 'none' },
  { label: '₹100', color: '#fd79a8', reward: 'wallet' },
  { label: 'Better Luck!', color: '#a29bfe', reward: 'none' },
]

const segmentAngle = computed(() => 360 / segments.length)

// Calculate SVG path for a pie segment
function getSegmentPath(index) {
  const anglePerSegment = 360 / segments.length
  const startAngle = index * anglePerSegment - 90 // Start from top
  const endAngle = startAngle + anglePerSegment
  
  const startRad = (startAngle * Math.PI) / 180
  const endRad = (endAngle * Math.PI) / 180
  
  const cx = 50, cy = 50, r = 48
  
  const x1 = cx + r * Math.cos(startRad)
  const y1 = cy + r * Math.sin(startRad)
  const x2 = cx + r * Math.cos(endRad)
  const y2 = cy + r * Math.sin(endRad)
  
  const largeArc = anglePerSegment > 180 ? 1 : 0
  
  return `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`
}

// Calculate label position for a segment
function getLabelPosition(index) {
  const anglePerSegment = 360 / segments.length
  const midAngle = index * anglePerSegment + anglePerSegment / 2 - 90
  const midRad = (midAngle * Math.PI) / 180
  
  const cx = 50, cy = 50, labelRadius = 32
  
  return {
    x: cx + labelRadius * Math.cos(midRad),
    y: cy + labelRadius * Math.sin(midRad)
  }
}

onMounted(async () => {
  try {
    const res = await client.get('/auth/me')
    user.value = res.data
    spinsRemaining.value = res.data.spins_remaining ?? 5
  } catch (e) {
    error.value = 'Please login to spin the wheel'
  } finally {
    loading.value = false
  }
})

async function spinWheel() {
  if (spinning.value || spinsRemaining.value <= 0) return
  
  spinning.value = true
  error.value = ''
  reward.value = null // Clear previous reward
  
  try {
    const res = await client.post('/spin')
    
    // Calculate target rotation based on reward
    let targetSegment = 7 // Default to "Better Luck!"
    
    if (res.data.prize_type === 'mystery') {
      targetSegment = 1 // Mystery segment
    } else if (res.data.prize_type === 'wallet_cash') {
      const amount = res.data.prize_value
      if (amount === 10) targetSegment = 0
      else if (amount === 25) targetSegment = 4
      else if (amount === 50) targetSegment = 2
      else if (amount === 100) targetSegment = 6
    } else if (res.data.prize_type === 'coupon') {
      targetSegment = 3
    } else {
      // Random "no reward" segment
      targetSegment = [5, 7][Math.floor(Math.random() * 2)]
    }
    
    // Calculate rotation: 5 full spins + landing on target (cumulative)
    const baseRotation = 360 * 5
    const segmentOffset = targetSegment * segmentAngle.value + segmentAngle.value / 2
    const spinRotation = baseRotation + (360 - segmentOffset)
    
    totalRotation.value += spinRotation
    rotation.value = totalRotation.value
    
    // Wait for animation to complete
    setTimeout(() => {
      spinning.value = false
      reward.value = res.data
      spinsRemaining.value = res.data.spins_remaining ?? 0
      
      // Refresh user data for updated wallet balance
      if (res.data.prize_type === 'wallet_cash') {
        client.get('/auth/me').then(r => {
          user.value = r.data
        })
      }
    }, 5000)
  } catch (e) {
    spinning.value = false
    error.value = e.response?.data?.detail || 'Failed to spin the wheel'
    if (e.response?.status === 400) {
      spinsRemaining.value = 0
    }
  }
}

function spinAgain() {
  reward.value = null // Clear reward to show spin button again
}

function goToProducts() {
  router.push('/products')
}
</script>

<template>
  <div class="spin-page">
    <div class="spin-header">
      <h1>Spin & Win!</h1>
      <p>Try your luck and win exciting rewards</p>
    </div>
    
    <div v-if="loading" class="loading">Loading...</div>
    
    <div v-else-if="error && !user" class="auth-required">
      <p>{{ error }}</p>
      <router-link to="/login?redirect=/spin" class="btn btn-primary">
        Login to Spin
      </router-link>
    </div>
    
    <div v-else class="spin-container">
      <!-- Wheel -->
      <div class="wheel-wrapper">
        <div class="wheel-pointer"></div>
        <div 
          class="wheel" 
          :style="{ transform: `rotate(${rotation}deg)` }"
          :class="{ spinning: spinning }"
        >
          <!-- Wheel segments using SVG for proper pie slices -->
          <svg viewBox="0 0 100 100" class="wheel-svg">
            <g v-for="(segment, index) in segments" :key="index">
              <path
                :d="getSegmentPath(index)"
                :fill="segment.color"
                stroke="#fff"
                stroke-width="0.5"
              />
              <text
                :x="getLabelPosition(index).x"
                :y="getLabelPosition(index).y"
                :transform="`rotate(${index * segmentAngle + segmentAngle / 2}, ${getLabelPosition(index).x}, ${getLabelPosition(index).y})`"
                text-anchor="middle"
                dominant-baseline="middle"
                class="segment-text"
              >
                {{ segment.label }}
              </text>
            </g>
            <!-- Center circle -->
            <circle cx="50" cy="50" r="12" fill="#333" stroke="#fff" stroke-width="2"/>
            <circle cx="50" cy="50" r="8" fill="#2874f0"/>
          </svg>
        </div>
      </div>
      
      <!-- Spins Remaining Badge -->
      <div class="spins-badge" v-if="user">
        <span class="spins-count">{{ spinsRemaining }}</span>
        <span class="spins-label">spins remaining today</span>
      </div>
      
      <!-- Spin Button / Result -->
      <div class="spin-actions">
        <div v-if="reward" class="reward-result">
          <div v-if="reward.prize_type === 'mystery'" class="reward-won mystery-reward">
            <div class="reward-icon">🎁</div>
            <h2>Mystery Prize!</h2>
            <p>You discovered something special!</p>
            <div class="mystery-flag">{{ reward.mystery_flag }}</div>
            <p class="mystery-hint">This is your secret reward!</p>
          </div>
          
          <div v-else-if="reward.prize_type === 'wallet_cash'" class="reward-won">
            <div class="reward-icon">💰</div>
            <h2>Congratulations!</h2>
            <p>You won <strong>₹{{ reward.prize_value }}</strong> in your wallet!</p>
            <p class="wallet-balance">
              New Balance: ₹{{ user?.wallet_balance?.toLocaleString('en-IN') || '...' }}
            </p>
          </div>
          
          <div v-else-if="reward.prize_type === 'coupon'" class="reward-won">
            <div class="reward-icon">🎟️</div>
            <h2>Congratulations!</h2>
            <p>You won a coupon code!</p>
            <div class="coupon-code">{{ reward.coupon_code }}</div>
            <p class="coupon-hint">Use this code at checkout for discounts</p>
          </div>
          
          <div v-else class="reward-none">
            <div class="reward-icon">😊</div>
            <h2>Better Luck Next Time!</h2>
            <p>You didn't win this time, but don't worry!</p>
          </div>
          
          <div class="reward-actions">
            <button v-if="spinsRemaining > 0" @click="spinAgain" class="btn btn-spin">
              Spin Again ({{ spinsRemaining }} left)
            </button>
            <button @click="goToProducts" class="btn btn-secondary">
              Continue Shopping
            </button>
          </div>
        </div>
        
        <div v-else-if="spinsRemaining <= 0" class="no-spins">
          <p>You've used all your spins for today!</p>
          <p class="hint">Come back tomorrow for 5 more spins.</p>
          <button @click="goToProducts" class="btn btn-primary">
            Continue Shopping
          </button>
        </div>
        
        <button 
          v-else
          @click="spinWheel" 
          class="btn btn-spin"
          :disabled="spinning"
        >
          {{ spinning ? 'Spinning...' : 'SPIN NOW!' }}
        </button>
        
        <p v-if="error && user" class="error">{{ error }}</p>
      </div>
      
      <!-- Rules -->
      <div class="rules card">
        <h3>Rules</h3>
        <ul>
          <li>Each user can spin the wheel up to 5 times per day</li>
          <li>Spins reset at midnight every day</li>
          <li>Wallet rewards are credited instantly</li>
          <li>Coupons can be used at checkout</li>
          <li>Rewards cannot be transferred or exchanged</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.spin-page {
  max-width: 600px;
  margin: 0 auto;
  padding: 1rem;
}

.spin-header {
  text-align: center;
  margin-bottom: 2rem;
}

.spin-header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.spin-header p {
  color: #666;
}

.loading, .auth-required {
  text-align: center;
  padding: 3rem;
}

.auth-required p {
  margin-bottom: 1rem;
  color: #666;
}

.spin-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.wheel-wrapper {
  position: relative;
  width: 320px;
  height: 320px;
}

.wheel-pointer {
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 20px solid transparent;
  border-right: 20px solid transparent;
  border-top: 35px solid #2874f0;
  z-index: 10;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}

.wheel {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  position: relative;
  box-shadow: 0 0 30px rgba(0,0,0,0.3);
  border: 8px solid #333;
  transition: transform 5s cubic-bezier(0.17, 0.67, 0.12, 0.99);
  background: #fff;
}

.wheel.spinning {
  animation: pulse 0.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 30px rgba(0,0,0,0.3), 0 0 60px rgba(40, 116, 240, 0.5); }
  50% { box-shadow: 0 0 50px rgba(0,0,0,0.4), 0 0 80px rgba(40, 116, 240, 0.7); }
}

.wheel-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.segment-text {
  font-size: 5px;
  font-weight: 700;
  fill: #333;
  text-shadow: 0 0 2px rgba(255,255,255,0.8);
  pointer-events: none;
}

.spin-actions {
  text-align: center;
}

.btn-spin {
  padding: 1rem 3rem;
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-spin:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.btn-spin:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.reward-result {
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.reward-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.reward-result h2 {
  margin-bottom: 0.5rem;
  color: #333;
}

.reward-result p {
  color: #666;
  margin-bottom: 0.5rem;
}

.wallet-balance {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2874f0;
  margin-top: 0.75rem;
}

.coupon-code {
  background: #f0f4ff;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-family: monospace;
  font-size: 1.2rem;
  font-weight: 700;
  color: #2874f0;
  border: 2px dashed #2874f0;
  margin: 1rem 0;
}

.coupon-hint {
  font-size: 0.85rem;
  color: #999;
}

.mystery-reward {
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  color: white;
  border-radius: 12px;
  padding: 1.5rem;
}

.mystery-reward h2 {
  color: white;
}

.mystery-reward p {
  color: rgba(255, 255, 255, 0.9);
}

.mystery-flag {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-family: monospace;
  font-size: 1rem;
  font-weight: 700;
  color: #fff;
  border: 2px dashed rgba(255, 255, 255, 0.5);
  margin: 1rem 0;
  word-break: break-all;
}

.mystery-hint {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
}

.reward-none {
  padding: 1rem 0;
}

.spins-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.spins-count {
  font-size: 1.5rem;
  font-weight: 700;
}

.spins-label {
  font-size: 0.75rem;
  opacity: 0.9;
}

.no-spins {
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  text-align: center;
}

.no-spins p {
  margin-bottom: 0.5rem;
}

.no-spins .hint {
  color: #999;
  font-size: 0.9rem;
}

.reward-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  background: #f0f0f0;
  color: #333;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.reward-result .btn {
  margin-top: 0;
}

.error {
  color: #e53e3e;
  margin-top: 1rem;
  padding: 0.5rem;
  background: #fee;
  border-radius: 4px;
}

.rules {
  width: 100%;
  padding: 1.5rem;
  margin-top: 1rem;
}

.rules h3 {
  margin-bottom: 1rem;
  font-size: 1rem;
}

.rules ul {
  margin: 0;
  padding-left: 1.25rem;
}

.rules li {
  margin-bottom: 0.5rem;
  color: #666;
  font-size: 0.9rem;
}
</style>
