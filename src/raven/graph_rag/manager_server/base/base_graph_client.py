from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SubgraphResult(BaseModel):
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]


class BaseGraphClient:
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database

    def close(self) -> None:
        """close client"""
        raise NotImplementedError

    def upsert_entity(self, entity: Dict[str, Any]) -> bool:
        raise NotImplementedError

    def get_entity_batch(self, workspace: str, entity_ids: List[str]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def query_entity(
        self,
        entity_type: Optional[str] = None,
        conditions: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        node_alias: str = "e",
        top_k: int = 1,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def delete_entity(self, workspace: str, entity_ids: List[str]) -> bool:
        raise NotImplementedError

    def upsert_relationship(self, relationship: Dict[str, Any]) -> None:
        raise NotImplementedError

    def delete_relationship(self, workspace: str, node_ids: List[Dict[str, str]]) -> bool:
        raise NotImplementedError

    def get_relationship(self, workspace: str, source_id: str, target_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def merge_entities(self, source: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def merge_relationship(self, source: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def find(
        self,
        node_id: str,
        max_depth: int,
        max_nodes: int,
        node_alias: str = "e",
        conditions: Optional[str] = None,
    ) -> SubgraphResult | None:
        raise NotImplementedError

    def build_prompt(self, graph: Optional[SubgraphResult] = None) -> str:
        raise NotImplementedError
