from typing import Any, Dict

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from ..prompts.attack_prompt import prompt_call_tool, prompt_router, prompt_summary
from ..utils import listening_mapping, setup_logger
from ..utils.schemas import AgentListen, MCPConnection
from .agent import AgentState, BaseAgent

logger = setup_logger(name=__name__)

name = "attack"


class AttackAgent(BaseAgent):
    def __init__(self) -> None:
        self.mcp_servers: Dict[str, MCPConnection] = {
            "ftp_ssh": {"command": "python3", "args": ["src/ai_pentest/tools/attack_ftp_ssh.py"], "transport": "stdio"},
            # "web": {"command": "python3", "args": ["src/ai_pentest/tools/attack_web.py"], "transport": "stdio"},
            "web": {"url": "http://localhost:8000/mcp/", "transport": "streamable_http"},
        }

        super().__init__(name)

        self.listen: AgentListen = listening_mapping(name)

    def add_node_edge(self, builder: StateGraph) -> None:
        """Add node and edge."""
        builder.add_node("router", self.router)
        builder.add_node("ssh_server", self.ssh_server)
        builder.add_node("ftp_server", self.ftp_server)
        builder.add_node("web_server", self.web_server)
        builder.add_node("summary", self.summary)

        builder.add_edge(START, "router")
        builder.add_conditional_edges(
            "router",
            self.routing,
            {"ssh_server": "ssh_server", "ftp_server": "ftp_server", "web_server": "web_server", END: END},
        )
        builder.add_edge("ssh_server", "summary")
        builder.add_edge("ftp_server", "summary")
        builder.add_edge("web_server", "summary")
        builder.add_edge("summary", END)

    def router(self, state: AgentState) -> Dict[str, Any]:
        messages = [SystemMessage(content=prompt_router.format(content=state["task"]["content"]))]

        response = self.llm.invoke(messages)
        print("decision: ", response.content)

        return {"decision": response.content}

    def routing(self, state: AgentState) -> str:
        if state["decision"] == "ssh_server":
            return "ssh_server"
        elif state["decision"] == "ftp_server":
            return "ftp_server"
        elif state["decision"] == "web_server":
            return "web_server"
        else:
            return END

    async def ssh_server(self, state: AgentState) -> Dict[str, Any]:
        response = await self.tool_call("ftp_ssh", state)

        return {"response": response}

    async def ftp_server(self, state: AgentState) -> Dict[str, Any]:
        response = await self.tool_call("ftp_ssh", state)

        return {"response": response}

    async def web_server(self, state: AgentState) -> Dict[str, Any]:
        response = await self.tool_call("web", state)

        return {"response": response}

    async def tool_call(self, server_name: str, state: AgentState) -> Dict[str, Any]:
        tools = await super().get_tools(server_name=server_name)
        tool_node = ToolNode(tools)

        messages = [SystemMessage(content=prompt_call_tool.format(content=state["task"]["content"], context=state["context"]))]
        response_llm = self.llm.bind_tools(tools).invoke(messages)
        print("llm response: ", response_llm)

        response_tool = await tool_node.ainvoke({"messages": [response_llm]})
        response = {"task": state["task"]["content"], "content": response_tool, "source": "Tool", "success": True}

        return response

    def summary(self, state: AgentState) -> Dict[str, Any]:
        messages = [SystemMessage(content=prompt_summary.format(content=state["response"]["content"]))]
        response = self.llm.invoke(messages)
        print("result: ", response.content)

        return {"result": response.content}


if __name__ == "__main__":
    pass
