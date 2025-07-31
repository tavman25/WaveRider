FROM python:3.9-slim

# Install SNMP tools
RUN apt-get update && apt-get install -y snmp snmp-mibs-downloader && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

# Use Flask development server with proper environment variables
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
