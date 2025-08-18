import argparse
import subprocess
from typing import Any, Dict

import yaml


# read yaml config file
def read_yaml(filename: str) -> Dict[str, Any]:
    print(f"reading config file {filename} ······")
    with open(filename, encoding="utf8") as file:
        config: Dict[str, Any] = yaml.safe_load(file)
    print(f"reading config file {filename} complete")
    return config


# download and load neo4j dump data
def load_neo4j(config: Dict[str, Any]) -> None:
    # downloading
    if config["download"]["enable"]:
        print("downloading neo4j dump data ······")
        command = config["download"]["command"].format(path=config["download"]["path"], url=config["download"]["url"])
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("downloading neo4j dump data complete")

    # loading
    print("loading neo4j dump data ······")
    command = config["load"]["command"].format(path=config["load"]["path"], database=config["load"]["database"])
    subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
    print("loading neo4j dump data complete")


# start docker compose
def run_app(config: Dict[str, Any]) -> None:
    print("starting docker compose ······")
    command = config["command"]
    subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
    print("starting docker compose complete")


# create kafka topic
def create_topic(config: Dict[str, Any]) -> None:
    print("creating kafka topic ······")
    for name in config["name"]:
        command = config["command"].format(topic=name)
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"topic {name} has created")
    print("creating kafka topic complete")


def main():
    print("initializing app ······")
    config = read_yaml(args.config_file)
    load_neo4j(config["init"]["neo4j"])
    run_app(config["init"]["app"]["start"])
    create_topic(config["init"]["kafka"]["topic"])
    print("initializing app complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_file", type=str, metavar="", default="configuration.yaml", help="app starting config file")
    args = parser.parse_args()
    main()
