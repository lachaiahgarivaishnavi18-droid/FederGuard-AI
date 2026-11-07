FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend /app/backend
COPY bank_clients /app/bank_clients
RUN useradd --create-home bank && mkdir /app/local && chown bank:bank /app/local
USER bank
ENV BANK_DATA_DIR=/app/local
EXPOSE 8100
CMD ["uvicorn", "bank_clients.node:app", "--host", "0.0.0.0", "--port", "8100"]
