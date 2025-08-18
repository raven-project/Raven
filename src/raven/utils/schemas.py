from typing import Any, Dict, List, Literal, TypedDict

from pydantic import BaseModel


class Task(TypedDict):
    """The format of task used for communication."""

    content: str
    host: str
    intent: Literal["Q&A", "Pentest", "None"]


class Message(TypedDict):
    """The format of messages used for communication."""

    src: str
    dst: str
    task: Task
    data: str | Dict[str, Any]
    state: Literal["doing", "done", "failed"]


class LocalMCPConnection(TypedDict):
    """The format of Local MCP Connection used for creating MCP Client."""

    command: Literal["python", "python3"]
    args: List[str]
    transport: Literal["stdio"]


class RemoteMCPConnection(TypedDict):
    """The format of Remote MCP Connection used for creating MCP Client."""

    url: str
    transport: Literal["streamable_http"]


class ListenAddress(TypedDict):
    """The format of Agent Listening address used for communication."""

    topic: Literal["events", "pt_events"]
    partition: Literal[0, 1, 2, 3, 4, 5]


class AgentListen(ListenAddress, total=False):
    """The format of Multi-Agent Listening address used for communication."""

    identifier: str


class LLMConfig(BaseModel):
    """The format and default values of the configuration used for LLM."""

    streaming: bool = True
    max_completion_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.8
    extra_body: dict[str, float] = {"repetition_penalty": 1.05}


MCPConnection = LocalMCPConnection | RemoteMCPConnection
