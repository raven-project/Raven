from raven.graph_rag.manager_server.neo4j_client import Neo4jClient

client = Neo4jClient(uri="neo4j://127.0.0.1:7687", username="neo4j", password="12345678")

#
client.upsert_entity(entity={"id": "t01", "type": "precise", "desc": ["Document findings, exploit details, and remediation recommendations"]})  #

client.upsert_entity(
    entity=client.merge_entities(
        {"id": "t01", "type": "precise", "desc": ["Document findings, exploit details, and remediation recommendations", "i like eat orange"]}
    )
)

client.upsert_entity(entity={"id": "test02", "type": "abstract", "desc": ["my name is huangyubin,you fuck", "i like apple"]})

client.upsert_relationship(
    relationship={"id": "r01", "source_id": "t01", "target_id": "test02", "relation": "用于", "desc": ["this is me", "my name is huangyubin"]}
)
c = client.merge_relationship({"id": "r01", "source_id": "t01", "target_id": "test02", "relation": "用于", "desc": ["I like me"]})
client.upsert_relationship(relationship=c)

#
#
# client.upsert_relationship(
#     relationship={
#         "id": "r01",
#         "source_id": "e02",
#         "target_id": "e01",
#         "relation": "喜欢"
#     }
# )
#
