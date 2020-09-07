# config.py
import multiprocessing

dubug = True
loglevel = 'debug'
bind = '0.0.0.0:5000'
timeout = 120
accesslog = './log/access.log'
errorlog = './log/error.log'

workers = multiprocessing.cpu_count() * 2 + 1
