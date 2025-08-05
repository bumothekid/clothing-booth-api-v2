import os
import multiprocessing

bind = "0.0.0.0:8000"
workers = 1 #multiprocessing.cpu_count() * 2 + 1
errorlog = os.path.join(os.path.dirname(__file__), "logs", "gunicorn_error.log")
accesslog = os.path.join(os.path.dirname(__file__), "logs", "gunicorn_access.log")
loglevel = "info"