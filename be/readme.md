# 구현한 것
- kafka
   - docker로 kafka 띄움
   - localhost:19092로 접근하면 됨
- producer
   - naver, youtube 반응 크롤링 구현
   - naver, youtube 반응 모두 ChatModel 모델 형태로 통일해서 produce
   - 임시로 각각의 producer file 의 마지막 부분에 실행 가능한 코드 첨부. video_id, page_id 변경해서 실행가능 
- consumer
   - 테스트 용도로 구현함

# 실행법
```
cd be
docker compose up -d
pipenv run python producer/naver_chat_producer.py
pipenv run python producer/youtube_chat_producer.py
pipenv run python producer/chat_consumer.py

작동하는 것 확인 후..

docker compose down -v
```

