import json

from kafka import KafkaConsumer

# Kafka 브로커 주소
# 토픽 이름
BROKER = 'localhost:19092'
TOPIC = 'test-topic'


def consume_chat(broker_host: str, topic: str):
    # Kafka Consumer 생성
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=broker_host,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='test-group',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))  # 메시지 디코딩
    )

    # 메시지 소비
    try:
        for record in consumer:
            chat = record.value
            print(f"Sent: [{chat['time']}]-[{chat['author']}]-[{chat['message']}] to topic: {topic}")
    except KeyboardInterrupt:
        print("Consumer stopped.")
    finally:
        consumer.close()


if __name__ == '__main__':
    consume_chat(
        'localhost:19092',
        'epl'
    )
