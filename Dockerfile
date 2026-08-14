# 미리 빌드된 모델 이미지 (Dockerfile.models로 빌드 후 DockerHub에 push)
ARG MODELS_IMAGE=yaejin02/passroute-ai:models
# hadolint ignore=DL3006
FROM ${MODELS_IMAGE} AS models

# 런타임 (PyTorch 미포함, 이미지 경량화)
FROM python:3.12-slim

WORKDIR /app

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ONNX 양자화 모델 + 토크나이저 복사
COPY --from=models /tmp/kr-sbert-uint8.onnx /app/models/kr-sbert-uint8.onnx
COPY --from=models /tmp/tokenizer/ /app/models/tokenizer/

# MediaPipe FaceLandmarker 모델 다운로드
RUN curl -o /app/models/face_landmarker.task \
    https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# AWS RDS SSL 인증서 다운로드
RUN curl -o /app/global-bundle.pem https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
