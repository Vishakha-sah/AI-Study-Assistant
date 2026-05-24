# Use official Python 3.12 slim image
FROM python:3.12-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies into the system python environment
RUN uv pip install --system -r requirements.txt

# Copy the backend source code into a 'backend' directory
# This maintains the package structure required for relative imports
COPY . ./backend/

# Set PYTHONPATH to the current directory
ENV PYTHONPATH=/app

# Expose the backend port
EXPOSE 8080

# Run uvicorn with the module path
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
