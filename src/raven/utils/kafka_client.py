import json
import logging
from typing import Optional
import uuid

from kafka import KafkaConsumer, KafkaProducer, TopicPartition

from ..utils import setup_logger
from .schemas import Message

logger = setup_logger(name=__name__)

logging.getLogger("kafka").setLevel(logging.WARNING)


class KafkaClient:
    """Initialize a message queue for agent communication."""

    def __init__(self, kafka_bootstrap_servers: str, group_id: Optional[str] = None, offset: str = "latest") -> None:
        """Init a Producer and Consumer

        Args:
            kafka_bootstrap_servers (str): 'host[:port]' string that the consumer and producer should contact to bootstrap initial cluster metadata.
            group_id (Optional[str], optional): The name of the consumer group to join for dynamic partition assignment (if enabled), \
                and to use for fetching and committing offsets. \
                If None, auto-partition assignment (via group coordinator) and offset commits are disabled. Default to None.
            offset (str, optional): A policy for resetting offsets on OffsetOutOfRange errors: \
                'earliest' will move to the oldest available message, 'latest' will move to the most recent. \
                Any other value will raise the exception. Defaults to "latest".
        """
        self.consumer = KafkaConsumer(
            bootstrap_servers=kafka_bootstrap_servers,
            key_deserializer=lambda k: k.decode("utf-8"),
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id=group_id,
            auto_offset_reset=offset,
        )

        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            key_serializer=lambda k: k.encode("utf-8"),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def receive(self, topic: str = "events", partition: int = 0, identifier: Optional[str] = None) -> Optional[Message]:
        """Receive messages from specific topic and partition

        Args:
            topic (str, optional): Topic for consumer to consume. Defaults to 'events'.
            partition (int, optional): Partition for consumer to consume. Defaults to 0.
            identifier (Optional[str], optional): Target consumer identifier, used to filter messages to ensure that \
                only messages sent to them are consumed, when more than one consumer consumes the same partition. Defaults to None.

        Returns:
            Optional[Message]: A dictionary of message for communication
        """
        success = 0
        self.consumer.assign([TopicPartition(topic, partition)])

        try:
            # Continuous consumer messages
            for record in self.consumer:
                message: Message = record.value
                logger.info(
                    f"Received message [{message['task']}] from partition [{record.partition}] of topic [{record.topic}] at offset [{record.offset}]"
                )
                if identifier:
                    if message["dst"] == identifier:
                        success = 1
                        return message
                else:
                    success = 1
                    return message
        except Exception as e:
            logger.error(f"Error receiving message: [{e}]")
        finally:
            if success:
                self.consumer.commit()  # 手动提交偏移量
                logger.info(f"[{message['dst']}] receives a message from [{message['src']}]: success")
            else:
                logger.info(f"[{message['dst']}] receives a message from [{message['src']}]: fail")

        return None

    def send(self, message: Message, topic: str = "events", partition: int = 0) -> None:
        """Send messages to specific topic and partition

        Args:
            message (Message): A dictionary of message for communication
            topic (str, optional): Topic for producer to product. Defaults to 'events'.
            partition (int, optional): Partition for producer to product. Defaults to 0.
        """
        success = 0
        try:
            # Send a message and wait for the message to be sent
            future = self.producer.send(topic=topic, partition=partition, key=uuid.uuid4().hex, value=message)
            result = future.get(timeout=10)
            logger.info(f"Sent message [{message['task']}] to partition [{result.partition}] of topic [{result.topic}] at offset [{result.offset}]")
            success = 1
        except Exception as e:
            logger.error(f"Error sending message: [{e}]")
        finally:
            self.producer.flush()  # Refresh the buffer
            if success:
                logger.info(f"[{message['src']}] sents a message to [{message['dst']}]: success")
            else:
                logger.info(f"[{message['src']}] sents a message to [{message['dst']}]: fail")

    def close(self) -> None:
        """close consumer and producer connection"""
        self.consumer.close()
        self.producer.close()


if __name__ == "__main__":
    pass
