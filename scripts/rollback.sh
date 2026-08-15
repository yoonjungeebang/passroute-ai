#!/bin/bash
set -e

PREVIOUS_IMAGE_FILE="/home/ubuntu/.previous_image"
PREVIOUS_SLOT_FILE="/home/ubuntu/.previous_slot"

if [ ! -f "$PREVIOUS_IMAGE_FILE" ] || [ ! -f "$PREVIOUS_SLOT_FILE" ]; then
  echo "롤백 불가: 이전 배포 정보 없음"
  exit 1
fi

PREVIOUS_IMAGE=$(cat "$PREVIOUS_IMAGE_FILE")
PREVIOUS_SLOT=$(cat "$PREVIOUS_SLOT_FILE")

if [ -z "$PREVIOUS_IMAGE" ] || [ -z "$PREVIOUS_SLOT" ]; then
  echo "롤백 불가: 이전 배포 정보가 비어있음"
  exit 1
fi

echo "===== 롤백 시작: $PREVIOUS_SLOT ($PREVIOUS_IMAGE) ====="

cd /home/ubuntu

export DEPLOY_IMAGE="$PREVIOUS_IMAGE"

# 롤백 실패 시 컨테이너 자동 정리
CLEANUP_SLOT="$PREVIOUS_SLOT"
cleanup() {
  if [ -n "$CLEANUP_SLOT" ]; then
    echo "롤백 실패 → $CLEANUP_SLOT 컨테이너 정리 중..."
    docker compose --profile "$CLEANUP_SLOT" stop "fastapi-$CLEANUP_SLOT" 2>/dev/null || true
    docker compose --profile "$CLEANUP_SLOT" rm -f "fastapi-$CLEANUP_SLOT" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# 이전 슬롯 컨테이너 시작
docker compose --profile "$PREVIOUS_SLOT" up -d "fastapi-$PREVIOUS_SLOT"

# 헬스체크 (최대 120초)
echo "헬스체크 대기 중..."
for i in $(seq 1 24); do
  if docker compose --profile "$PREVIOUS_SLOT" exec "fastapi-$PREVIOUS_SLOT" python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" > /dev/null 2>&1; then
    echo "롤백 헬스체크 통과"

    # nginx upstream 전환
    sed -i "s|server fastapi-.*:8000;|server fastapi-$PREVIOUS_SLOT:8000;|" /home/ubuntu/nginx/nginx.conf
    echo "nginx 재시작 중..."
    if docker compose ps nginx --format '{{.State}}' 2>/dev/null | grep -q "running"; then
      docker compose restart nginx
    else
      docker compose up -d nginx
    fi

    # 반대쪽 실패 컨테이너 정리
    if [ "$PREVIOUS_SLOT" = "blue" ]; then OTHER="green"; else OTHER="blue"; fi
    docker compose --profile "$OTHER" stop "fastapi-$OTHER" 2>/dev/null || true
    docker compose --profile "$OTHER" rm -f "fastapi-$OTHER" 2>/dev/null || true

    CLEANUP_SLOT=""
    echo "===== 롤백 완료 ====="
    exit 0
  fi
  sleep 5
done

echo "롤백 헬스체크 실패"
docker compose --profile "$PREVIOUS_SLOT" logs "fastapi-$PREVIOUS_SLOT"
exit 1
