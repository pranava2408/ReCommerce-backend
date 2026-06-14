# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Hugging Face Spaces run as a non-root user, so we must make sure
# the cache directories for AI models are writable.
ENV TRANSFORMERS_CACHE=/tmp/huggingface_cache
ENV HF_HOME=/tmp/huggingface_cache

# Make port 7860 available (Hugging Face Spaces default port)
EXPOSE 7860

# Run uvicorn when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
