import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from ..prompts.recon_prompt import prompt_call_tool, prompt_plan_task, prompt_summary, prompt_supervisor
from ..utils import listening_mapping, setup_logger
from ..utils.schemas import AgentListen, MCPConnection
from .agent import AgentState, BaseAgent

logger = setup_logger(name=__name__)

name = "recon"


class ReconAgent(BaseAgent):
    def __init__(self) -> None:
        self.mcp_servers: Dict[str, MCPConnection] = {
            "port_scan": {"command": "python3", "args": ["src/ai_pentest/tools/recon_port_scan.py"], "transport": "stdio"},
            "dir_enumerate": {"command": "python3", "args": ["src/ai_pentest/tools/recon_dir_enum.py"], "transport": "stdio"},
            "app_server": {"command": "python3", "args": ["src/ai_pentest/tools/recon_app_server.py"], "transport": "stdio"},
        }

        super().__init__(name)

        self.listen: AgentListen = listening_mapping(name)

    def add_node_edge(self, builder: StateGraph) -> None:
        """Add node and edge."""
        builder.add_node("plan_task", self.plan_task)
        builder.add_node("supervisor", self.supervisor)
        builder.add_node("port_scan", self.port_scan)
        builder.add_node("dir_enumerate", self.dir_enumerate)
        builder.add_node("app_server", self.app_server)
        builder.add_node("summary", self.summary)

        builder.add_edge(START, "plan_task")
        builder.add_edge("plan_task", "supervisor")
        builder.add_conditional_edges(
            "supervisor",
            self.routing,
            {"port_scan": "port_scan", "dir_enumerate": "dir_enumerate", "app_server": "app_server", "summary": "summary", END: END},
        )
        builder.add_edge("port_scan", "supervisor")
        builder.add_edge("dir_enumerate", "supervisor")
        builder.add_edge("app_server", "supervisor")
        builder.add_edge("summary", END)

    def plan_task(self, state: AgentState) -> Dict[str, Any]:
        messages = [SystemMessage(content=prompt_plan_task.format(content=state["task"]["content"]))]

        response = self.llm.invoke(messages)
        print("subtask: ", response.content)

        try:
            subtasks = json.loads(str(response.content))
            assert isinstance(subtasks, list)
        except Exception as e:
            logger.info(f"[ERROR] Failed to parse subtasks: {e}")
            subtasks = [
                "执行目标资产的端口扫描，识别开放端口和运行服务",
                "对目标站点进行目录枚举，发现潜在的隐藏路径或敏感接口",
                "对目标站点进行指纹识别，识别服务类型、框架和中间件信息，判断技术栈与应用特征",
            ]

        return {"subtask": subtasks, "history": {"plan_task": subtasks}, "current_subtask_index": -1}

    def supervisor(self, state: AgentState) -> Dict[str, Any]:
        if state["current_subtask_index"] >= (len(state["subtask"]) - 1):
            print("[INFO] All subtasks completed. Going to summary.")
            return {"decision": "summary"}

        messages = [SystemMessage(content=prompt_supervisor.format(content=state["subtask"][state["current_subtask_index"] + 1]))]
        response = self.llm.invoke(messages)
        print("decision: ", response.content)

        return {"decision": response.content, "current_subtask_index": state["current_subtask_index"] + 1}

    def routing(self, state: AgentState) -> str:
        if state["decision"] == "port_scan":
            return "port_scan"
        elif state["decision"] == "dir_enumerate":
            return "dir_enumerate"
        elif state["decision"] == "app_server":
            return "app_server"
        elif state["decision"] == "summary":
            return "summary"
        else:
            return END

    async def port_scan(self, state: AgentState) -> Dict[str, Any]:
        response = await self.tool_call("port_scan", state)

        return {"history": response}

    async def dir_enumerate(self, state: AgentState) -> Dict[str, Any]:
        response = await self.tool_call("dir_enumerate", state)

        return {"history": response}

    async def app_server(self, state: AgentState) -> Dict[str, Any]:
        response = await self.tool_call("app_server", state)

        return {"history": response}

    async def tool_call(self, server_name: str, state: AgentState) -> Dict[str, Any]:
        tools = await super().get_tools(server_name=server_name)
        tool_node = ToolNode(tools)

        logger.info(f"[DEBUG] current_subtask_index: {state['current_subtask_index']}")
        logger.info(f"[DEBUG] current subtask content: {state['subtask'][state['current_subtask_index']]}")

        messages = [
            SystemMessage(
                content=prompt_call_tool.format(content=state["subtask"][state["current_subtask_index"]], host=state["task"].get("host", ""))
            )
        ]

        response_llm = await self.llm.bind_tools(tools).ainvoke(messages)
        logger.info("llm response:%s", response_llm)

        response_tool = await tool_node.ainvoke({"messages": [response_llm]})
        response = {"task": state["task"]["content"], "content": response_tool, "source": "Tool", "success": True}
        logger.info("[DEBUG] LLM raw response:%s\n", response)

        state["history"].update({server_name: response})
        return state["history"]

    def summary(self, state: AgentState) -> Dict[str, Any]:
        messages = [SystemMessage(content=prompt_summary.format(content=state["history"]))]
        response = self.llm.invoke(messages)
        print("result:", response.content)

        return {"result": response.content}


if __name__ == "__main__":
    pass
