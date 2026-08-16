FROM python:3.11-slim

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/export.py .

ENV OUTPUT_DIR=/data
ENV EXPORT_TABLE=shipments

CMD ["python", "export.py"]
