import os

from dotenv import find_dotenv, load_dotenv

from raven.graph_rag.graph_rag import GraphRAG
from raven.graph_rag.ingestion_service.document_loader import DocumentLoader
from raven.graph_rag.ingestion_service.text_chunker import TextChunker
from raven.graph_rag.llm_service.llm_client import LLMClient
from raven.graph_rag.manager_server.milvus_client import MilvusClient
from raven.graph_rag.manager_server.neo4j_client import Neo4jClient

_ = load_dotenv(find_dotenv())
milvus_url = os.getenv("milvus_url", "localhost:19530")

openai_api_key = os.getenv("openai_api_key", "EMPTY")
openai_api_base = os.getenv("openai_api_base", "http://localhost:8000/v1")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = "neo4j"


rag = GraphRAG(
    text_chunker=TextChunker(),
    document_loader=DocumentLoader(),
    vector_client=MilvusClient(
        collection_names=["test_entity_json", "test_text_json"],
        uri="https://in03-65999f931855788.serverless.aws-eu-central-1.cloud.zilliz.com",
        user="db_65999f931855788",
        password="15717747056HYB!",
        dim=4096,
    ),
    graph_client=Neo4jClient(uri="neo4j://127.0.0.1:7687", username="neo4j", password="12345678", database="testjson"),
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

#
# if __name__ == "__main__":
# # rag.upsert(source="graph_rag_text.txt")
# rag.upsert(source="test.json")

# if __name__ == '__main__':
q = rag.query(search_type="origin", query="Windows 11 x64 - Reverse TCP Shellcode (564 bytes) 漏洞谁发现的？")
print(q)
