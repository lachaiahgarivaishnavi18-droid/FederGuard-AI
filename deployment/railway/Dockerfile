FROM python:3.12-slim
ARG SERVICE_KIND=backend
WORKDIR /app
COPY backend/requirements-cloud.txt /app/backend/requirements-cloud.txt
RUN pip install --no-cache-dir -r backend/requirements-cloud.txt
# Bank training needs the supported accountant and CPU-only torch, never CUDA wheels.
RUN if [ "$SERVICE_KIND" = "bank" ]; then pip install --no-cache-dir 'torch>=2.5,<3' --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir 'opacus>=1.5,<2'; fi
COPY backend /app/backend
COPY bank_clients /app/bank_clients
COPY scripts/cloud_service.py /app/scripts/cloud_service.py
RUN useradd --uid 10001 --create-home service && mkdir /data && chown service:service /data
ENV SERVICE_KIND=$SERVICE_KIND
EXPOSE 8000
CMD ["python", "/app/scripts/cloud_service.py"]
