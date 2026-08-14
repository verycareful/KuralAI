FROM python:3.12-slim

# Install system dependencies (ffmpeg required by pydub)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create output directory
RUN mkdir -p output

# Expose port (7860 for Hugging Face Spaces, or dynamic $PORT on Render)
EXPOSE 7860
ENV PORT=7860

# Run Flask server
CMD ["python", "app.py"]
