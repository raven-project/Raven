import os
from typing import Optional, Tuple

# 扩展名 ↔ MIME 映射表（可扩展）
EXTENSION_MIME_MAP = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".zip": "application/zip",
    ".png": "image/png",
}

# 关键文件类型的文件头校验规则（替代 magic 库）
FILE_HEADER_RULES = {
    "application/pdf": b"%PDF-",  # PDF 文件头
    "application/zip": b"PK\x03\x04",  # ZIP 文件头
    "text/plain": lambda data: b"\x00" not in data[:100],  # 文本文件（前100字节无二进制空字节）
}


class DocumentLoader:
    def __init__(self, config_ini_path: str = "config.ini"):
        self.config_ini_path = config_ini_path
        self.max_file_size = self._load_max_file_size()

    def _load_max_file_size(self) -> int:
        """从 config.ini 加载最大文件大小"""
        try:
            with open(self.config_ini_path, "r") as f:
                for line in f:
                    if line.startswith("max_file_size"):
                        return int(line.split("=")[1].strip())
        except FileNotFoundError:
            print(f"[警告] 配置文件 {self.config_ini_path} 未找到，使用默认值 1024000（1MB）")
            return 1024000  # 默认 1MB
        return 1024000  # 兜底

    def _validate_file_header(self, file_path: str, expected_mime: str) -> bool:
        """手动校验文件头（替代 magic 库）"""
        try:
            with open(file_path, "rb") as f:
                header = f.read(10)  # 读取前10字节校验

                rule = FILE_HEADER_RULES.get(expected_mime)
                if not rule:
                    return True  # 无规则时默认通过

                # 处理固定字节或自定义函数规则
                if isinstance(rule, bytes):
                    return header.startswith(rule)
                elif callable(rule):
                    return bool(rule(header))
                return True
        except Exception as e:
            print(f"[错误] 文件头校验失败: {e}")
            return False

    def _get_extension_from_path(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """双重验证扩展名与文件类型（无 magic 依赖）"""
        ext = os.path.splitext(file_path)[1].lower()
        mime = EXTENSION_MIME_MAP.get(ext) if ext else None

        # 双重验证（有扩展名时）
        if ext and mime:
            if self._validate_file_header(file_path, mime):
                print(f"[调试] 双重验证通过：扩展名 {ext} → MIME {mime}")
                return ext, mime
            else:
                print(f"[警告] 双重验证失败：扩展名 {ext} 与文件头不匹配（期望 {mime}）")
                return ext, mime

        # 无扩展名时，尝试通过文件头推导
        if not ext:
            for candidate_mime, _rule in FILE_HEADER_RULES.items():
                if self._validate_file_header(file_path, candidate_mime):
                    # 反向查扩展名
                    for ext_map, mime_map in EXTENSION_MIME_MAP.items():
                        if mime_map == candidate_mime:
                            ext = ext_map
                            mime = candidate_mime
                            print(f"[调试] 无扩展名 → 推导 MIME {mime} → 扩展名 {ext}")
                            return ext, mime
            print("[警告] 无扩展名且无法推导类型")
            return None, None

        return ext, mime

    def _check_file_size(self, file_path: str) -> bool:
        """检查文件大小是否符合配置"""
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                print(f"[错误] 文件 {file_path} 大小 {file_size}B 超过限制 {self.max_file_size}B")
                return False
            print(f"[调试] 文件 {file_path} 大小 {file_size}B 符合限制")
            return True
        except FileNotFoundError:
            print(f"[错误] 文件 {file_path} 不存在")
            return False

    def load_text_from_file(self, file_path: str) -> Optional[str]:
        """完整加载文件流程：类型验证 → 大小检查 → 内容读取"""
        ext, mime = self._get_extension_from_path(file_path)
        if not ext and not mime:
            print(f"[错误] 文件 {file_path} 类型识别失败")
            return None

        if not self._check_file_size(file_path):
            return None

        if mime == "text/plain":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                print(f"[调试] 成功加载文本内容：\n{content}")
                return content
            except Exception as e:
                print(f"[错误] 加载文本失败: {e}")
                return None
        else:
            print(f"[警告] 不支持的类型 {mime}，无法加载文本")
            return None


# 直接运行示例（可选，方便快速测试）
if __name__ == "__main__":
    # 初始化加载器（使用默认 config.ini）
    loader = DocumentLoader()

    # 测试文件路径（确保 test_file.txt 存在，内容为测试文本）
    test_file_path = "test_file.txt"

    # 调用加载方法
    loader.load_text_from_file(test_file_path)
