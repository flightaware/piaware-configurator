# Gunicorn configuration file

# bind - what ports/sockets to listen on
bind = '127.0.0.1:5000'

# loglevel - "debug", "info", "warning", "error", "critical"
loglevel = 'info'

# Number of worker processes
workers = 2

# Worker timeout (seconds)
timeout = 120
