FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard ./dashboard
COPY data ./data

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/streamlit_app.py", "--server.address=0.0.0.0"]
