# Start from official Python 3.11 slim image
# slim = smaller than full Python image, has what we need
FROM python:3.11-slim

# Set working directory inside the container
# All subsequent commands run from here
WORKDIR /app

# Copy requirements first — before copying all code
# Why? Docker caches layers. If requirements haven't changed,
# Docker skips the pip install step on rebuild. Faster builds.
COPY requirements.txt .


# Install dependencies
# --no-cache-dir = don't store pip cache inside image, keeps it smaller
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the code
COPY . .

# Expose port 8000 so Docker knows this container uses it
EXPOSE 8000


# Default command when container starts
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]