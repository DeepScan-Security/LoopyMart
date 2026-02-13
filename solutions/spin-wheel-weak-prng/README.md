# Spin Wheel Weak PRNG Challenge

## Challenge Description

The Spin the Wheel feature on the e-commerce site uses a predictable random number generator. By exploiting this weakness, you can predict when the Mystery Prize will be awarded and win the CTF flag.

## Spin Limit

Users can spin the wheel **5 times per day** (resets at midnight). This gives you multiple attempts to hit the mystery prize at the right moment.

## Vulnerability

The backend uses Python's `random` module seeded with the current Unix timestamp in seconds:

```python
import time
import random

random.seed(int(time.time()))
rand = random.random()
```

This is a **Weak PRNG** vulnerability because:
1. The seed is predictable - it's just the current Unix timestamp
2. Python's Mersenne Twister PRNG is deterministic given the same seed
3. An attacker can predict the exact random value that will be generated

## Prize Distribution

- **Mystery Prize (Flag)**: `rand < 0.1` (10% chance)
- **Wallet Cash**: `0.1 <= rand < 0.45` (35% chance)
- **Coupon**: `0.45 <= rand < 0.7` (25% chance)
- **No Reward**: `rand >= 0.7` (30% chance)

## Exploitation

1. Get the current Unix timestamp
2. Seed Python's random with the same timestamp
3. Call `random.random()` to predict the server's value
4. If the value is < 0.1, the Mystery Prize will be won
5. If not, calculate the next winning timestamp and wait
6. With 5 spins per day, you can wait for up to 5 winning timestamps

## Solution

Run the `solve.py` script to find the next timestamp where the Mystery Prize will be awarded:

```bash
python solve.py
```

The script will:
1. Search upcoming timestamps for a winning moment
2. Display countdown to the optimal spin time
3. Automatically detect when to click SPIN

## Manual Exploitation

```python
import time
import random

# Check if current timestamp wins mystery prize
timestamp = int(time.time())
random.seed(timestamp)
value = random.random()

if value < 0.1:
    print(f"SPIN NOW! Timestamp {timestamp} wins mystery prize!")
else:
    print(f"Value: {value} - won't win mystery prize")
```

## Flag

Successfully exploiting this vulnerability awards the flag:
```
CTF{w34k_prng_pr3d1ct4bl3_sp1n}
```

## Mitigation

To fix this vulnerability:
1. Use `secrets` module instead of `random` for security-sensitive operations
2. Never seed random with predictable values
3. Use cryptographically secure random number generators (CSPRNG)

```python
import secrets

# Secure alternative
rand = secrets.randbelow(100) / 100  # Cryptographically secure
```
