import re


class MarkdownProcessor:
    def _load_markdown(self, md_content: str) -> str:
        """
        移除所有Markdown语法符号，返回纯文本

        参数:
            md_content (str): 包含Markdown格式的文本

        返回:
            str: 完全去除Markdown标记的纯文本
        """
        # Markdown转换规则列表
        transformations = [
            (r"^#+\s*(.*?)\s*$", r"\1"),  # 标题
            (r"\[([^\]]+)\]\([^\)]+\)", r"\1"),  # 链接
            (r"!\[([^\]]*)\]\([^\)]+\)", r"\1"),  # 图片
            (r"`([^`]+)`", r"\1"),  # 内联代码
            (r"```.*?\n(.*?)```", r"\1"),  # 代码块（多行）
            (r"(\*\*|__)(.*?)\1", r"\2"),  # 加粗
            (r"(\*|_)(.*?)\1", r"\2"),  # 斜体
            (r"~~(.*?)~~", r"\1"),  # 删除线
            (r"^[\s]*[-*+]\s+", ""),  # 无序列表
            (r"^[\s]*\d+\.\s+", ""),  # 有序列表
            (r"^>\s*", ""),  # 引用
            (r"\|([^\|]+)\|", r"\1"),  # 表格单元格
            (r"^[-:|]+\s*$", ""),  # 表格分隔线
            (r"<[^>]+>", ""),  # HTML标签
            (r"\n{3,}", "\n\n"),  # 多个空行合并
            (r"[ \t]{2,}", " "),  # 多个空格合并1
        ]

        text = md_content
        for pattern, replacement in transformations:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.DOTALL)

        return text.strip()


# 使用示例
if __name__ == "__main__":
    processor = MarkdownProcessor()

    markdown_text = """
    # 标题

    **加粗** 和 *斜体* 文字

    [链接文本](https://example.com)

    - 列表项1
    - 列表项2

    > 引用内容

    `代码片段` 和 ```多行代码块```
    """

    clean_text = processor._load_markdown(markdown_text)
    print("\n处理后纯文本:\n", clean_text)
