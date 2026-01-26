import time
import os
import sys
import urllib.request
import urllib.error

# this is a "smart" wake-up call that respects Render's free tier limits (750 hours/month)
# and handles the "cold start" delay (which can be 50+ seconds), we will use a Hybrid Approach:
# The Waker Script (Python): A robust script with Retry Logic (Fallback).
# Standard HTTP requests often timeout during a Render cold start. This script will try, wait, and retry until the API wakes up.
# The Scheduler (GitHub Actions): Using GitHub Actions (which is free) to run this script on a specific "Business Hours" schedule.
# This ensures you don't run 24/7 and hit the usage limit.

# --- CONFIGURATION ---
# FIX: Use 'or' to handle cases where env var exists but is empty string ""
env_url = os.getenv("NEXT_PUBLIC_API_URL")
URL = (env_url or "http://127.0.0.1:8000").rstrip("/")

MAX_RETRIES = 5
RETRY_DELAY = 10  # Seconds
TIMEOUT = 60  # Render cold starts can take ~50s

def wake_up():
    print(f"⏰ Waking up API at: {URL}")

    if not URL.startswith("http"):
        print(f"❌ Error: Invalid URL '{URL}'. Must start with http:// or https://")
        sys.exit(1)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start_time = time.time()
            # Send a request with a User-Agent to mimic a real browser
            req = urllib.request.Request(
                URL,
                headers={'User-Agent': 'Sentient-Waker-Bot/1.0'}
            )

            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                duration = time.time() - start_time
                print(f"✅ Success! API is awake. (Status: {response.status}, Time: {duration:.2f}s)")
                return True

        except urllib.error.HTTPError as e:
            # OPTIMIZATION: If we get a 404, 401, or 500, the server IS awake.
            duration = time.time() - start_time
            print(f"✅ API is awake (Status: {e.code}). (Time: {duration:.2f}s)")
            return True

        except urllib.error.URLError as e:
            print(f"❌ Attempt {attempt}/{MAX_RETRIES} failed: {e.reason}")
            print(f"⏳ Waiting {RETRY_DELAY}s for cold start...")
            time.sleep(RETRY_DELAY)

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(RETRY_DELAY)

    print("💀 Failed to wake API after multiple attempts.")
    sys.exit(1)


if __name__ == "__main__":
    wake_up()
