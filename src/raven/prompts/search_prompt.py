prompt_call_tool = """
你即将调用一个搜索工具来完成任务。请根据以下任务内容，合理构造输入参数。

任务内容：
{content}

请返回工具函数的名称和参数（如有），确保格式正确并与任务高度匹配。
"""


prompt_judge_online = """
请判断以下任务内容是否需要进行在线搜索。

任务内容：
{content}

返回：
- 若任务包含"web 搜索", "联网搜索", "在线搜索"等关键词，则返回 online_search
- 若任务未包含上述关键词，则返回 local_search
- 除非任务区中明确包含在线搜索的意思，否则不应选择 online_search, 应该选择 local_search
- 若任务与搜索无关，则返回 END

仅返回上述三个关键词之一，不添加其他内容。
"""

prompt_judge_local = """
请根据 local_search 返回内容判断是否需要进行在线搜索。

local_search 返回内容：
{content}

返回：
- 若local_search 返回内容显示相关内容未找到，则返回 online_search
- 若local_search 返回内容显示内容未已找到，则返回 summary
- 若任务与搜索无关，则返回 END

仅返回上述三个关键词之一，不添加其他内容。
"""


prompt_summary = """
以下是搜索工具返回的原始内容，请总结其中的关键信息。

原始结果：
{content}

请完成以下任务：
- 提炼出有价值的资产/漏洞/标签信息
- 如果搜索失败，请指出原因
- 用自然语言简洁表述结果，避免复制原始字段结构
"""
