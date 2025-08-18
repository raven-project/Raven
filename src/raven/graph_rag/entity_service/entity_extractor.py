import json
import os
import re
from typing import Any, Dict, List

from jinja2 import Template

from raven.graph_rag.llm_service.llm_client import LLMClient


class EntityExtractor:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def extract_entity(self, text: str) -> Dict[str, Any]:
        prompt = self._load_prompt(text, source="template/entity.prompt")
        result = self.llm_client.quick_chat(prompt)
        re = self._parse_entities_relations(result=result)
        return re

    def extract_query_entity(self, text: str) -> Dict[str, Any]:
        prompt = self._load_prompt(text, source="template/query_entity.prompt")
        result = self.llm_client.quick_chat(prompt)
        re = self._parse_query_entities(result=result)
        return re

    def extract_query_text(self, text: str) -> List[Dict[str, Any]]:
        prompt = self._load_prompt(text, source="template/query_text.prompt")
        result = self.llm_client.quick_chat(prompt)
        re = self._parse_text(result=result, pattern=r"资料: \[(.*?)\]；\[(.*?)\]")
        return re

    def load_prompt(self, text: str, source: str, **kwargs: Any) -> Any:
        return self._load_prompt(text, source, **kwargs)

    def _load_prompt(self, text: str, source: str, **kwargs: Any) -> Any:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 当前脚本的目录
        file_path = os.path.join(BASE_DIR, source)
        # 1. 从文件中读取模板内容
        with open(file_path, "r", encoding="utf-8") as f:
            template_str = f.read()

        jinja_ctl = Template(template_str)
        prompt = jinja_ctl.render(text=text, **kwargs)
        return prompt

    def render_template(self, template: str, **kwargs: Any) -> Any:
        jinja_ctl = Template(template)
        prompt = jinja_ctl.render(kwargs)
        return prompt

    def _parse_text(self, result: str, pattern: str) -> List[Dict[str, Any]]:
        results = result.splitlines()
        texts = []
        for text in results:
            for match in re.finditer(pattern, text):
                types_str, tags_str = match.groups()
                texts.append({"type": [t.strip() for t in types_str.split(",") if t], "tags": [t.strip() for t in tags_str.split(",") if t]})
        return texts

    def _parse_entities(self, result: str, pattern: str) -> List[Dict[str, Any]]:
        entities = []
        for text in result.splitlines():
            for match in re.finditer(pattern, text):
                name, alias_str, entity_type, tags_str = match.groups()
                entities.append(
                    {
                        "content": name.strip(),
                        "alias": [a.strip() for a in alias_str.split(",") if a],
                        "type": entity_type.strip(),
                        "tags": [t.strip() for t in tags_str.split(",") if t],
                    }
                )
        return entities

    def _parse_query_entities(self, result: str) -> Dict[str, Any]:
        entities = []
        for line in result.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if all(key in data for key in ["e", "t"]):
                    entities.append({"content": data["e"], "type": data["t"]})
            except json.JSONDecodeError:
                # Skip lines that aren't valid JSON
                continue
        return {"entities": entities}

    def _parse_entities_relations(self, result: str) -> Dict[str, Any]:
        entities = []
        relations = []

        # Split the result by lines and process each line
        for line in result.split("\n"):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)

                # Check for entity format
                if all(key in data for key in ["e", "desc", "t"]):
                    entities.append({"content": data["e"], "type": data["t"], "desc": data["desc"]})
                # Check for relation format
                elif all(key in data for key in ["x1", "r", "x2", "desc"]):
                    relations.append({"source": data["x1"], "relationship": data["r"], "target": data["x2"], "desc": data["desc"]})

            except json.JSONDecodeError:
                # Skip lines that aren't valid JSON
                continue

        return {"entities": entities, "relationships": relations}
