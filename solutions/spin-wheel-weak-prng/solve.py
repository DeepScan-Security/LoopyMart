#!/usr/bin/env python3
"""
Spin Wheel Weak PRNG Exploit

This script exploits the weak PRNG vulnerability in the spin wheel feature.
The server seeds Python's random with the current Unix timestamp, making
the random values predictable.

Usage:
    python solve.py [--search-range SECONDS] [--api-url URL]
"""

import argparse
import random
import time
import sys

# Prize thresholds (must match server configuration)
MYSTERY_THRESHOLD = 0.1  # rand < 0.1 wins mystery prize


def predict_outcome(timestamp: int) -> tuple[float, str]:
    """
    Predict the spin outcome for a given timestamp.
    
    Args:
        timestamp: Unix timestamp in seconds
        
    Returns:
        Tuple of (random_value, prize_type)
    """
    random.seed(timestamp)
    value = random.random()
    
    if value < 0.1:
        return value, "mystery"
    elif value < 0.45:
        return value, "wallet_cash"
    elif value < 0.7:
        return value, "coupon"
    else:
        return value, "no_reward"


def find_next_mystery_timestamp(start_time: int, search_range: int = 3600) -> int | None:
    """
    Find the next timestamp that will win the mystery prize.
    
    Args:
        start_time: Starting Unix timestamp
        search_range: How many seconds to search ahead
        
    Returns:
        Winning timestamp or None if not found in range
    """
    for offset in range(search_range):
        timestamp = start_time + offset
        value, prize = predict_outcome(timestamp)
        if prize == "mystery":
            return timestamp
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Exploit weak PRNG in spin wheel to win mystery prize"
    )
    parser.add_argument(
        "--search-range",
        type=int,
        default=3600,
        help="How many seconds ahead to search (default: 3600)"
    )
    parser.add_argument(
        "--check-current",
        action="store_true",
        help="Just check if current timestamp wins"
    )
    parser.add_argument(
        "--timestamp",
        type=int,
        help="Check a specific timestamp"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Spin Wheel Weak PRNG Exploit")
    print("=" * 60)
    print()
    
    current_time = int(time.time())
    
    # Check specific timestamp
    if args.timestamp:
        value, prize = predict_outcome(args.timestamp)
        print(f"Timestamp: {args.timestamp}")
        print(f"Random value: {value:.6f}")
        print(f"Prize: {prize}")
        if prize == "mystery":
            print("\n[!] This timestamp WINS the mystery prize!")
        return
    
    # Check current timestamp
    if args.check_current:
        value, prize = predict_outcome(current_time)
        print(f"Current timestamp: {current_time}")
        print(f"Random value: {value:.6f}")
        print(f"Prize: {prize}")
        if prize == "mystery":
            print("\n[!] SPIN NOW to win the mystery prize!")
        else:
            print(f"\n[*] Current timestamp won't win mystery prize (need < {MYSTERY_THRESHOLD})")
        return
    
    # Search for next winning timestamp
    print(f"Current time: {current_time}")
    print(f"Searching next {args.search_range} seconds for mystery prize...")
    print()
    
    winning_ts = find_next_mystery_timestamp(current_time, args.search_range)
    
    if winning_ts is None:
        print(f"[!] No winning timestamp found in next {args.search_range} seconds")
        print("    Try increasing --search-range")
        return
    
    value, _ = predict_outcome(winning_ts)
    wait_seconds = winning_ts - current_time
    
    print(f"[+] Found winning timestamp!")
    print(f"    Timestamp: {winning_ts}")
    print(f"    Random value: {value:.6f} (< {MYSTERY_THRESHOLD})")
    print(f"    Wait time: {wait_seconds} seconds")
    print()
    
    # Show some nearby winning timestamps too
    print("Upcoming winning timestamps:")
    print("-" * 40)
    count = 0
    for offset in range(args.search_range):
        ts = current_time + offset
        val, prize = predict_outcome(ts)
        if prize == "mystery":
            wait = ts - current_time
            print(f"  {ts} (in {wait:>5}s) - value: {val:.6f}")
            count += 1
            if count >= 10:
                print("  ... (more available)")
                break
    print()
    
    # Interactive countdown
    print("Starting countdown to first winning timestamp...")
    print("Press Ctrl+C to exit")
    print()
    
    try:
        while True:
            now = int(time.time())
            remaining = winning_ts - now
            
            if remaining <= 0:
                print("\r" + " " * 50, end="")
                print(f"\r[!!!] SPIN NOW! Timestamp {winning_ts} is active!")
                
                # Wait for this second to pass, then find next
                time.sleep(1.5)
                winning_ts = find_next_mystery_timestamp(int(time.time()), args.search_range)
                if winning_ts is None:
                    print("[*] No more winning timestamps in search range")
                    break
                continue
            
            # Progress bar
            bar_width = 30
            progress = max(0, 1 - (remaining / wait_seconds)) if wait_seconds > 0 else 1
            filled = int(bar_width * progress)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            print(f"\r[{bar}] {remaining:>4}s until mystery prize...", end="", flush=True)
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\nExiting...")


if __name__ == "__main__":
    main()
