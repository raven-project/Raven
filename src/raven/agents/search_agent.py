from typing import Any, Dict

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from ..prompts.search_prompt import prompt_call_tool, prompt_judge_local, prompt_judge_online, prompt_summary
from ..utils import listening_mapping, setup_logger
from ..utils.schemas import AgentListen, MCPConnection
from .agent import AgentState, BaseAgent

logger = setup_logger(name=__name__)

name = "search"


class SearchAgent(BaseAgent):
    def __init__(self) -> None:
        self.mcp_servers: Dict[str, MCPConnection] = {
            "online_search": {"command": "python3", "args": ["src/ai_pentest/tools/search_online.py"], "transport": "stdio"},
            "local_search": {"command": "python3", "args": ["src/ai_pentest/tools/search_local.py"], "transport": "stdio"},
        }

        super().__init__(name)

        self.listen: AgentListen = listening_mapping(name)

    def add_node_edge(self, builder: StateGraph) -> None:
        """Add node and edge."""
        builder.add_node("judge_online", self.judge_online)
        builder.add_node("judge_local", self.judge_local)
        builder.add_node("online_search", self.online_search)
        builder.add_node("local_search", self.local_search)
        builder.add_node("summary", self.summary)

        builder.add_edge(START, "judge_online")
        builder.add_conditional_edges(
            "judge_online",
            self.routing_online,
            {"online_search": "online_search", "local_search": "local_search", END: END},
        )
        builder.add_edge("local_search", "judge_local")
        builder.add_conditional_edges(
            "judge_local",
            self.routing_local,
            {"online_search": "online_search", "summary": "summary", END: END},
        )
        builder.add_edge("online_search", "summary")
        builder.add_edge("summary", END)

    def judge_online(self, state: AgentState) -> Dict[str, Any]:
        messages = [SystemMessage(content=prompt_judge_online.format(content=state["task"]["content"]))]

        response = self.llm.invoke(messages)
        print("decision: ", response.content)

        return {"decision": response.content}

    def routing_online(self, state: AgentState) -> str:
        if state["decision"] == "online_search":
            return "online_search"
        elif state["decision"] == "local_search":
            return "local_search"
        else:
            return END

    def judge_local(self, state: AgentState) -> Dict[str, Any]:
        messages = [SystemMessage(content=prompt_judge_local.format(content=state["response"]))]

        response = self.llm.invoke(messages)
        print("decision: ", response.content)

        return {"decision": response.content}

    def routing_local(self, state: AgentState) -> str:
        if state["decision"] == "online_search":
            return "online_search"
        elif state["decision"] == "summary":
            return "summary"
        else:
            return END

    async def local_search(self, state: AgentState) -> Dict[str, Any]:
        response = await self.tool_call("local_search", state)

        return {"response": response}

    async def online_search(self, state: AgentState) -> Dict[str, Any]:
        response = await self.tool_call("online_search", state)

        return {"response": response}

    async def tool_call(self, server_name: str, state: AgentState) -> Dict[str, Any]:
        tools = await super().get_tools(server_name=server_name)
        tool_node = ToolNode(tools)

        messages = [SystemMessage(content=prompt_call_tool.format(content=state["task"]["content"]))]
        response_llm = self.llm.bind_tools(tools).invoke(messages)
        print("llm response: ", response_llm)

        response_tool = await tool_node.ainvoke({"messages": [response_llm]})
        response = {"task": state["task"]["content"], "content": response_tool, "source": "Tool", "success": True}
        print("tool response: ", response_tool)

        return response

    def summary(self, state: AgentState) -> Dict[str, Any]:
        messages = [SystemMessage(content=prompt_summary.format(content=state["response"]["content"]))]
        response = self.llm.invoke(messages)
        print("result: ", response.content)

        return {"result": response.content}


if __name__ == "__main__":
    pass
