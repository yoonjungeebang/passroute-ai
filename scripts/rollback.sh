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

echo "===== 롤백 시작: $PREVIOUS_SLOT ($PREVIOUS_IMAGE) ====="

cd /home/ubuntu

# 이전 슬롯의 이미지 복원
sed -i "/fastapi-$PREVIOUS_SLOT:/,/profiles:/{s|image:.*|image: $PREVIOUS_IMAGE|}" docker-compose.yml

# 이전 슬롯 컨테이너 시작
docker compose --profile "$PREVIOUS_SLOT" up -d "fastapi-$PREVIOUS_SLOT"

# 헬스체크 (최대 60초)
echo "헬스체크 대기 중..."
for i in $(seq 1 12); do
  if docker compose exec "fastapi-$PREVIOUS_SLOT" curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "롤백 헬스체크 통과"

    # nginx upstream 전환
    sed -i "s|server fastapi-.*:8000;|server fastapi-$PREVIOUS_SLOT:8000;|" /home/ubuntu/nginx/nginx.conf
    docker compose exec nginx nginx -s reload

    echo "===== 롤백 완료 ====="
    exit 0
  fi
  sleep 5
done

echo "롤백 헬스체크 실패"
docker compose logs "fastapi-$PREVIOUS_SLOT"
exit 1
