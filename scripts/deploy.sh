#!/bin/bash
set -e

IMAGE_TAG=$1

if [ -z "$IMAGE_TAG" ]; then
  echo "사용법: deploy.sh <image_tag>"
  exit 1
fi

echo "===== Blue-Green 배포 시작: $IMAGE_TAG ====="

cd /home/ubuntu

export DEPLOY_IMAGE="$IMAGE_TAG"

# 첫 배포 여부 확인
FIRST_DEPLOY=false
if ! docker compose --profile blue --profile green ps --format '{{.Name}}' 2>/dev/null | grep -q "fastapi"; then
  FIRST_DEPLOY=true
fi

# 현재 활성 컨테이너 확인 (blue or green)
if [ "$FIRST_DEPLOY" = true ]; then
  CURRENT="blue"
  TARGET="blue"
  echo "첫 배포 감지 → blue로 시작"
elif docker compose --profile green ps --format '{{.Name}}' 2>/dev/null | grep -q "fastapi-green"; then
  CURRENT="green"
  TARGET="blue"
else
  CURRENT="blue"
  TARGET="green"
fi

echo "현재 활성: $CURRENT → 전환 대상: $TARGET"

# 현재 이미지 백업 (롤백용)
echo "$IMAGE_TAG" > /home/ubuntu/.current_image
if [ "$FIRST_DEPLOY" = false ]; then
  if docker compose --profile "$CURRENT" ps -q "fastapi-$CURRENT" 2>/dev/null | head -1 | xargs -r docker inspect --format='{{.Config.Image}}' 2>/dev/null > /home/ubuntu/.previous_image; then
    echo "이전 이미지 백업 완료"
  fi
fi
echo "$CURRENT" > /home/ubuntu/.previous_slot

# 새 이미지 pull
echo "이미지 다운로드 중..."
docker pull "$IMAGE_TAG"

# 타겟 컨테이너 시작
if [ "$FIRST_DEPLOY" = true ]; then
  echo "첫 배포 - fastapi-blue + redis 시작 중..."
  sed -i "s|server fastapi-.*:8000;|server fastapi-blue:8000;|" /home/ubuntu/nginx/nginx.conf
  docker compose --profile blue up -d fastapi-blue
else
  echo "$TARGET 컨테이너 시작 중..."
  docker compose --profile "$TARGET" up -d "fastapi-$TARGET"
fi

# 헬스체크 (최대 180초)
echo "헬스체크 대기 중..."
HEALTH_OK=false
for i in $(seq 1 36); do
  if docker compose --profile "$TARGET" exec "fastapi-$TARGET" curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "$TARGET 헬스체크 통과"
    HEALTH_OK=true
    break
  fi
  echo "헬스체크 대기... ($i/36)"
  sleep 5
done

if [ "$HEALTH_OK" = false ]; then
  echo "헬스체크 실패 - $TARGET 컨테이너 제거"
  docker compose --profile "$TARGET" logs "fastapi-$TARGET" 2>&1 | tail -50
  docker compose --profile "$TARGET" stop "fastapi-$TARGET" 2>/dev/null || true
  docker compose --profile "$TARGET" rm -f "fastapi-$TARGET" 2>/dev/null || true
  if [ "$FIRST_DEPLOY" = true ]; then
    docker compose --profile blue down 2>/dev/null || true
  fi
  exit 1
fi

# 헬스체크 통과 후 처리
if [ "$FIRST_DEPLOY" = true ]; then
  # 첫 배포: nginx도 시작
  echo "nginx 시작 중..."
  docker compose --profile blue up -d nginx
else
  # nginx upstream을 타겟으로 전환
  sed -i "s|server fastapi-.*:8000;|server fastapi-$TARGET:8000;|" /home/ubuntu/nginx/nginx.conf
  docker compose --profile "$TARGET" exec nginx nginx -s reload

  echo "트래픽 전환 완료: $CURRENT → $TARGET"

  # 이전 컨테이너 종료
  sleep 3
  docker compose --profile "$CURRENT" stop "fastapi-$CURRENT" 2>/dev/null || true
  docker compose --profile "$CURRENT" rm -f "fastapi-$CURRENT" 2>/dev/null || true
fi

# 미사용 이미지 정리
docker image prune -f

echo "===== 배포 완료 ====="
exit 0
