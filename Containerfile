FROM python:3.12.0-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
	pip install -r requirements.txt

COPY . .
CMD ["python", "batch_process.py"]
