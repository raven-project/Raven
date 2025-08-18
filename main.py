import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import argparse
from multiprocessing import Process
import time
from typing import Any, Dict, Iterator, List, Type

from dotenv import find_dotenv, load_dotenv
import gradio as gr
import yaml

# from ai_pentest.agents import *  # noqa: F403
from raven.agents import AttackAgent, IntentAgent, OutputAgent, PlanAgent, ReconAgent, SearchAgent, SuperAgent
from raven.utils import listening_mapping, setup_logger
from raven.utils.kafka_client import KafkaClient
from raven.utils.schemas import Message

_ = load_dotenv(find_dotenv())  # read local .env file
kafka_bootstrap_servers = os.getenv("kafka_bootstrap_servers", "localhost:9092")

logger = setup_logger(consolehandle=True)


# read yaml config file
def read_yaml(filename: str) -> Dict[str, Any]:
    with open(filename, encoding="utf8") as file:
        config: Dict[str, Any] = yaml.safe_load(file)

    return config


def run_agent(agent: Type) -> None:
    agent_obj = agent()
    agent_obj.run()


def start_agent(config: Dict[str, Any]) -> None:
    for agent in [AttackAgent, IntentAgent, OutputAgent, PlanAgent, ReconAgent, SearchAgent, SuperAgent]:
        p = Process(target=run_agent, args=(agent,))
        p.start()

    time.sleep(7)


def run(message: str, history: List[Dict[str, str]]) -> str:
    send_message: Message = {
        "src": "user",
        "dst": "intent",
        "task": {"content": message, "host": "None", "intent": "None"},
        "data": "None",
        "state": "doing",
    }
    address = listening_mapping("intent")
    listen = listening_mapping("user")

    kafka_client = KafkaClient(kafka_bootstrap_servers=kafka_bootstrap_servers, group_id="user")
    kafka_client.send(send_message, topic=address["topic"], partition=address["partition"])

    receive_message = kafka_client.receive(listen["topic"], listen["partition"], listen["identifier"])
    if receive_message:
        output = receive_message.get("data", "error")
        return f"{output}"

    return "No response received"


def print_stream(message: str, history: List[Dict[str, str]]) -> Iterator[str]:
    text = run(message, history)

    for i in range(1, len(text) + 1):
        time.sleep(0.02)
        yield text[:i]


def start_web(config: Dict[str, Any]) -> None:
    demo = gr.ChatInterface(print_stream, type="messages", save_history=True)
    demo.launch()


def main(args):  # type: ignore[no-untyped-def]
    logger.info("Hello from ai-pentest!")

    config = read_yaml(args.config_file)
    logger.info("reading config file complete")

    start_agent(config["running"]["agent"])
    logger.info("starting agent complete")

    start_web(config["running"]["web"])
    logger.info("starting web complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_file", type=str, metavar="", default="./docker/configuration.yaml", help="app starting config file")
    args = parser.parse_args()
    main(args)
