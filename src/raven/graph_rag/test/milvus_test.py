import os

from dotenv import find_dotenv, load_dotenv

from raven.graph_rag.llm_service.llm_client import LLMClient
from raven.graph_rag.manager_server.milvus_client import MilvusClient

_ = load_dotenv(find_dotenv())
openai_api_key = os.getenv("openai_api_key", "EMPTY")
openai_api_base = os.getenv("openai_api_base", "http://localhost:8000/v1")


client = MilvusClient(
    collection_names=["test"],
    uri="https://in03-65999f931855788.serverless.aws-eu-central-1.cloud.zilliz.com",
    user="db_65999f931855788",
    password="15717747056HYB!",
    dim=4096,
)
llm = LLMClient(
    api_key=openai_api_key,
    base_url=openai_api_base,
    embedding_model="Qwen/Qwen3-Embedding-8B",
    dimensions=4096,
)
# # # print(type(llm.embed("hello world")[0]))
# client.upsert(
#     id_prefix="test",
#     collection_name="test",
#     vector_models=[
#         {
#             "content": "hello world2",
#             "embedding": llm.embed("hello world1"),
#             "meta": [1,3,4]
#          }
#     ]
# )
#
# print(client.count(["test"]))


# r=client.query(
#     collection_name="test",
#     vector_model={
#         "embedding": llm.embed("hell")
#     },
#     output_fields=["vector_id","content","type"]
# )

# print(r)

# m=client.merge(
#     collection_name="test",
#     model={
#         "vector_id": "test3",
#         "content": "hello world2",
#         "meta": [1,4,5]
#     },
#     fields=["meta"]
# )
#
# print(m)

client.upsert(
    id_prefix="t",
    collection_name="test",
    vector_models=[
        {"vector_id": "v02", "hash": "1234567", "content": "我是黄渝斌1", "embedding": llm.embed("我是黄渝斌"), "desc": ["i like apple"]}
    ],
)
m = client.merge(
    collection_name="test",
    model={
        "vector_id": "v01",
        "hash": "1234567",
        "content": "我是黄渝斌1",
        # "embedding": llm.embed("我是黄渝斌"),
        "desc": ["我西黄吃西瓜", "我哎话多"],
    },
    fields=["hash", "desc", "content"],
)
print(m["desc"])
# client.upsert(
#     id_prefix="t",
#     collection_name="test",
#
#     vector_models=[m]
# )
