import os
import unittest

from ..ingestion_service.document_loader import DocumentLoader


class TestDocumentLoader(unittest.TestCase):
    TEST_FILE = "test_file.txt"  # 带扩展名测试文件
    EMPTY_EXT_FILE = "test_no_ext"  # 无扩展名测试文件
    LARGE_FILE = "large_file.txt"  # 超大文件
    CONFIG_INI = "config.ini"  # 配置文件

    @classmethod
    def setUpClass(cls) -> None:
        """测试前置：创建测试文件"""
        # 创建普通文本文件
        with open(cls.TEST_FILE, "w", encoding="utf-8") as f:
            f.write("严格双重验证测试内容")

        # 创建无扩展名文件
        with open(cls.EMPTY_EXT_FILE, "w", encoding="utf-8") as f:
            f.write("无扩展名测试内容")

        # 创建超大文件（2MB，超过默认 1MB 限制）
        with open(cls.LARGE_FILE, "wb") as f:
            f.seek(2 * 1024 * 1024)  # 定位到 2MB 位置
            f.write(b"\0")  # 写空字节

        # 创建配置文件
        with open(cls.CONFIG_INI, "w") as f:
            f.write("max_file_size = 1024000\n")  # 1MB 限制

    @classmethod
    def tearDownClass(cls) -> None:
        """测试后置：清理文件"""
        for file in [cls.TEST_FILE, cls.EMPTY_EXT_FILE, cls.LARGE_FILE, cls.CONFIG_INI]:
            if os.path.exists(file):
                os.remove(file)

    def test_extension_validation(self) -> None:
        """测试扩展名与文件头双重验证"""
        loader = DocumentLoader(self.CONFIG_INI)

        # 带扩展名文件（.txt）
        ext, mime = loader._get_extension_from_path(self.TEST_FILE)
        self.assertEqual(ext, ".txt")
        self.assertEqual(mime, "text/plain")

        # 无扩展名文件
        ext, mime = loader._get_extension_from_path(self.EMPTY_EXT_FILE)
        self.assertEqual(ext, ".txt")
        self.assertEqual(mime, "text/plain")

    def test_file_size_check(self) -> None:
        """测试文件大小校验"""
        loader = DocumentLoader(self.CONFIG_INI)

        # 正常文件（<1MB）
        self.assertTrue(loader._check_file_size(self.TEST_FILE))

        # 超大文件（>1MB）
        self.assertFalse(loader._check_file_size(self.LARGE_FILE))

    def test_text_loading(self) -> None:
        """测试文本加载完整流程"""
        loader = DocumentLoader(self.CONFIG_INI)

        # 正常加载
        content = loader._load_text_from_file(self.TEST_FILE)
        self.assertEqual(content, "严格双重验证测试内容")

        # 无扩展名加载
        content = loader._load_text_from_file(self.EMPTY_EXT_FILE)
        self.assertEqual(content, "无扩展名测试内容")

        # 超大文件加载（预期失败）
        content = loader._load_text_from_file(self.LARGE_FILE)
        self.assertEqual(content, None)


if __name__ == "__main__":
    unittest.main()
