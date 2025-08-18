import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage
from langgraph.graph import END, StateGraph

from ..prompts.plan_prompt import prompt_plan_task
from ..utils import listening_mapping, setup_logger
from ..utils.schemas import AgentListen, ListenAddress, Message
from .agent import AgentState, BaseAgent

logger = setup_logger(name=__name__)

name = "plan"


class PlanAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name)

        self.listen: AgentListen = listening_mapping(name)

    def add_node_edge(self, builder: StateGraph) -> None:
        """Add node and edge."""

        builder.add_node("plan_task", self.plan_task)
        builder.add_node("supervisor", self.supervisor)
        builder.add_node("call_recon_agent", self.call_recon_agent)
        builder.add_node("call_attack_agent", self.call_attack_agent)
        builder.add_node("summary", self.summary)

        builder.set_entry_point("plan_task")
        builder.add_edge("plan_task", "supervisor")
        builder.add_conditional_edges(
            "supervisor",
            self.routing,
            {"call_recon_agent": "call_recon_agent", "call_attack_agent": "call_attack_agent", "summary": "summary", END: END},
        )
        builder.add_edge("call_recon_agent", "supervisor")
        builder.add_edge("call_attack_agent", "supervisor")
        builder.add_edge("summary", END)

    def plan_task(self, state: AgentState) -> Dict[str, Any]:
        messages = [SystemMessage(content=prompt_plan_task.format(content=state["task"]["content"]))]

        response = self.llm.invoke(messages)
        print("decision: ", response.content)

        try:
            subtasks = json.loads(str(response.content))
            assert isinstance(subtasks, list)
        except Exception as e:
            logger.info(f"[ERROR] Failed to parse subtasks: {e}")
            subtasks = ["call_recon_agent", "call_attack_agent"]

        return {"subtask": subtasks, "history": {}, "current_subtask_index": -1}

    def supervisor(self, state: AgentState) -> Dict[str, Any]:
        if state["current_subtask_index"] >= (len(state["subtask"]) - 1):
            print("[INFO] All subtasks completed. Going to summary.")
            return {"decision": "summary"}

        decision = state["subtask"][state["current_subtask_index"]+1]
        print("decision: ", decision)

        return {"decision": decision, "current_subtask_index": state["current_subtask_index"] + 1}

    def routing(self, state: AgentState) -> str:
        if state["decision"] == "call_recon_agent":
            return "call_recon_agent"
        elif state["decision"] == "call_attack_agent":
            return "call_attack_agent"
        elif state["decision"] == "summary":
            return "summary"
        else:
            return END

    def call_recon_agent(self, state: AgentState) -> Dict[str, Any]:
        response = self.call_agent(state, "recon")

        return {"history": response}

    def call_attack_agent(self, state: AgentState) -> Dict[str, Any]:
        response = self.call_agent(state, "attack")

        return {"history": response}

    def call_agent(self, state: AgentState, name: str) -> Dict[str, Any]:
        message: Message = {"src": "plan", "dst": name, "task": state["task"], "data": state["history"], "state": "doing"}
        address: ListenAddress = listening_mapping(name)

        self.send_message(message, address)
        message = self.listen_message(self.listen)

        state["history"].update({name: message["data"]})

        return state["history"]

    def summary(self, state: AgentState) -> Dict[str, Any]:
        recon_response = ""
        attack_response = ""

        if "recon" in state["history"]:
            recon_response: str = state["history"]["recon"]
            print("recon_response")
        if "attack" in state["history"]:
            attack_response: str = state["history"]["attack"]
            print("attack_response")

        response = recon_response + attack_response
        print("result:", response)

        return {"result": response}


if __name__ == "__main__":
    pass
