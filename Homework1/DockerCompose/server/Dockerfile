# Dockerfile per il server
FROM python:3.9

WORKDIR /app
COPY ./server.py /app/
COPY ./service_pb2.py /app/
COPY ./service_pb2_grpc.py /app/
COPY ./CQRS_Pattern /app/CQRS_Pattern/

COPY ./requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt






CMD ["python", "server.py"]
