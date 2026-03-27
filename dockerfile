FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY . /app
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080"]