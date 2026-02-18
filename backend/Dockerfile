# Use official TensorFlow CPU image (already has tensorflow installed)
FROM tensorflow/tensorflow:2.18.1

WORKDIR /app

# Install system libraries needed for OpenCV / DeepFace
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install remaining dependencies (EXCLUDE tensorflow)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:10000"]
