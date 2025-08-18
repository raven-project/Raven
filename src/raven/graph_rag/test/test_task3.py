import os
import sys
import unittest

# 添加上级目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用相对导入
from ..ingestion_service.document_loader import DocumentLoader


class TestDocumentLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = DocumentLoader()

    def test_get_extension_from_url(self) -> None:
        urls = [
            ("http://example.com/file.pdf?token=123", "pdf"),
            ("http://example.com/malicious.exe.pdf", "pdf"),
            ("http://example.com/noextension", ""),
            ("http://example.com/invalid.docx.html", "html"),
            ("http://example.com/unknown.format", ""),
        ]
        for url, expected in urls:
            result = self.loader._get_extension_from_url(url)
            self.assertEqual(result, expected)

    def test_load_plain_text(self) -> None:
        # 创建一个测试文本文件
        with open("test.txt", "w", encoding="utf-8") as f:
            f.write("这是一个测试文本。")

        # 读取测试文本文件
        with open("test.txt", "rb") as f:
            result = self.loader._load_plain_text(f)
            self.assertEqual(result, "这是一个测试文本。")


if __name__ == "__main__":
    unittest.main()
