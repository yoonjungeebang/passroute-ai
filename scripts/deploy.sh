#!/bin/bash
set -e

IMAGE_TAG=$1

if [ -z "$IMAGE_TAG" ]; then
  echo "사용법: deploy.sh <image_tag>"
  exit 1
fi

echo "===== Blue-Green 배포 시작: $IMAGE_TAG ====="

cd /home/ubuntu

# 현재 활성 컨테이너 확인 (blue or green)
if docker compose ps --format '{{.Name}}' 2>/dev/null | grep -q "fastapi-green"; then
  CURRENT="green"
  TARGET="blue"
else
  CURRENT="blue"
  TARGET="green"
fi

echo "현재 활성: $CURRENT → 전환 대상: $TARGET"

# 현재 이미지 백업 (롤백용)
echo "$IMAGE_TAG" > /home/ubuntu/.current_image
if docker compose ps -q "fastapi-$CURRENT" 2>/dev/null | head -1 | xargs -r docker inspect --format='{{.Config.Image}}' 2>/dev/null > /home/ubuntu/.previous_image; then
  echo "이전 이미지 백업 완료"
fi
echo "$CURRENT" > /home/ubuntu/.previous_slot

# docker-compose.yml에서 타겟 서비스의 이미지를 새 태그로 교체
sed -i "/fastapi-$TARGET:/,/profiles:/{s|image:.*|image: $IMAGE_TAG|}" docker-compose.yml

# 새 이미지 pull
echo "이미지 다운로드 중..."
docker pull "$IMAGE_TAG"

# 타겟 컨테이너 시작
echo "$TARGET 컨테이너 시작 중..."
docker compose --profile "$TARGET" up -d "fastapi-$TARGET"

# 헬스체크 (최대 60초)
echo "헬스체크 대기 중..."
for i in $(seq 1 12); do
  if docker compose exec "fastapi-$TARGET" curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "$TARGET 헬스체크 통과"

    # nginx upstream을 타겟으로 전환
    sed -i "s|server fastapi-.*:8000;|server fastapi-$TARGET:8000;|" /home/ubuntu/nginx/nginx.conf
    docker compose exec nginx nginx -s reload

    echo "트래픽 전환 완료: $CURRENT → $TARGET"

    # 이전 컨테이너 종료
    sleep 3
    docker compose stop "fastapi-$CURRENT" 2>/dev/null || true
    docker compose rm -f "fastapi-$CURRENT" 2>/dev/null || true

    # 미사용 이미지 정리
    docker image prune -f

    echo "===== 배포 완료 ====="
    exit 0
  fi
  echo "헬스체크 대기... ($i/12)"
  sleep 5
done

# 헬스체크 실패 시 타겟 컨테이너 제거 (기존 서비스 유지)
echo "헬스체크 실패 - $TARGET 컨테이너 제거, 기존 $CURRENT 유지"
docker compose stop "fastapi-$TARGET" 2>/dev/null || true
docker compose rm -f "fastapi-$TARGET" 2>/dev/null || true
exit 1
