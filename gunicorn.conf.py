"""Loaded automatically by Gunicorn from the repository root on Render."""

# Keep one process on the free instance, but allow concurrent I/O-bound requests.
workers = 1
worker_class = "gthread"
threads = 4
timeout = 30
