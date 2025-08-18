import logging
import os
import threading
import time

import pytest

from raven.utils.kafka_client import KafkaClient
from raven.utils.schemas import Message

timewait = 1
kafka_bootstrap_servers = os.getenv("kafka_bootstrap_servers", "localhost:9092")
topic = "pt_events"
partition = 5
message: Message = {
    "src": "user",
    "dst": "assistant",
    "task": {"content": "This is a test.", "host": "None", "intent": "None"},
    "data": "None",
    "state": "doing",
}


class TestKafka:
    @pytest.mark.kafka
    def test_message_send_and_receive(self, setup_consumer: None, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO)

        self.send()
        time.sleep(timewait)

        expectation = [
            f"Received message [{message['task']}] from partition [{partition}] of topic [{topic}]",
            f"[{message['dst']}] receives a message from [{message['src']}]: success",
            f"Sent message [{message['task']}] to partition [{partition}] of topic [{topic}]",
            f"[{message['src']}] sents a message to [{message['dst']}]: success",
        ]

        # received = all(any(expect in record.message for record in caplog.records) for expect in expectation)
        # assert received, "Log output not as expected"

        # missing = [expect for expect in expectation if not any(expect in record.message for record in caplog.records)]
        # assert not missing, f"Missing expected log messages: {missing}"

        log_text = "\n".join(record.message for record in caplog.records)
        missing = [expect for expect in expectation if expect not in log_text]
        assert not missing, f"Missing expected log messages: {missing}"

    @pytest.fixture(scope="module")
    def setup_consumer(self) -> None:
        threading.Thread(target=self.receive, daemon=True).start()
        time.sleep(timewait)

    def send(self) -> None:
        mq = KafkaClient(kafka_bootstrap_servers)
        mq.send(message, topic, partition)

    def receive(self) -> None:
        mq = KafkaClient(kafka_bootstrap_servers)
        mq.receive(topic, partition)
