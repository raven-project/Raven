import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src")))

from typing import Literal

from dotenv import find_dotenv, load_dotenv
from mcp.server.fastmcp import FastMCP

from raven.graph_rag.graph_rag import GraphRAG
from raven.graph_rag.ingestion_service.document_loader import DocumentLoader
from raven.graph_rag.ingestion_service.text_chunker import TextChunker
from raven.graph_rag.llm_service.llm_client import LLMClient
from raven.graph_rag.manager_server.milvus_client import MilvusClient
from raven.graph_rag.manager_server.neo4j_client import Neo4jClient

_ = load_dotenv(find_dotenv())

milvus_url = os.getenv("milvus_url", "http://localhost:19530")

openai_api_key = os.getenv("openai_api_key", "EMPTY")
openai_api_base = os.getenv("openai_api_base", "http://localhost:8000/v1")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

mcp = FastMCP("Local_Search")


@mcp.tool()
async def graph_search(query: str, search_type: Literal["origin", "graph"] = "origin") -> str:
    """使用 RAG 检索图数据。

    Args:
        query (str): _description_
        search_type (Literal["origin", "graph"], optional): "origin" or "graph". "origin" means query only by vector database. \
        "graph" means query entity firstly by vector database, then query by graph database. Defaults to "origin".

    Returns:
        str: _description_
    """
    rag = GraphRAG(
        text_chunker=TextChunker(),
        document_loader=DocumentLoader(),
        vector_client=MilvusClient(
            collection_names=["test_entity_json", "test_text_json"],
            uri=milvus_url,
            user="",
            password="",
            dim=4096,
        ),
        graph_client=Neo4jClient(uri=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE),
        entity_vector_collection="test_entity_json",
        text_vector_collection="test_text_json",
        llm_client=LLMClient(
            api_key=openai_api_key,
            base_url=openai_api_base,
            model="deepseek-ai/DeepSeek-V3",
        ),
        rerank_client=LLMClient(
            api_key=openai_api_key,
            base_url=openai_api_base,
            rerank_model="Qwen/Qwen3-Reranker-8B",
        ),
        embed_client=LLMClient(
            api_key=openai_api_key,
            base_url=openai_api_base,
            embedding_model="Qwen/Qwen3-Embedding-8B",
            dimensions=4096,
        ),
    )

    response = rag.query(query=query, search_type=search_type)

    return response


if __name__ == "__main__":
    mcp.run(transport="stdio")
