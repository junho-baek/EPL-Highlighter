# **스포츠 하이라이터 프로젝트**

## **프로젝트 개요**

유튜브 실시간 스트리밍 데이터를 기반으로 실시간 반응을 수집하고 분석하여 하이라이트 구간을 탐지하고 요약 정보를 제공하는 시스템.

---

## **구현 항목**

### **Backend (BE)**

1. **유튜브 스트리밍 영상 검색 및 ID 추출 (Selenium)**

   - Selenium을 사용해 유튜브에서 경기와 관련된 실시간 스트리밍 채널 ID를 검색하고 추출.

2. **실시간 반응 데이터 수집 요청 (pytchat)**

   - pytchat 라이브러리를 활용해 유튜브 실시간 스트리밍의 채팅 데이터를 수집.

3. **분석 요청 및 결과 저장**

   - 수집된 데이터를 기반으로 감정 분석 및 키워드 추출 진행.
   - 분석 결과를 PostgreSQL 또는 MongoDB에 저장하여 하이라이트 데이터를 관리.

4. **에러 핸들링 및 로깅** (선택)

   - 작업 중 발생 가능한 오류를 처리하고 모든 작업을 로깅.

5. **API 문서화** (선택)
   - FastAPI의 Swagger/OpenAPI 기능을 활용하여 API 문서화 제공.

---

### **Frontend (FE)**

1. **경기 탐색 페이지**

   - 오늘/내일 경기를 필터링하여 일정 목록 제공.
   - 각 경기의 시간 및 상태(LIVE 여부) 버튼 표시.

2. **반응 확인 페이지**

   - 실시간 반응 데이터를 그래프로 시각화.
   - 키워드 클라우드 및 감정 점수를 추가로 표시.

3. **분석 확인 페이지**

   - 탐지된 하이라이트 구간별 분석 결과 제공.
   - 분석 데이터를 JSON 또는 CSV로 다운로드 가능.(선택)

4. **실시간 상태 표시** (선택)

   - 작업 상태(데이터 수집 중, 분석 중, 완료)를 실시간으로 업데이트.

5. **다크 모드 및 모바일 최적화** (선택)
   - 사용자 경험을 향상시키기 위해 다크 모드와 반응형 UI 제공.

---

## **기술 스택**

### **Backend**

- **Framework**: FastAPI
- **Web Scraping**: Selenium
- **Chat Collection**: pytchat
- **Database**: PostgreSQL / MongoDB
- **Task Scheduling**: Celery (선택사항)
- **Logging & Error Tracking**: Python Logging, Sentry

### **Frontend**

- **Framework**: React
- **CSS**: TailwindCSS
- **Charting**: Recharts, D3.js
- **State Management**: React Context API / Redux (선택사항)

### **DevOps**

- **Containerization**: Docker
- **Deployment**: AWS EC2, AWS RDS, S3
- **Version Control**: Git, GitHub

---
