FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt .

# ✅ Fix: Use --only-binary flag
RUN pip install --no-cache-dir \
    --only-binary :all: \
    Flask==3.0.0 \
    Werkzeug==3.0.1 \
    flake8==6.1.0 \
    pytest==7.4.0 || \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
