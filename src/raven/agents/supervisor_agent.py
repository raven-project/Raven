from typing import Any, Dict, Tuple, Union

from langgraph.graph import END, START, StateGraph

from ..utils import listening_mapping, setup_logger
from ..utils.schemas import AgentListen, ListenAddress, Message
from .agent import AgentState, BaseAgent

logger = setup_logger(name=__name__)

name = "super"


class SuperAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name)

        self.listen: AgentListen = listening_mapping(name)

    def output_to_message(self, message: Message, output: Union[Dict[str, Any], Any]) -> Tuple[Message, ListenAddress]:
        return_message: Message = {
            "src": "super",
            "dst": "user",
            "task": output["task"],
            "data": output["result"],
            "state": "done",
        }

        address = listening_mapping("user")

        return return_message, address

    def add_node_edge(self, builder: StateGraph) -> None:
        """Add node and edge."""
        builder.add_node("call_output_agent", self.call_output_agent)
        builder.add_node("call_plan_agent", self.call_plan_agent)

        builder.add_conditional_edges(
            START,
            self.routing,
            {"call_output_agent": "call_output_agent", "call_plan_agent": "call_plan_agent", END: END},
        )
        builder.add_edge("call_plan_agent", END)
        builder.add_edge("call_output_agent", END)

    def routing(self, state: AgentState) -> str:
        if state["task"]["intent"] == "Q&A":
            return "call_output_agent"
        elif state["task"]["intent"] == "Pentest":
            return "call_plan_agent"
        else:
            return END

    def call_output_agent(self, state: AgentState) -> Dict[str, Any]:
        response = self.call_agent(state, "output")

        return {"result": response}

    def call_plan_agent(self, state: AgentState) -> Dict[str, Any]:
        response = self.call_agent(state, "plan")

        return {"result": response}

    def call_agent(self, state: AgentState, name: str) -> str:
        message: Message = {"src": "super", "dst": name, "task": state["task"], "data": "None", "state": "doing"}
        address: ListenAddress = listening_mapping(name)

        self.send_message(message, address)
        message = self.listen_message(self.listen)
        print("Message: ", message)

        return message["data"]
