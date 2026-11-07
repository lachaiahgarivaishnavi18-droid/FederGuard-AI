FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend /app/backend
COPY bank_clients /app/bank_clients
RUN useradd --create-home coordinator && mkdir /app/runtime && chown coordinator:coordinator /app/runtime
USER coordinator
CMD ["python", "-m", "backend.federated.flower", "server"]
