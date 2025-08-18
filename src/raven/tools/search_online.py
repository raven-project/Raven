import asyncio
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import requests

# 加载环境变量
load_dotenv()

# 创建 MCP 实例
mcp = FastMCP("Online_Search")

# Serper 配置
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"


@mcp.tool()
async def online_search(input: str) -> dict:
    """
    使用 Serper API 执行网页搜索。
    """
    headers = {"X-API-KEY": SERPER_API_KEY}
    params = {"q": input}

    try:
        response = await asyncio.to_thread(requests.get, SERPER_URL, headers=headers, params=params)
        if response.status_code == 200:
            return {"output": response.json()}
        else:
            return {"output": [], "error": f"HTTP {response.status_code} - {response.text}"}
    except Exception as e:
        return {"output": [], "error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
