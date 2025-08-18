import json
import logging
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter


class TextChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 200):
        """
        Initialize the document processor with chunking parameters.

        :param chunk_size: Character length of each text chunk
        :param overlap: Overlapping characters between adjacent chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> list[str]:
        """
        Split text into chunks using sliding window approach.
        using langchain
        :param text: Input text to chunk
        :return: List of text chunks
        """
        # do json
        try:
            json_text = json.loads(text)
            if isinstance(json_text, dict):
                json_text = [json_text]
            new_json_item = []
            for item in json_text:
                over_size_value = {**item}
                # 找出最大可分割的values数组长度1
                max_size = 1
                for key, value in item.items():
                    if isinstance(value, str) and len(value) > self.chunk_size:
                        values = self._chunk_text(text=value)
                        over_size_value[key] = values
                        if len(values) >= max_size:
                            max_size = len(values)
                item_json = []
                for i in range(max_size):
                    new_item = {**over_size_value}
                    for key, value in over_size_value.items():
                        if isinstance(value, list):
                            index = i
                            if index < len(value):
                                new_item[key] = value[index]
                            else:
                                new_item[key] = value[len(value) - 1]

                    item_json.append(new_item)
                new_json_item.extend(item_json)
            texts = []
            for item in new_json_item:
                s = ""
                for k, v in item.items():
                    s += f"{k}:{v}\n"
                texts.append(s)
            return texts
        except Exception:
            logging.info("not json loading text")
        try:
            return self._chunk_text(text=text)
        # report error1
        except Exception as e:
            raise RuntimeError(f"An error occurred while chunking text: {str(e)}") from e

    def _chunk_text(self, text: str) -> List[str]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap,
            separators=[
                ".\n",
                "!\n",
                "?\n",
                ". ",
                "! ",
                "? ",
                "！\n",
                "？\n",
                "。\n",
                "！\n",
                "？\n",
                "\n",
                "\r\n",
                "，",
                "？",
                "！",
                "。",
                " ",
                "",
                ", ",
            ],
        )
        chunks: List[str] = text_splitter.split_text(text)
        return chunks
