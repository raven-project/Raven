from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from ..utils import listening_mapping, setup_logger
from ..utils.schemas import AgentListen, ListenAddress, Message
from .agent import AgentState, BaseAgent

logger = setup_logger(name=__name__)

name = "output"


class OutputAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name)

        self.listen: AgentListen = listening_mapping(name)

    def add_node_edge(self, builder: StateGraph) -> None:
        """Add node and edge."""
        builder.add_node("q_a", self.q_a)

        builder.add_edge(START, "q_a")
        builder.add_edge("q_a", END)

    def q_a(self, state: AgentState) -> Dict[str, Any]:
        message: Message = {"src": "output", "dst": "search", "task": state["task"], "data": "None", "state": "doing"}
        address: ListenAddress = listening_mapping("search")

        self.send_message(message, address)
        message = self.listen_message(self.listen)

        return {"result": message["data"]}


if __name__ == "__main__":
    pass
