#!/bin/bash

# EC2 인스턴스 정보
EC2_HOST="43.201.56.15"
EC2_USER="ec2-user"
KEY_PATH="/Users/gimjinhyeon/.ssh/mindforest-key.pem"
PROJECT_NAME="mindforest-backend"

echo "🚀 MindForest Backend 배포 시작..."

# 1. 프로젝트 압축
echo "📦 프로젝트 압축 중..."
tar -czf /tmp/${PROJECT_NAME}.tar.gz \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    .

# 2. 파일 전송
echo "📤 서버로 파일 전송 중..."
scp -i ${KEY_PATH} -o StrictHostKeyChecking=no /tmp/${PROJECT_NAME}.tar.gz ${EC2_USER}@${EC2_HOST}:/tmp/

# 3. 서버 설정 스크립트 생성
cat > /tmp/setup_server.sh << 'EOF'
#!/bin/bash

# 시스템 업데이트
sudo yum update -y

# Python 및 필요 패키지 설치
sudo yum install -y python3 python3-pip nginx postgresql15

# 프로젝트 디렉토리 생성
sudo mkdir -p /opt/mindforest-backend
cd /opt/mindforest-backend

# 압축 해제
sudo tar -xzf /tmp/mindforest-backend.tar.gz

# 가상환경 생성 및 활성화
sudo python3 -m venv venv
source venv/bin/activate

# 의존성 설치
sudo venv/bin/pip install --upgrade pip
sudo venv/bin/pip install -r requirements.txt

# 권한 설정
sudo chown -R ec2-user:ec2-user /opt/mindforest-backend

# Systemd 서비스 파일 생성
sudo tee /etc/systemd/system/mindforest-backend.service > /dev/null << 'SERVICE'
[Unit]
Description=MindForest Backend FastAPI
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/mindforest-backend
Environment="PATH=/opt/mindforest-backend/venv/bin"
ExecStart=/opt/mindforest-backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Nginx 설정
sudo tee /etc/nginx/sites-available/mindforest-backend > /dev/null << 'NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

# Nginx 설정 활성화
sudo ln -sf /etc/nginx/sites-available/mindforest-backend /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable mindforest-backend
sudo systemctl restart mindforest-backend

# 상태 확인
sleep 5
sudo systemctl status mindforest-backend --no-pager

echo "✅ 배포 완료!"
echo "🌐 서버 접속: http://${EC2_HOST}/"
echo "📊 API 문서: http://${EC2_HOST}/docs"
EOF

# 4. 설정 스크립트 전송 및 실행
echo "⚙️ 서버 설정 중..."
scp -i ${KEY_PATH} -o StrictHostKeyChecking=no /tmp/setup_server.sh ${EC2_USER}@${EC2_HOST}:/tmp/
ssh -i ${KEY_PATH} -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} "chmod +x /tmp/setup_server.sh && /tmp/setup_server.sh"

# 5. 임시 파일 삭제
rm -f /tmp/${PROJECT_NAME}.tar.gz
rm -f /tmp/setup_server.sh

echo "🎉 MindForest Backend 배포 완료!"
echo "접속 URL: http://${EC2_HOST}"