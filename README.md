# smart-bicycle-service
프로젝트 1
대여소별 미래 자전거 부족·반납 불가 예측 서비스  

#### 2026-08-11     
- React의 mock JSON 대신 FastAPI API 연동
- 서울시 실시간 API + Data 폴더의 csv 파일로 운영 대여소·대여 가능 자전거등 각종 항목 표시
    - GET /api/bike/seoul/summary → 실시간 API + 이용정보 CSV 둘 다 사용
    - GET /api/bike/seoul/stations → 실시간 API만 사용
    - GET /api/ai/bike/analysis → 이용정보 CSV 또는 생성된 JSON 캐시 사용
- 대여소명 앞 번호 제거(4자리 번호 5571, 2281 등)
- localhost:5174 CORS 문제 해결(서버가 이미 실행중이면 5173이 아니라 5174를 반환)
- 오류 발생 시 프론트에 원인 표시
- JSON 디스크 캐시로 응답시간을 약 34초에서 0.1초로 단축
![alt text](<2026-08-11 img.png>)