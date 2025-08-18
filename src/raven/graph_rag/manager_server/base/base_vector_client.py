from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class VectorStoreModel(BaseModel):
    vector_id: str
    content: str
    embedding: List[float]
    meta_data: Optional[Dict[str, Any]] = None
    created_time: Optional[int] = None
    updated_time: Optional[int] = None


class BaseVectorClient:
    def __init__(
        self,
        uri: str,
        dim: int,
        metric_type: str = "L2",
        index_type: str = "IVF_FLAT",
    ):
        self.uri = uri
        self.dim = dim
        self.metric_type = metric_type
        self.index_type = index_type

    def upsert(self, id_prefix: str, collection_name: str, vector_models: List[Dict[str, Any]]) -> None:
        raise NotImplementedError

    def delete(self, collection_name: str, ids: List[str]) -> None:
        raise NotImplementedError

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
        raise NotImplementedError

    def count(self, collections: List[str]) -> Dict[str, Any]:
        raise NotImplementedError

    def drop_collection(
        self,
        collection_name: str,
    ) -> bool:
        raise NotImplementedError

    def merge(self, collection_name: str, model: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        raise NotImplementedError
