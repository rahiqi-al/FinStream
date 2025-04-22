from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
import json
import logging
import websocket
from config.config import config

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename="/project/log/app.log", filemode='a')
logger = logging.getLogger(__name__)

def report(err, msg):
    if err is not None:
        logger.error(f'Message failed from the producer: {err}')
    else:
        logger.info(f'Message delivered to: topic = {msg.topic()} & partition = {msg.partition()}')

def on_message(ws, message):
    try:
        logger.info(f'Received WebSocket message: {message}')
        producer.produce(config.topic_name, value=message, callback=report)
        producer.flush()
    except Exception as e:
        logger.error(f'Error producing message to Kafka: {e}')

def on_error(ws, error):
    logger.error(f'WebSocket error: {error}')

def on_close(ws, close_status_code, close_msg):
    logger.info(f'WebSocket closed: {close_status_code}, {close_msg}')

def on_open(ws):
    logger.info('WebSocket connection opened')
    ws.send('{"type":"subscribe","symbol":"AAPL"}')
    ws.send('{"type":"subscribe","symbol":"AMZN"}')
    ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')
    ws.send('{"type":"subscribe","symbol":"IC MARKETS:1"}')

def producer():
    global producer
    try:
        # Create Kafka topic if it doesn't exist
        admin = AdminClient(config.producer_config)
        if config.topic_name not in admin.list_topics().topics:
            topic = NewTopic(config.topic_name, num_partitions=1, replication_factor=1)
            admin.create_topics([topic])
            logger.info(f'Topic created: {config.topic_name}')
        else:
            logger.info(f'Topic already exists: {config.topic_name}')

        # Initialize Kafka producer
        producer = Producer(config.producer_config)

        # Start WebSocket connection
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            f"wss://ws.finnhub.io?token={config.finnhub_token}",
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.on_open = on_open
        ws.run_forever()  # Runs indefinitely, keeping container alive

    except Exception as e:
        logger.exception('Producer error')

producer()