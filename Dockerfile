FROM python:3.10-slim

WORKDIR /app

# Install git for pip requirement from GitHub
RUN apt-get update && apt-get install -y git && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the entire application first
COPY . .

# Copy requirements file and install dependencies
# Note: We're installing the dependencies first, then our local package
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Set environment variables (these should be overridden at runtime)
ENV AWS_ACCESS_KEY=""
ENV AWS_SECRET_KEY=""
ENV AWS_REGION="us-east-1"

# Set the entrypoint to run.py
ENTRYPOINT ["python", "run/run.py"]

# Default command can be overridden at runtime
CMD ["--websites", "https://www.example.com"] 