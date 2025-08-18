from abc import ABC, abstractmethod
import asyncio
import os
from typing import Annotated, Any, Dict, List, Literal, NotRequired, Optional, Tuple, Type, TypedDict, Union, cast

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from pydantic import SecretStr

from ..utils import listening_mapping, setup_logger
from ..utils.kafka_client import KafkaClient
from ..utils.schemas import AgentListen, ListenAddress, LLMConfig, MCPConnection, Message, Task

logger = setup_logger(name=__name__)


class AgentResponse(TypedDict):
    """The format used to represent Agent Response."""

    task: str
    content: Dict[str, Any]
    source: Literal["LLM", "Graph", "Web", "Tool"]
    success: bool
    error: NotRequired[str]
    reflection: Annotated[List, add_messages]


class AgentState(TypedDict):
    """The format used to represent Agent State."""

    task: Task
    decision: str
    subtask: Union[List[str], str]
    current_subtask_index: int
    response: AgentResponse
    result: Any
    revision_number: int
    max_revisions: int
    context: Dict[str, Any]
    history: Dict[str, Any]
    status: Literal["init", "running", "failed", "completed"]
    subtask_status: Dict[str, Literal["waiting", "running", "completed", "failed"]]


class BaseAgent(ABC):
    """Base/Parent class of all agents, implements some common methods and logic."""

    def __init__(self, group_id: Optional[str] = None) -> None:
        """Get the environment variables, including llm, neo4j and kafka config.

        Args:
            group_id (Optional[str], optional): The name of the consumer group. Defaults to None.
        """
        # self.logger = setup_logger(name=self.__class__.__name__)
        # self.logger = logging.LoggerAdapter(logger, {"class_name": self.__class__.__name__})
        logger.extra["class_name"] = self.__class__.__name__  # type: ignore[index]

        self.group_id = group_id

    def run(self) -> None:
        """Agent startup entry."""
        self.get_env()
        logger.info("Getting environment configuration done")

        mcp_servers = getattr(self, "mcp_servers", None)
        self.create_agent(mcp_servers)
        logger.info("Creating agent done")

        logger.info("Running agent ... ")
        listen = getattr(self, "listen", None)
        asyncio.run(self.run_loop(listen))

    def get_env(self) -> None:
        self.kafka_bootstrap_servers = os.getenv("kafka_bootstrap_servers", "localhost:9092")

        self.openai_api_key = SecretStr(os.getenv("openai_api_key", "EMPTY"))
        self.openai_api_base = os.getenv("openai_api_base", "http://localhost:8000/v1")
        self.model = os.getenv("model", "Qwen/Qwen2.5-32B-Instruct")

        self.NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
        self.NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
        self.NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

    def create_agent(
        self,
        mcp_servers: Optional[Dict[str, MCPConnection]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        agent_state: Optional[Type[Any]] = None,
    ) -> None:
        """Create the Agent.

        Steps:
            1. Initialize the config of agent.
            2. Create the workflow of agent with state graph.

        Args:
            mcp_servers (Optional[Dict[str, MCPConnection]], optional): A dictionary mapping server names to connection configurations. \
                If None, Clinet is not initialized. Defaults to None.
            llm_config (Optional[Dict[str, Any]], optional): LLM Configuration, such as temperature, etc. \
                If None, then load the default configuration. Defaults to None.
            agent_state (Optional[Type[Any]], optional): The schema class that defines the state. \
                If None, use the default state. Defaults to None.
        """
        self.init_agent(llm_config, mcp_servers)
        logger.info("Initializing agent done ")

        self.create_state_graph(agent_state)
        logger.info("Creating state graph done")

    def init_agent(self, llm_config: Optional[Dict[str, Any]] = None, mcp_servers: Optional[Dict[str, MCPConnection]] = None) -> None:
        """Initialize agent, including llm, mcp client, kafka and neo4j.

        Args:
            llm_config (Optional[Dict[str, Any]], optional): LLM Configuration, such as temperature, etc. \
                If None, then load the default configuration. Defaults to None.
            mcp_servers (Optional[Dict[str, MCPConnection]], optional): A dictionary mapping server names to connection configurations. \
                If None, Clinet is not initialized. Defaults to None.
        """
        llm_config = llm_config or LLMConfig().model_dump()
        self.llm = ChatOpenAI(api_key=self.openai_api_key, base_url=self.openai_api_base, model=self.model, **llm_config)
        logger.info("Initializing llm done ")

        if mcp_servers:
            mcp_servers_type = cast(Dict[str, Connection], mcp_servers)
            self.mcp_client = MultiServerMCPClient(mcp_servers_type)
            logger.info("Initializing mcp client done")

        self.kafka_client = KafkaClient(kafka_bootstrap_servers=self.kafka_bootstrap_servers, group_id=self.group_id)
        logger.info("Initializing kafka client done ")

        self.neo4j_client = Neo4jGraph(url=self.NEO4J_URI, username=self.NEO4J_USERNAME, password=self.NEO4J_PASSWORD, database=self.NEO4J_DATABASE)
        logger.info("Initializing neo4j client done ")

    def create_state_graph(self, agent_state: Optional[Type[Any]] = None) -> None:
        """Create agent workflow with state graph.

        Steps:
            1. Create a graph whose nodes communicate by reading and writing shared state.
            2. Add nodes and edges.
            3. Compile the state graph into a CompiledStateGraph object.

        The compiled graph implements the Runnable interface and can be invoked, streamed, batched, and run asynchronously.

        Args:
            agent_state (Optional[Type[Any]], optional): The schema class that defines the state. If None, use the default state. Defaults to None.
        """
        if agent_state is None:
            agent_state = AgentState

        builder = StateGraph(agent_state)
        logger.info("Initializing state graph done ")

        self.add_node_edge(builder)
        logger.info("Adding node and edge done")

        self.graph: CompiledStateGraph = builder.compile()
        logger.info("Building state graph done")

    @abstractmethod
    def add_node_edge(self, builder: StateGraph) -> None:
        """Add node and edge.

        Args:
            builder (StateGraph): A graph whose nodes communicate by reading and writing to a shared state.
        """
        pass

    async def run_loop(self, listen: Optional[AgentListen] = None) -> None:
        """Run the main event loop for the agent.

        This loop continuously listens for messages, executes the agent graph, and sends the resulting message to the appropriate destination.

        Steps:
            1. Create the agent.
            2. Listen for messages.
            3. Invoke the agent graph.
            4. Send the response.

        Args:
            listen (Optional[AgentListen], optional): Topics and partitions of agent listening. If None, raise a error. Defaults to None.
        """
        if not listen:
            raise RuntimeError("Failed to start agent, listening address is None.")

        while True:
            message = self.listen_message(listen)
            input = self.message_to_input(message)
            output = await self.graph.ainvoke(input)
            message, address = self.output_to_message(message, output)
            self.send_message(message, address)

    def message_to_input(self, message: Message) -> Union[Dict[str, Any], Any]:
        """Convert message to agent input.

        Args:
            message (Message): Received messages.

        Returns:
            Union[Dict[str, Any], Any]: Agent input.
        """
        input = {"task": message["task"], "revision_number": 0, "max_revisions": 1, "context": message["data"], "status": "init"}

        return input

    def output_to_message(self, message: Message, output: Union[Dict[str, Any], Any]) -> Tuple[Message, ListenAddress]:
        """Convert agent output to message and target to be sent.

        Args:
            message (Message): Received messages.
            output (Union[Dict[str, Any], Any]): Agent output.

        Returns:
            Tuple[Message, ListenAddress]: Message and address to be sent.
        """
        return_message: Message = {
            "src": message["dst"],
            "dst": message["src"],
            "task": message["task"],
            "data": output["result"],
            "state": "done",
        }

        address = listening_mapping(message["src"])

        return return_message, address

    def listen_message(self, listen: AgentListen) -> Message:
        """Receive messages from specific topic and partition.

        Args:
            listen (AgentListen): Topics and partitions of agent listening.

        Returns:
            Message: A dictionary of message for communication.
        """
        topic = listen["topic"]
        partition = listen["partition"]
        identifier = listen.get("identifier")

        message = self.kafka_client.receive(topic, partition, identifier)
        while not message:
            message = self.kafka_client.receive(topic, partition, identifier)

        return message

    def send_message(self, message: Message, address: ListenAddress) -> None:
        """Send messages to specific topic and partition.

        Args:
            message (Message): A dictionary of message for communication.
            address (ListenAddress): Topic and Partition for producer to product.
        """
        topic = address["topic"]
        partition = address["partition"]

        self.kafka_client.send(message, topic, partition)

    async def get_tools(self, server_name: Optional[str] = None) -> List[BaseTool]:
        """Get a list of all tools from connected servers.

        Args:
            server_name (Optional[str], optional): The name of connected servers. Defaults to None.

        Returns:
            List[BaseTool]: A list of all tools.
        """
        tools: List[BaseTool] = await self.mcp_client.get_tools(server_name=server_name)

        return tools


if __name__ == "__main__":
    pass
