# Amazon Linux 2023 배포 가이드
```
전제 조건
EC2 인스턴스 (Amazon Linux 2023)
IAM Role에 AmazonDynamoDBFullAccess (또는 최소 권한 정책) 부착
보안 그룹: 인바운드 80(HTTP), 443(HTTPS), 22(SSH) 허용
```

1. EC2 IAM Role 설정
```
EC2에 IAM Role을 붙여 액세스 키 없이 DynamoDB에 접근합니다.

IAM → 역할 생성 → EC2 → AmazonDynamoDBFullAccess 정책 연결
→ EC2 인스턴스 → 작업 → 보안 → IAM 역할 수정
.env에서 AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY는 삭제하고 FLASK_ENV=production으로 설정합니다.
```

2. 서버 초기 설정

```
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip python3.11-devel nginx git
```

3. 앱 배포

```
# 앱 디렉터리 생성
sudo mkdir -p /srv/running-coach
sudo chown ec2-user:ec2-user /srv/running-coach

# 코드 복사 (git 사용 시)
git clone <repo-url> /srv/running-coach

# 작업 디렉터리로 이동
cd /srv/running-coach

# 가상환경 생성 및 의존성 설치
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

4. 환경변수 설정

```
cat > /srv/running-coach/backend/.env << 'EOF'
FLASK_ENV=production
AWS_REGION=ap-northeast-2
BIO_EVENTS_TABLE=bio_events
HEART_RATE_TABLE=heart_rate
EOF

chmod 600 /srv/running-coach/backend/.env
python-dotenv로 .env를 로드하려면 run.py에 한 줄 추가합니다.
```

5. DynamoDB 테이블 생성

```
aws dynamodb create-table \
  --table-name bio_events \
  --attribute-definitions AttributeName=userId,AttributeType=S AttributeName=eventId,AttributeType=S \
  --key-schema AttributeName=userId,KeyType=HASH AttributeName=eventId,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region ap-northeast-2

aws dynamodb create-table \
  --table-name heart_rate \
  --attribute-definitions AttributeName=userId,AttributeType=S AttributeName=eventId,AttributeType=S \
  --key-schema AttributeName=userId,KeyType=HASH AttributeName=eventId,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region ap-northeast-2
```


6. systemd 서비스 등록

```
sudo tee /etc/systemd/system/running-coach.service << 'EOF'
[Unit]
Description=Running Coach Flask Backend
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/srv/running-coach
ExecStart=/srv/running-coach/.venv/bin/gunicorn \
    --workers 2 \
    --bind 127.0.0.1:5000 \
    --access-logfile /var/log/running-coach/access.log \
    --error-logfile /var/log/running-coach/error.log \
    run:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo mkdir -p /var/log/running-coach
sudo chown ec2-user:ec2-user /var/log/running-coach

sudo systemctl daemon-reload
sudo systemctl enable --now running-coach
sudo systemctl status running-coach
```


7. Nginx 리버스 프록시

```
sudo tee /etc/nginx/conf.d/running-coach.conf << 'EOF'
server {
    listen 80;
    server_name _;

    location /v1/ {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sudo nginx -t
sudo systemctl enable --now nginx
```

nginx 설정 충돌 확인

```
AL2023 기본 nginx 설정이 모든 요청을 가로채는 경우가 많습니다.


# 기본 서버 블록이 /v1/ 보다 우선순위를 가지는지 확인
cat /etc/nginx/nginx.conf | grep -A5 "server {"
기본 server 블록을 비활성화하고 설정을 교체합니다.


# 기존 conf.d 파일 확인
ls /etc/nginx/conf.d/

# running-coach.conf를 아래 내용으로 교체
sudo tee /etc/nginx/conf.d/running-coach.conf << 'EOF'
server {
    listen 80 default_server;
    server_name _;

    location /v1/ {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    }

    location / {
        return 404;
    }
}
EOF
nginx.conf 안에 기본 server 블록이 있다면 비활성화합니다.


# nginx.conf에서 기본 server 블록을 include 방식으로 관리하는지 확인
grep -n "include" /etc/nginx/nginx.conf

# nginx.conf의 http 블록 안에 server {} 가 직접 있다면 주석 처리
sudo vi /etc/nginx/nginx.conf
# 기존 server { ... } 블록 전체를 # 으로 주석 처리
```



8. 동작 확인

```
# 서비스 상태
sudo systemctl status running-coach

# 로컬에서 헬스체크
curl -X POST http://localhost/v1/bio/events \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-1",
    "deviceId": "Pixel 8",
    "sessionId": "session-abc",
    "events": [{
      "eventId": "hr-session-abc-1700000000",
      "sensorType": "heart_rate",
      "measuredAt": "2024-01-01T10:00:00Z",
      "value": 145,
      "unit": "bpm"
    }]
  }'
```

응답
```
{"saved": {"heart_rate": 1, "bio_events": 0}}
```

구조 요약
```
Android (health-connector)
        │  POST /v1/bio/events
        ▼
   Nginx :80
        │
        ▼
   Gunicorn :5000 (2 workers)
        │
        ▼
   Flask App
   ├── sensorType == heart_rate → DynamoDB: heart_rate_samples
   └── 그 외                   → DynamoDB: bio_events
workers 수는 (vCPU × 2) + 1 공식을 기준으로 인스턴스 타입에 맞게 조정하세요. t3.micro(1 vCPU)면 --workers 3이 적당합니다.
```