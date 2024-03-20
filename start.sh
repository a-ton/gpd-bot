#!/bin/bash


exec /usr/local/bin/python3 -u /app/msg_monitor.py &
exec /usr/local/bin/python3 -u /app/reddit_response.py &

echo "The bot is now running"

sleep infinity