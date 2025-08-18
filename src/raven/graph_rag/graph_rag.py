import hashlib
import logging
import time
from typing import Any, Dict, List, Literal, Tuple

from raven.graph_rag.entity_service.entity_extractor import EntityExtractor
from raven.graph_rag.ingestion_service.document_loader import DocumentLoader
from raven.graph_rag.ingestion_service.text_chunker import TextChunker
from raven.graph_rag.llm_service.llm_client import LLMClient
from raven.graph_rag.manager_server.base.base_graph_client import BaseGraphClient
from raven.graph_rag.manager_server.base.base_vector_client import BaseVectorClient

# 配置日志格式和等级
logging.basicConfig(
    level=logging.INFO,  # 或 DEBUG、WARNING、ERROR、CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class GraphRAG:
    def __init__(
        self,
        text_chunker: TextChunker,
        document_loader: DocumentLoader,
        llm_client: LLMClient,
        embed_client: LLMClient,
        rerank_client: LLMClient,
        vector_client: BaseVectorClient,
        graph_client: BaseGraphClient,
        threshold_score: float = 0.1,
        entity_vector_collection: str = "entity_cl",
        entity_vector_id_prefix: str = "entity",
        text_vector_id_prefix: str = "text",
        text_vector_collection: str = "text_cl",
        prompt_source: str = "template/query.prompt",
    ):
        self.text_chunker = text_chunker
        self.document_loader = document_loader
        self.llm_client = llm_client
        self.embed_client = embed_client
        self.rerank_client = rerank_client
        self.vector_count = vector_client.count([entity_vector_collection, text_vector_collection])
        self.vector_client = vector_client
        self.entity_vector_collection = entity_vector_collection
        self.text_vector_collection = text_vector_collection
        self.graph_client = graph_client
        self.extractor = EntityExtractor(llm_client=llm_client)
        self.prompt_source = prompt_source
        self.threshold_score = threshold_score
        self.entity_vector_id_prefix = entity_vector_id_prefix
        self.text_vector_id_prefix = text_vector_id_prefix

    def upsert(self, source: str = "") -> bool:
        """
        Example Flow:
            Text vector Store：
            {
                vector_id:"",
                content:"",
                embedding: [],
                "entity_ids":[],
                "source":"", tips: "https://xxxx" or file path,
                "type":["","" ...]
                "tags": ["","" ...]
            }
            Entity vector Store:
            {
                "vector_id:"",
                "content":"",
                embedding:[],
                "chunk_ids": ["",""],
                "type":["precise","abstract"],
                "tags":["","",...],
                "alias":["","",...]
            }

            Graph vector Store:
            {
                "id": "",
                "relation":"",
                "source_id":"",
                "target_id":"",
            }

        """
        start = time.perf_counter()
        text = self.document_loader.load(source=source)
        chunker_texts = self.text_chunker.chunk_text(text=text)

        for chunker_text in chunker_texts:
            # llm create entity
            result = self._load_entity(chunker_text)

            #
            logging.info("Initializing Entity And Text ......")
            # process entity and text vector
            processed_entities, processed_text = self._process_text(chunker_text=chunker_text, source=source, result=result)
            logging.info("Upserting Vector ...... ")
            # upsert vector
            self._upsert_vector(processed_entities=processed_entities, processed_text=processed_text)
            #
            # # upsert graph
            relationships = result["relationships"]

            logging.info("Upserting Graph ......")
            # print(f"r={relationships}")
            self._upsert_graph(merged_entities=processed_entities, relationships=relationships)

            end = time.perf_counter()
            logging.info(f"Upsert Success time: {end - start:.2f} s")
        return True

    def query(
        self, query: str = "hello", top_depth: int = 5, top_k: int = 5, max_nodes: int = 100, search_type: Literal["origin", "graph"] = "origin"
    ) -> str:
        if search_type == "origin":
            return self._origin_search(query=query, top_k=top_k)
        elif search_type == "graph":
            return self._graph_search(query=query, top_k=top_k, top_depth=top_depth, max_nodes=max_nodes)

    def _origin_search(self, query: str, top_k: int) -> str:
        # query by vector database
        vector_models = self.vector_client.query(
            collection_name=self.text_vector_collection,
            top_k=top_k,
            embedding=self.embed_client.embed(text=query),
            output_fields=["vector_id", "content"],
        )

        documents = [model["content"] for model in vector_models]

        # rerank
        resp = self.rerank_client.rerank(query=query, documents=documents)
        texts = []
        for result in resp["results"]:
            texts.append(documents[result["index"]])

        text = "\n".join(texts)

        # build context
        prompt = self.extractor.load_prompt(text, self.prompt_source, question=query)

        # query to llm
        return self.llm_client.quick_chat(query=prompt)  # type: ignore

    def _graph_search(self, query: str, top_k: int, top_depth: int, max_nodes: int) -> str:
        result = self.extractor.extract_query_entity(query)
        entities = result["entities"]
        entity_prompts = []
        precise_entities = [entity["content"] for entity in entities if entity["type"] == "precise"]
        abstract_entities = [entity["content"] for entity in entities if entity["type"] == "abstract"]
        precise_content = ",".join(precise_entities)
        abstract_content = ",".join(abstract_entities)

        # query vector database
        precise_vector_models = self.vector_client.query(
            collection_name=self.entity_vector_collection,
            embedding=self.embed_client.embed(precise_content),
            top_k=top_k,
            output_fields=["vector_id", "content"],
        )

        abstract_vector_models = self.vector_client.query(
            collection_name=self.entity_vector_collection,
            embedding=self.embed_client.embed(abstract_content),
            top_k=top_k,
            output_fields=["vector_id", "content"],
        )
        vector_ids = list(set([model["vector_id"] for model in precise_vector_models] + [model["vector_id"] for model in abstract_vector_models]))
        # get all entity-relationship-entity
        for id in vector_ids:
            graph = self.graph_client.find(
                node_id=id,
                max_depth=top_depth,
                max_nodes=max_nodes,
            )
            if graph:
                entity_prompt = self.graph_client.build_prompt(graph=graph)
                entity_prompts.append(entity_prompt)

        prompt = self.extractor.load_prompt(text="\n".join(entity_prompts), source=self.prompt_source, question=query)
        return self.llm_client.quick_chat(query=prompt)  # type: ignore

    def _upsert_graph(self, merged_entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> None:
        labels = []
        labels.append("")
        # upsert graph entity
        for entity in merged_entities:
            merged_entity = self.graph_client.merge_entities(
                {"id": entity["vector_id"], "name": entity["content"], "type": entity["type"], "desc": entity["desc"]}
            )
            self.graph_client.upsert_entity(entity=merged_entity)

        # build RelationShip
        relationship_list = []

        for relationship in relationships:
            # 找 source
            source_id = next((entity["vector_id"] for entity in merged_entities if entity["content"] == relationship["source"]), None)
            # 找 target
            target_id = next((entity["vector_id"] for entity in merged_entities if entity["content"] == relationship["target"]), None)

            # 如果有一个没找到，就跳过
            if source_id is None or target_id is None:
                logging.warning(f"[WARN] Skipping relationship {relationship}  because entity not found.")
                continue

            relationship_list.append(
                {
                    "id": f"relation_{source_id}_{target_id}",
                    "relation": relationship["relationship"],
                    "source_id": source_id,
                    "target_id": target_id,
                    "desc": relationship["desc"] if relationship["desc"] else "此关系无描述",
                }
            )

        for relationShip in relationship_list:
            merged_relationship = self.graph_client.merge_relationship({**relationShip})
            self.graph_client.upsert_relationship(relationship=merged_relationship)

    def _merge_meta_data(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        if dict1 is None:
            return dict2

        if dict2 is None:
            return dict1

        result: Dict[str, Any] = {}

        keys = set(dict1.keys()) | set(dict2.keys())
        for key in keys:
            val1 = dict1.get(key)
            val2 = dict2.get(key)

            if key in dict1 and key in dict2:
                if isinstance(val1, str) and isinstance(val2, str):
                    result[key] = val1  # 取第一个
                elif isinstance(val1, list) and isinstance(val2, list):
                    result[key] = list(set(val1 + val2))  # 合并去重
                else:
                    # 不一致类型，默认用第一个
                    result[key] = val1
            else:
                result[key] = val1 if key in dict1 else val2

        return result

    def _upsert_vector(self, processed_entities: List[Dict[str, Any]], processed_text: List[Dict[str, Any]]) -> None:
        # builder vector

        # upsert
        self.vector_client.upsert(
            collection_name=self.entity_vector_collection, vector_models=processed_entities, id_prefix=self.entity_vector_id_prefix
        )
        self.vector_client.upsert(collection_name=self.text_vector_collection, vector_models=processed_text, id_prefix=self.text_vector_id_prefix)

    def _merge(
        self, entity_vector_models: List[Dict[str, Any]], text_vector_models: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        merged_entity_models = list(
            map(
                lambda model: self.vector_client.merge(
                    collection_name=self.entity_vector_collection, model=model, fields=["vector_id", "chunk_ids", "type", "desc"]
                ),
                entity_vector_models,
            )
        )
        merged_text_models = list(
            map(
                lambda model: self.vector_client.merge(
                    collection_name=self.text_vector_collection, model=model, fields=["vector_id", "entity_ids", "source", "type"]
                ),
                text_vector_models,
            )
        )
        return merged_entity_models, merged_text_models

    def _process_text(self, chunker_text: str, source: str, result: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        embed_llm = self.embed_client
        entities = result["entities"]

        process_entities = [
            {
                **entity,
                "hash": hashlib.md5(str(entity["content"]).encode("utf-8")).hexdigest(),
                "embedding": embed_llm.embed(entity["content"] + "\n" + entity["desc"]),
                "vector_id": "",
                "desc": [entity["desc"]],
            }
            for i, entity in enumerate(entities)
        ]

        process_text = [
            {
                "vector_id": "",
                "content": chunker_text,
                "hash": hashlib.md5(chunker_text.encode("utf-8")).hexdigest(),
                "embedding": embed_llm.embed(chunker_text),
                "source": source,
            }
        ]

        # merge
        merged_entity_models, merged_text_models = self._merge(entity_vector_models=process_entities, text_vector_models=process_text)

        count = self.vector_client.count([self.entity_vector_collection, self.text_vector_collection])
        entity_index = count[self.entity_vector_collection]
        text_index = count[self.text_vector_collection]

        # 处理一些vector_id为空的情况
        id_merged_entity_models = []
        i = 1
        for merged_entity_model in merged_entity_models:
            if not merged_entity_model["vector_id"]:
                id_merged_entity_models.append({**merged_entity_model, "vector_id": f"{self.entity_vector_id_prefix}_{entity_index + i}"})
                i = i + 1
            else:
                id_merged_entity_models.append(merged_entity_model)

        j = 1
        id_merged_text_models = []
        for merged_text_model in merged_text_models:
            if not merged_text_model["vector_id"]:
                id_merged_text_models.append({**merged_text_model, "vector_id": f"{self.text_vector_id_prefix}_{text_index + j}"})
                j = j + 1
            else:
                id_merged_text_models.append(merged_text_model)

        processed_entities = [
            {**entity, "chunk_ids": [text["vector_id"] for text in id_merged_text_models if text]} for entity in id_merged_entity_models
        ]

        processed_text = [{**text, "entity_ids": [entity["vector_id"] for entity in id_merged_entity_models]} for text in id_merged_text_models]

        return processed_entities, processed_text

    def _load_entity(self, text: str) -> Dict[str, Any]:
        return self.extractor.extract_entity(text)
