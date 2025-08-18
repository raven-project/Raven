import re
from typing import Any

from bs4 import BeautifulSoup


class HTMLProcessor:
    def _load_html(self, file_obj: Any) -> str:
        """
        从文件对象加载HTML并去噪，返回纯文本内容

        参数:
            file_obj: 包含HTML内容的文件对象

        返回:
            str: 清理后的纯文本内容
        """
        # 读取HTML内容
        html_content = file_obj.read()

        # 常见噪声元素的class/id正则模式
        noise_patterns = [
            r"ad(s|vertisement)?",
            r"banner",
            r"navbar",
            r"footer",
            r"sidebar",
            r"menu",
            r"comment",
            r"widget",
            r"related",
            r"share",
            r"popup",
            r"modal",
            r"cookie",
            r"login",
            r"signup",
            r"subscribe",
            r"promo",
            r"sponsor",
            r"tracking",
        ]

        # 需要直接移除的标签
        remove_tags = ["script", "style", "iframe", "noscript", "svg", "img", "form"]

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. 移除噪声标签
        for tag in remove_tags:
            for element in soup.find_all(tag):
                element.decompose()

        # 2. 移除匹配噪声模式的元素
        for pattern in noise_patterns:
            # 按class移除
            for element in soup.find_all(class_=re.compile(pattern, re.I)):
                element.decompose()
            # 按id移除
            for element in soup.find_all(id=re.compile(pattern, re.I)):
                element.decompose()

        # 3. 获取纯文本并清理
        text = soup.get_text("\n", strip=True)

        # 4. 移除多余空行和首尾空白
        clean_text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return clean_text


# 使用示例
if __name__ == "__main__":
    # 模拟文件对象
    from io import StringIO

    example_html = """
    <html>
    <head><title>测试页面</title></head>
    <body>
        <div class="header navbar">导航栏内容</div>
        <div id="ad-banner">广告内容</div>
        <script>alert('测试');</script>
        <style>body {color: red;}</style>

        <article>
            <h1>真正的文章标题</h1>
            <p>这是有用的正文内容第一段。</p>
            <p>这是第二段重要内容。</p>
            <div class="related-articles">相关文章推荐</div>
        </article>

        <footer>页脚内容 © 2023</footer>
    </body>
    </html>
    """

    file_obj = StringIO(example_html)
    processor = HTMLProcessor()
    clean_text = processor._load_html(file_obj)
    print("清理后的纯文本:\n", clean_text)
