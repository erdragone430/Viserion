FROM python:3.12-slim

WORKDIR /app
COPY assets/ /app/assets/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

WORKDIR /app/dashboard
CMD ["streamlit", "run", "dashboard.py", "--server.address=0.0.0.0"]
