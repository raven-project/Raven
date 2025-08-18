from typing import Any, Dict, List, Optional

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

from raven.graph_rag.manager_server.base.base_vector_client import BaseVectorClient


class MilvusClient(BaseVectorClient):
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        collection_names: List[str],
        dim: int,
        chunk_dim: Optional[int] = None,
        index_type: str = "IVF_FLAT",
        metric_type: str = "L2",
    ):
        """
        Initialize Milvus client and create collection if not exists.

        :param uri: Milvus server URI (e.g. "http://localhost:19530")
        :param collection_name: Name of the collection to operate
        :param dim: Dimension of entity embeddings
        :param chunk_dim: Dimension of chunk text embeddings (default to entity dim)
        :param index_type: Index type for vector search
        :param metric_type: Distance metric type (e.g., L2, IP, COSINE)
        """
        super().__init__(
            uri=uri,
            dim=dim,
            index_type=index_type,
            metric_type=metric_type,
        )
        self.collections = {}
        self.dim = dim
        self.chunk_dim = chunk_dim if chunk_dim is not None else dim
        # Connect to Milvus
        connections.connect(alias="default", user=user, password=password, uri=uri)

        # Define schema fields
        fields = [
            FieldSchema(name="vector_id", is_primary=True, dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=10000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
        ]
        schema = CollectionSchema(fields, enable_dynamic_field=True, description="RAG vector store for entities")

        for namespace in collection_names:
            # Create collection if not exists
            collection = None
            if not utility.has_collection(namespace):
                collection = Collection(name=namespace, schema=schema)
                collection.create_index(
                    field_name="embedding", index_params={"index_type": index_type, "metric_type": metric_type, "params": {"nlist": 128}}
                )
            else:
                collection = Collection(name=namespace)
            self.collections[namespace] = collection
            collection.load()

    # Insert entity embeddings and metadata
    def upsert(self, id_prefix: str, collection_name: str, vector_models: List[Dict[str, Any]]) -> None:
        """
        Insert Or Update  into the collection.
        """
        collection = self.collections[collection_name]

        # 构造每列数据
        entities = [
            {
                **(entity or {}),
                "vector_id": f"{id_prefix}_{self.count([collection_name]).get(collection_name)}"
                if not entity.get("vector_id")
                else entity["vector_id"],
                "content": entity["content"],
                "embedding": entity["embedding"],
            }
            for entity in vector_models
        ]

        if len(entities) > 0:
            # 插入数据（upsert）
            collection.upsert(entities)
            collection.flush()

    # Delete by ID
    def delete(self, collection_name: str, ids: List[str]) -> None:
        """
        Delete entities by their primary key IDs.
        :param ids: entity_id list
        :return:
        """
        collection = self.collections[collection_name]
        # 构造删除表达式
        id_str = ", ".join([f'"{vid}"' for vid in ids])
        expr = f"vector_id in ({id_str})"
        collection.delete(expr)
        collection.flush()

    # Vector similarity search (by entity embedding)
    def query(
        self,
        collection_name: str,
        embedding: Optional[List[float]] = None,
        top_k: int = 5,
        filter_expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        search_params: Optional[Dict] = None,
        timeout: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search with enhanced control.

        Args:
            vector_model: Query Model.
            top_k: Number of results to return.
            filter_expr: Milvus filter expression (e.g., "type == 'entity'").
            output_fields: Fields to return (None returns all).
            search_params: Index-specific params (e.g., {"nprobe": 16} for IVF_FLAT).
            timeout: Query timeout in seconds.

        Returns:
            List of results, each as a dict with requested fields.
        """
        collection = self.collections[collection_name]

        # 设置默认查询参数
        if search_params is None:
            search_params = {"metric_type": self.metric_type, "params": {"nprobe": 16}}

        if not embedding:
            results: List[Dict[str, Any]] = collection.query(
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=output_fields,
                timeout=timeout,
            )
            return results

        else:
            # 调用 Milvus 查询
            results = collection.search(
                data=[embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=output_fields,
                timeout=timeout,
            )

            # 解析结果
            matched_models = []
            for hits in results:
                for hit in hits:
                    fields = hit.entity.to_dict()  # type: ignore
                    matched_models.append({**fields["entity"]})

            return matched_models

    def merge(
        self,
        collection_name: str,
        model: Dict[str, Any],
        fields: List[str],
    ) -> Dict[str, Any]:
        models = self.query(collection_name=collection_name, filter_expr=f"hash == '{model.get('hash')}'", top_k=1, output_fields=fields)
        if len(models) == 1:
            merged_model = self._merge_meta_data(models[0], model)
            # merge desc
            return merged_model
        else:
            return model

    def _merge_meta_data(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        if dict1 is None:
            return dict2

        if dict2 is None:
            return dict1

        result = {}

        keys = set(dict1.keys()) | set(dict2.keys())
        for key in keys:
            val1 = dict1.get(key)
            val2 = dict2.get(key)

            if key in dict1 and key in dict2:
                if not val1:
                    result[key] = val2
                if not val2:
                    result[key] = val1
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

    def count(self, collections: List[str]) -> Dict[str, Any]:
        return {collection_name: self.collections[collection_name].num_entities for collection_name in collections}

    def drop_collection(
        self,
        collection_name: str,
    ) -> Any:
        """
        Drop the entire collection.
        """
        return self.collections[collection_name].drop()
