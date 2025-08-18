from typing import Any, List, Optional

from openai import OpenAI
import requests


class LLMClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 1024,
        embedding_model: str = "text-embedding-3-small",
        dimensions: int = 256,
        rerank_model: str = "",
        timeout: float = 60.0,
        **keywords: Any,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        self.model = model
        self.embedding_model = embedding_model
        self.dimensions = dimensions
        self.rerank_mode = rerank_model
        self.default_params = {
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
        self.default_params.update(keywords)

    def quick_chat(self, query: str, stream: bool = False) -> Any:
        return self.chat_completion(messages=[{"role": "user", "content": query}], stream=stream)

    def chat_completion(self, messages: list, stream: bool = False) -> Any:
        stream = stream if stream is not None else self.default_params["stream"]
        payload = {"model": self.model, "messages": messages, "stream": stream, **self.default_params}

        # remove None value（OpenAI API not accept null）
        payload = {k: v for k, v in payload.items() if v is not None}
        if stream:
            return self._stream_chat(pyload=payload)

        else:
            # response all
            response = self.client.chat.completions.create(**payload)  # type: ignore
            return response.choices[0].message.content
    
    def _stream_chat(self, pyload) -> Any:
        # stream out
        response = self.client.chat.completions.create(**payload)  # type: ignore
        for chunk in response:
            delta = chunk.choices[0].delta
            yield delta.content or ""

    def embed(self, text: str) -> List[float]:
        response = self.client.embeddings.create(model=self.embedding_model, input=text, dimensions=self.dimensions)
        content: List[float] = response.data[0].embedding
        return content

    def rerank(self, query: str, documents: Optional[List] = None) -> Any:
        if documents is None:
            documents = []
        payload = {"model": self.rerank_mode, "query": query, "documents": documents}
        headers = {"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"}
        url = self.base_url + "rerank"
        response = requests.request("POST", url=url, json=payload, headers=headers)
        print(f"Rerank response: {response}")
        return response.json()
