FROM python:3.13-slim

# Install system dependencies (if needed by aiortc or audio tools)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavdevice-dev \
    libavfilter-dev \
    libopus-dev \
    libvpx-dev \
    libx264-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run the assistant
# CMD ["python", "agent.py"]
CMD ["python", "agent.py", "start"]
