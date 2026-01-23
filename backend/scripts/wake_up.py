import time
import requests
import os
import sys

# a "smart" wake-up call that respects Render's free tier limits (750 hours/month)
# and handles the "cold start" delay (which can be 50+ seconds), we will use a Hybrid Approach:
# The Waker Script (Python): A robust script with Retry Logic (Fallback).
# Standard HTTP requests often timeout during a Render cold start. This script will try, wait, and retry until the API wakes up.
# The Scheduler (GitHub Actions): Using GitHub Actions (which is free) to run this script on a specific "Business Hours" schedule.
# This ensures you don't run 24/7 and hit the usage limit.

# 1. CONFIGURATION
# We can set this in GitHub Secrets, or default to a hardcoded URL for simple setups
URL = os.getenv("NEXT_PUBLIC_API_URL", "https://your-api-name.onrender.com")
MAX_RETRIES = 5
RETRY_DELAY = 10  # Seconds


def wake_up():
    print(f"⏰ Waking up API at: {URL}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 2. THE ATTEMPT
            # Render cold starts can take 50s+. We set a long timeout.
            start_time = time.time()
            response = requests.get(f"{URL}/health", timeout=60)
            duration = time.time() - start_time

            # 3. SUCCESS
            if response.status_code == 200:
                print(f"✅ Success! API is awake. (Response time: {duration:.2f}s)")
                return True
            else:
                print(f"⚠️ API returned status {response.status_code}. Retrying...")

        except requests.exceptions.RequestException as e:
            # 4. FALLBACK LOGIC
            # If the request fails (timeout/connection error), we don't give up.
            print(f"❌ Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            print(f"⏳ Waiting {RETRY_DELAY}s for fallback retry...")
            time.sleep(RETRY_DELAY)

    print("💀 Failed to wake API after multiple attempts.")
    sys.exit(1)  # Fail the GitHub Action


if __name__ == "__main__":
    wake_up()