FROM python:3.13-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy application code
COPY . /app

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

ENV PYTHONPATH=/app/src

# Copy start script and make it executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
