FROM python:3.8-slim

WORKDIR /app

COPY msg_monitor.py reddit_response.py requirements.txt /app/

COPY start.sh /start.sh

RUN chmod +x /start.sh

RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

CMD ["/start.sh"]