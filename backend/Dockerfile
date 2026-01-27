# ResMatch Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF and LaTeX (for RenderCV)
RUN apt-get update && apt-get install -y \
    build-essential \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p output

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
