import os
import multiprocessing

os.makedirs("logs", exist_ok=True)

preload_app = False # set to false because causes artifacts on background removal
bind = "0.0.0.0:8000"
workers = 1 #multiprocessing.cpu_count() * 2 + 1
errorlog = os.path.join(os.path.dirname(__file__), "logs", "gunicorn_error.log")
accesslog = os.path.join(os.path.dirname(__file__), "logs", "gunicorn_access.log")
loglevel = "info"