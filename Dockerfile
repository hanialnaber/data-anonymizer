# Use official Python image
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Install the package in development mode
RUN pip install -e .

# Create samples directory and generate sample data
RUN mkdir -p /app/samples
ENV DOCKER_ENV=true
RUN python -m data_anonymizer.utils.data_generator

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Start both FastAPI and Streamlit using a shell script
RUN chmod +x ./scripts/start.sh
CMD ["./scripts/start.sh"]
