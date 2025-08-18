import json
from typing import Any, Dict, Tuple, Union

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph

from ..prompts.intent_prompt import prompt_intent
from ..utils import listening_mapping, setup_logger
from ..utils.schemas import AgentListen, ListenAddress, Message
from .agent import AgentState, BaseAgent

logger = setup_logger(name=__name__)

name = "intent"


class IntentAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name)

        self.listen: AgentListen = listening_mapping(name)

    def output_to_message(self, message: Message, output: Union[Dict[str, Any], Any]) -> Tuple[Message, ListenAddress]:
        return_message: Message = {
            "src": "intent",
            "dst": "super",
            "task": output["task"],
            "data": "None",
            "state": "done",
        }

        address = listening_mapping("super")

        return return_message, address

    def add_node_edge(self, builder: StateGraph) -> None:
        """Add node and edge."""
        builder.add_node("llm_intent", self.llm_intent)

        builder.add_edge(START, "llm_intent")
        builder.add_edge("llm_intent", END)

    def llm_intent(self, state: AgentState) -> Dict[str, Any]:
        messages = [SystemMessage(content=prompt_intent.format(content=state["task"]["content"]))]

        response_llm = self.llm.invoke(messages)
        print("response: ", response_llm.content)

        response_json = json.loads(response_llm.content)  # type: ignore
        print("response: ", response_json)

        state["task"]["host"] = response_json["host"]
        state["task"]["intent"] = response_json["intent"]

        return {"task": state["task"]}
