import json
import os
from typing import Type, TypeVar, Union
import unittest

T = TypeVar("T")


class JsonFileHandler:
    def load_json_to_object(self, source: Union[str, bytes, os.PathLike], target_class: Type[T]) -> T:
        """Load JSON file content and convert to target class instance"""
        # 输出加载的文件名
        print(f"\nLoading JSON file: {source}")  # type: ignore
        try:
            if not os.path.exists(source):
                raise FileNotFoundError(f"File not found: {source}")  # type: ignore

            with open(source, "r", encoding="utf-8") as file:
                data = json.load(file)
                print(f"  File content: {data}")  # 输出文件内容

            if isinstance(data, dict):
                print(f"  Converting dictionary to {target_class.__name__}")
                return target_class(**data)
            elif isinstance(data, list) and issubclass(target_class, list):
                print(f"  Converting list to {target_class.__name__}")
                return target_class(data)  # type: ignore
            else:
                raise ValueError(f"Cannot convert JSON data to {target_class.__name__} type")

        except json.JSONDecodeError as e:
            print(f"  Error: Invalid JSON format - {e}")
            raise ValueError(f"JSON parsing error: {e}") from e
        except FileNotFoundError:
            print("Error: File not found")
            raise
        except Exception as e:
            print(f"  Error: Unexpected error - {e}")
            raise RuntimeError(f"Error loading JSON file: {e}") from e


class TestJsonFileProcessing(unittest.TestCase):
    # Test file paths
    TEST_DICT_FILE = "test_data_dict.json"
    TEST_LIST_FILE = "test_data_list.json"
    TEST_INVALID_FILE = "test_data_invalid.json"

    def setUp(self) -> None:
        print("\n===== Setting up test environment =====")
        self.handler = JsonFileHandler()
        self._create_test_files()  # Generate export files
        print("Test files created successfully.")

    def _create_test_files(self) -> None:
        """Create test JSON files (exported files)"""
        # 1. Valid dictionary JSON
        with open(self.TEST_DICT_FILE, "w", encoding="utf-8") as f:
            user_data = {"username": "john_doe", "email": "john@example.com", "age": 32, "is_active": True, "roles": ["admin", "editor"]}
            json.dump(user_data, f, indent=2)
            print(f"Created {self.TEST_DICT_FILE}")

        # 2. Valid list JSON
        with open(self.TEST_LIST_FILE, "w", encoding="utf-8") as f:
            skills = ["Python", "JSON", "unittest", "file handling"]
            json.dump(skills, f, indent=2)
            print(f"Created {self.TEST_LIST_FILE}")

        # 3. Invalid format JSON
        with open(self.TEST_INVALID_FILE, "w", encoding="utf-8") as f:
            invalid_content = '{name: "Invalid", age: 30, email: invalid@example.com}'
            f.write(invalid_content)
            print(f"Created {self.TEST_INVALID_FILE} (invalid format)")

    def tearDown(self) -> None:
        print("\n===== Cleaning up test environment =====")
        # Keep files by commenting out this section if needed
        for file in [self.TEST_DICT_FILE, self.TEST_LIST_FILE, self.TEST_INVALID_FILE]:
            if os.path.exists(file):
                os.remove(file)
                print(f"Removed {file}")
        print("Cleanup completed.")

    def test_valid_dict_conversion(self) -> None:
        print("\n=== Testing valid dictionary conversion ===")

        class UserProfile:
            def __init__(self, username: str, email: str, age: int, is_active: bool, roles: list):
                self.username = username
                self.email = email
                self.age = age
                self.is_active = is_active
                self.roles = roles

        profile = self.handler.load_json_to_object(self.TEST_DICT_FILE, UserProfile)

        print(f"  Converted object: {vars(profile)}")
        self.assertEqual(profile.username, "john_doe")
        self.assertEqual(profile.email, "john@example.com")
        self.assertEqual(profile.age, 32)
        self.assertEqual(profile.is_active, True)
        self.assertEqual(profile.roles, ["admin", "editor"])
        print("  Dictionary conversion test passed.")

    def test_valid_list_conversion(self) -> None:
        print("\n=== Testing valid list conversion ===")
        items = self.handler.load_json_to_object(self.TEST_LIST_FILE, list)

        print(f"  Converted list: {items}")
        self.assertEqual(items, ["Python", "JSON", "unittest", "file handling"])
        self.assertIsInstance(items, list)
        print("  List conversion test passed.")

    def test_missing_file_handling(self) -> None:
        print("\n=== Testing missing file handling ===")
        with self.assertRaises(FileNotFoundError) as context:
            self.handler.load_json_to_object("non_existent_file.json", dict)

        error_msg = str(context.exception)
        print(f"  Expected error: {error_msg}")
        self.assertIn("File not found", error_msg)
        print("  Missing file test passed.")

    def test_invalid_json_handling(self) -> None:
        print("\n=== Testing invalid JSON handling ===")
        with self.assertRaises(ValueError) as context:
            self.handler.load_json_to_object(self.TEST_INVALID_FILE, dict)

        error_msg = str(context.exception)
        print(f"  Expected error: {error_msg}")
        self.assertIn("JSON parsing error", error_msg)
        print("  Invalid JSON test passed.")


if __name__ == "__main__":
    unittest.main()
