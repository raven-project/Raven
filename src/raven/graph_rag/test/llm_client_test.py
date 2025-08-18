# import re

# from jinja2 import Template

import os

from dotenv import find_dotenv, load_dotenv

from raven.graph_rag.llm_service.llm_client import LLMClient

_ = load_dotenv(find_dotenv())
openai_api_key = os.getenv("openai_api_key", "EMPTY")
openai_api_base = os.getenv("openai_api_base", "http://localhost:8000/v1")

#
# # 1. 从文件中读取模板内容
# with open("../entity_service/tempalte/entity.prompt", "r", encoding="utf-8") as f:
#     template_str = f.read()
#
# jinja_ctl = Template(template_str)
#
# prompt = jinja_ctl.render(text="""东辰实验学校的声明也称，毕节梁才学校涉嫌虚假宣传。如2024年高考成绩查分后，第一天宣传600分以上有378人，第二天宣传有398人，第三天宣传有418人；2025年中考600分以上的，一开始宣传有74人，后又宣传88人。声明中指控毕节梁才学校声明中涉及该校的各类数据是为了不当竞争，故意捏造。
# 极目新闻记者查到两份声明的原文，一则名为《毕节梁才学校严正声明》，一则名为《毕节七星关东辰实验学校关于毕节梁才学校“严正声明”的声明》，两则声明后面都盖有学校的公章。
# 　　7月20日，极目新闻记者登录两所学校的官方账号，发现各自已经将声明撤销。随后，记者向毕节梁才学校咨询为何要撤销声明，一工作人员表示，经当地教育主管部门介入协调，两校已握手言和。记者又联系东辰实验学校，但无人接电话。""")
#
# print(prompt)
# llm = LLMClient(
#     api_key=openai_api_key,
#     base_url=openai_api_base,
#     model="Qwen/Qwen2.5-72B-Instruct"
# )
# def parse_entities_relations(text: str):
#     entity_pattern = r"实体: (.*?)（别名：\[(.*?)\]；类型：(.*?)；标签：\[(.*?)\]）"
#     relation_pattern = r"关系: (.*?) -(.+?)-> (.*)"
#
#     entities = []
#     relations = []
#
#     for match in re.finditer(entity_pattern, text):
#         name, alias_str, entity_type, tags_str = match.groups()
#         entities.append({
#             "name": name.strip(),
#             "alias": [a.strip() for a in alias_str.split(",") if a],
#             "type": entity_type.strip(),
#             "tags": [t.strip() for t in tags_str.split(",") if t]
#         })
#
#     for match in re.finditer(relation_pattern, text):
#         subj, pred, obj = match.groups()
#         relations.append({"subject": subj.strip(), "predicate": pred.strip(), "object": obj.strip()})
#
#     return entities, relations
#
# query = llm.quick_chat(query=prompt)
# print(query)
#
# d=parse_entities_relations(query)
#
# print(d)


# llm = LLMClient(
#     api_key=openai_api_key,
#     base_url=openai_api_base,
#     embedding_model="Qwen/Qwen3-Embedding-8B",
#     dimensions=4096,
# )
# import numpy as np
# print(np.array_equal(llm.embed("你好"),llm.embed("你好")))
#


llm = LLMClient(api_key=openai_api_key, base_url=openai_api_base, rerank_model="Qwen/Qwen3-Reranker-8B")

resp = llm.rerank("谁比较爱吃苹果？", ["牛顿和苹果", "乔布斯和苹果"])

a = resp["results"]

print(a)

print(a[0])

print(a[0]["index"])


# print(type(resp["results"].))
