# AWS EC2 + Docker 배포 안내

대상 EC2 Public IPv4: `3.34.185.174`

> 일반 Public IPv4는 EC2 중지 후 다시 시작하면 변경될 수 있습니다. 주소를 고정하려면 Elastic IP를 연결하세요.

배포 후 접속 주소:

- React: `http://3.34.185.174`
- Swagger: `http://3.34.185.174/docs`
- Health Check: `http://3.34.185.174/healthz`

## 1. EC2 보안 그룹

다음 인바운드 규칙을 설정합니다.

| 포트 | 소스 | 용도 |
|---:|---|---|
| 22 | 내 IP | SSH |
| 80 | `0.0.0.0/0` | 웹 서비스 |

`3306`, `8000`, `5173`은 외부에 개방하지 않습니다.

## 2. SSH 접속

```bash
chmod 400 smart-bicycle-service.pem
ssh -i smart-bicycle-service.pem ubuntu@3.34.185.174
```

Amazon Linux를 사용했다면 계정은 `ec2-user`입니다.

## 3. 프로젝트와 서비스 파일 준비

Git으로 소스 코드를 받은 후, Git에서 제외된 다음 파일은 별도로 EC2에 복사해야 합니다.

```text
server/models/artifacts/demand_model.joblib
server/models/artifacts/inference_features.csv
server/data/usage/*.csv
server/data/external/weather_hourly.csv
```

`server/data3`와 `server/data/ml_processed`는 운영 추론에 필요하지 않습니다.

예시:

```bash
scp -i smart-bicycle-service.pem -r server/models/artifacts ubuntu@3.34.185.174:~/smart-bicycle-service/server/models/
scp -i smart-bicycle-service.pem -r server/data/usage ubuntu@3.34.185.174:~/smart-bicycle-service/server/data/
scp -i smart-bicycle-service.pem -r server/data/external ubuntu@3.34.185.174:~/smart-bicycle-service/server/data/
```

## 4. Docker 설치 확인

EC2에 Docker Engine과 Compose Plugin을 설치한 뒤 다음 명령이 모두 성공하는지 확인합니다.

```bash
docker --version
docker compose version
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

그룹 적용을 위해 SSH 연결을 종료한 뒤 다시 접속합니다.

## 5. 운영 환경변수

EC2 프로젝트 루트에서 다음을 실행합니다.

```bash
cp .env.ec2.example .env
nano .env
```

`.env`의 DB 비밀번호, JWT Secret, 서울시·기상청·OpenAI API Key를 실제 값으로 변경합니다.

## 6. Docker Compose 실행

```bash
docker compose config
docker compose up --build -d
docker compose ps
```

로그 확인:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mysql
```

## 7. 업데이트

```bash
git pull
docker compose up --build -d
docker image prune -f
```

## 8. 종료와 데이터 주의사항

컨테이너만 종료:

```bash
docker compose down
```

MySQL 데이터는 `mysql_data` 볼륨에 유지됩니다. 다음 명령은 DB 볼륨까지 삭제하므로 사용하지 않습니다.

```bash
docker compose down -v
```

로컬 PC의 기존 `fastapi_db`와 Docker MySQL은 서로 다른 DB입니다. 기존 회원 데이터를 옮기려면 로컬 DB를 `mysqldump`로 백업하고 EC2 MySQL 컨테이너에 별도로 복원해야 합니다. 옮기지 않아도 `bike_member` 테이블 자체는 FastAPI 시작 시 자동 생성됩니다.

## 9. HTTPS 적용 전 주의사항

현재 설정은 공인 IP 기반 HTTP입니다. 따라서 `REFRESH_COOKIE_SECURE=false`를 사용합니다.
도메인과 HTTPS를 적용한 뒤에는 `REFRESH_COOKIE_SECURE=true`로 변경해야 합니다.
