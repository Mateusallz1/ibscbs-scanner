"""
gunicorn.conf.py
----------------
Gunicorn configuration for production.

Uses 1 worker with multiple threads so that threading.Lock and
threading.Semaphore work correctly for in-memory scan result storage.
"""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Single worker + threads keeps in-memory state (Lock, Semaphore) consistent.
# Scale threads as needed; switch to multiple workers only after moving
# scan result storage to Redis or database.
workers = 1
threads = int(os.environ.get("GUNICORN_THREADS", 4))

# Timeout for long-running scan requests (large archives)
timeout = 120

accesslog = "-"
errorlog = "-"
loglevel = "info"
