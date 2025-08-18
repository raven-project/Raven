import logging
from typing import Any, Dict, List, Optional

from neo4j import Driver, GraphDatabase

from raven.graph_rag.manager_server.base.base_graph_client import BaseGraphClient, SubgraphResult

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Neo4jClient")


class Neo4jClient(BaseGraphClient):
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """
        init Neo4j Client

        :param uri: Neo4j  URI (e.g., "bolt://localhost:7687")
        :param username:
        :param password:
        :param database:  ( "neo4j")
        """
        super().__init__(uri=uri, username=username, password=password, database=database)
        self.driver: Driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        self.create_database_if_not_exists(db_name=database)
        logger.info(f"Neo4j client initialized for database: {self.database}")

    def create_database_if_not_exists(self, db_name: str) -> None:
        with self.driver.session(database="system") as session:
            result = session.run("SHOW DATABASES")
            db_names = [record["name"] for record in result]
            if db_name not in db_names:
                session.run(f"CREATE DATABASE {db_name}")
                logger.info(f"Database '{db_name}' created.")
            else:
                logger.info(f"Database '{db_name}' already exists.")

    def upsert_entity(self, entity: Dict[str, Any]) -> bool:
        cypher = f"""
        MERGE (e:{entity["type"]}{{id: $id}})
        SET e += $properties
        """
        try:
            with self.driver.session(database=self.database) as session:
                session.run(cypher, id=entity["id"], properties=entity)
            return True
        except Exception as e:
            logger.error(f"Upsert Entity Failed: {e}")
            return False

    # def get_entity_batch(self, workspace: str, entity_ids: List[str]) -> List[Dict[str,Any]]:
    #     cypher = f"""
    #     MATCH (e:{workspace})
    #     WHERE e.id IN $ids
    #     RETURN e
    #     """
    #     try:
    #         with self.driver.session(database=self.database) as session:
    #             result = session.run(cypher, ids=entity_ids)
    #             return [
    #                 Entity(
    #                     id=record["e"]["id"],
    #                     name=record["e"].get("name", ""),
    #                     meta_data=record["e"].get("meta_data", {})
    #                 )
    #                 for record in result
    #             ]
    #     except Exception as e:
    #         logger.error(f"Get Entity Batch Failed: {e}")
    #         return []

    def query_entity(
        self,
        entity_type: Optional[str] = None,
        conditions: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        node_alias: str = "e",
        top_k: int = 1,
    ) -> List[Dict[str, Any]]:
        expr = ""
        if conditions:
            expr += f"where {conditions}"

        entity_type_label = ""
        if entity_type:
            entity_type_label = f":{entity_type}"

        cypher = f"""
            MATCH ({node_alias}{entity_type_label})
            {expr}
            RETURN {node_alias}
            LIMIT {top_k}
        """
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher, parameters=params)
                entities = []
                for record in result:
                    node = dict(record[f"{node_alias}"])
                    entities.append(node)
                return entities
        except Exception as e:
            logger.error(f"Query Entity Failed: {e}")
            return []

    #
    # def delete_entity(self, workspace: str, entity_ids: List[str]) -> bool:
    #     cypher = f"""
    #     UNWIND $ids AS eid
    #     MATCH (e:{workspace} {{id: eid}})
    #     DETACH DELETE e
    #     """
    #     try:
    #         with self.driver.session(database=self.database) as session:
    #             session.run(cypher, ids=entity_ids)
    #         return True
    #     except Exception as e:
    #         logger.error(f"Delete Entity Failed: {e}")
    #         return False

    def upsert_relationship(self, relationship: Dict[str, Any]) -> None:
        cypher = f"""
            MATCH (s {{id: $source_id}})
            MATCH (t {{id: $target_id}})
            MERGE (s)-[r: `{relationship["relation"]}` ]->(t)
            SET r.id =$id,r.desc=$desc
            """
        try:
            with self.driver.session(database=self.database) as session:
                session.run(cypher, parameters=relationship)
        except Exception as e:
            logger.error(f"Upsert Relationship Failed: {e}")
            raise

    # def delete_relationship(self, workspace: str, node_ids: List[Dict[str, str]]) -> bool:
    #     if not node_ids:
    #         return True
    #
    #     cypher = f"""
    #     UNWIND $pairs AS pair
    #     MATCH (a:{workspace} {id: pair.source_id})-[r]-(b:Entity {id: pair.target_id})
    #     DELETE r
    #     """
    #     try:
    #         with self.driver.session(database=self.database) as session:
    #             session.run(cypher, pairs=node_ids)
    #         return True
    #     except Exception as e:
    #         logger.error(f"Delete Relationship Failed: {e}")
    #         raise

    # def get_relationship(self, workspace: str, source_id: str, target_id: str) -> RelationShip:
    #     cypher = f"""
    #     MATCH (a:{workspace} {{id: $source_id}})-[r]->(b:{workspace} {{id: $target_id}})
    #     RETURN r
    #     LIMIT 1
    #     """
    #     try:
    #         with self.driver.session(database=self.database) as session:
    #             result = session.run(cypher, source_id=source_id, target_id=target_id)
    #             record = result.single()
    #             if record:
    #                 return RelationShip(
    #                     id=record["r"].id,
    #                     relation=record["r"]["relation"],
    #                     source_id=source_id,
    #                     target_id=target_id
    #                 )
    #     except Exception as e:
    #         logger.error(f"Get Relationship Failed: {e}")
    #         raise

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

    def merge_entities(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        merge entity(meta_data etc.)
        """
        entities = self.query_entity(entity_type=source["type"], conditions=f"e.id='{source['id']}'")

        if entities:
            entity = entities[0]
            merged_entity = self._merge_meta_data(dict1=entity, dict2=source)
            return merged_entity
        return source

    def merge_relationship(self, source: Dict[str, Any]) -> Dict[str, Any]:
        relationships = self.query_relationship(source_id=source["source_id"], target_id=source["target_id"], relation=source["relation"])
        if relationships:
            relationship = relationships[0]

            if relationship["desc"]:
                relationship["desc"] = list(set(relationship["desc"] + source["desc"]))
            return relationship
        else:
            return source

    def query_relationship(self, source_id: str, target_id: str, relation: str) -> List[Dict[str, Any]] | None:
        exist_cypher = f"""
            CALL db.relationshipTypes()
            YIELD relationshipType
            WHERE relationshipType = '{relation}'
            RETURN COUNT(*) > 0 AS exists
            """

        cypher = f"""
        MATCH (source)-[r:`{relation}`]->(target)
        WHERE source.id = $source_id AND target.id = $target_id
        RETURN r
        """
        with self.driver.session(database=self.database) as session:
            exist_result = session.run(exist_cypher)
            exist = exist_result.single()
            if exist and not exist["exists"]:
                return None

            result = session.run(cypher, source_id=source_id, target_id=target_id)
            relationships = []
            for record in result:
                rel = record["r"]
                relationships.append({"id": rel["id"], "source_id": source_id, "relation": rel.type, "target_id": target_id, "desc": rel["desc"]})
            return relationships

    def find(
        self,
        node_id: str,
        max_depth: int = 10,
        max_nodes: int = 10,
        node_alias: str = "e",
        conditions: Optional[str] = None,
    ) -> SubgraphResult | None:
        """
        查找子图

        :param node_id: 实体ID
        :param max_depth: 最大遍历深度
        :param max_nodes: 返回的最大节点数
        :param conditions: 额外的Cypher条件表达式
        :return: 包含节点和关系的子图结果
        """
        # 参数验证
        if max_depth <= 0 or max_nodes <= 0:
            raise ValueError("max_depth和max_nodes必须大于0")

        if not node_id:
            raise ValueError("must node_id")

        # 构建查询参数
        params = {"entity_id": node_id}

        # 构建WHERE条件

        where_clause = f"{node_alias}.id = $entity_id"

        if conditions:
            where_clause += conditions

        # 优化后的Cypher查询
        cypher = f"""
            MATCH ({node_alias})
            WHERE {where_clause}
            OPTIONAL MATCH path=({node_alias})-[*..{max_depth}]->(m)
            WITH e, collect(DISTINCT m) AS other_nodes,
                 apoc.coll.toSet(apoc.coll.flatten(collect(relationships(path)))) AS all_rels
            WITH apoc.coll.toSet(other_nodes + [e]) AS nodes, all_rels
            RETURN coalesce(nodes, []) AS nodes,
                   [r IN all_rels WHERE r IS NOT NULL |
                    {{
                        source: startNode(r).id,
                        target: endNode(r).id,
                        desc: r.desc,
                        relation: type(r),
                        id: elementId(r)
                    }}] AS relationships

        """

        try:
            with self.driver.session(database=self.database) as session:
                record = session.run(cypher, parameters=params).single()

            if not record:
                return None

            # 处理节点结果
            entities = [node for node in record["nodes"]]
            # 处理关系结果
            relationships = [rel for rel in record["relationships"]]

            return SubgraphResult(entities=entities, relationships=relationships)

        except Exception as e:
            logger.error(f"查找子图失败: {str(e)}\n查询语句: {cypher}")
            raise

    def build_prompt(self, graph: Optional[SubgraphResult] = None) -> str:
        context = []
        if graph:
            entities = {entity["id"]: entity for entity in graph.entities}
            relationships = graph.relationships
            exist_relationship_entity_ids = []
            for relationship in relationships:
                source = entities.get(relationship["source"])
                target = entities.get(relationship["target"])
                if source:
                    exist_relationship_entity_ids.append(relationship["source"])
                if target:
                    exist_relationship_entity_ids.append(relationship["target"])
                if source and target:
                    prompt = f"""
                    实体和关系组描述:
                        {source["name"]}->{relationship["relation"]}->{target["name"]},
                        {source["name"]}:{";".join(source["desc"])}
                        {target["name"]}:{";".join(target["desc"])}
                        {relationship["relation"]}:{";".join(relationship["desc"])}
                    """
                    context.append(prompt)

            # get not exist relation entity
            for entity in graph.entities:
                if entity["id"] not in exist_relationship_entity_ids:
                    prompt = f"""
                    单独实体描述:
                        {entity["name"]}:{";".join(entity["desc"])}
                    """
                    context.append(prompt)

        return "\n".join(context)
