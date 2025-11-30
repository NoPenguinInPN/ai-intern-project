import os
import requests
import logging

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, chat_url=None, embed_url=None, api_key=None, timeout=60):
        # 可以从环境变量或参数传入
        self.chat_url = chat_url or os.getenv("CHAT_API_URL")
        self.embed_url = embed_url or os.getenv("EMBED_API_URL")
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        else:
            key = os.getenv("MODEL_API_KEY")
            if key:
                self.headers["Authorization"] = f"Bearer {key}"
        self.timeout = timeout

    def call_chat(self, messages, model, temperature=0.1, stream=False):
        """
        调用大模型 Chat Completions API
        messages: list of {"role": "...", "content": "..."}
        model: 模型名，如 "tclf90/qwen3-32b-gptq-int8"
        返回 JSON 结构（requests 返回的 .json()）
        """
        if not self.chat_url:
            raise ValueError("CHAT_API_URL 未配置")
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        try:
            resp = requests.post(self.chat_url, headers=self.headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("call_chat 出错: %s", e)
            raise

    def call_embeddings(self, inputs, model):
        """
        调用 Embeddings API
        inputs: list of strings
        model: 嵌入模型名，如 "Xorbits/bge-m3"
        返回 JSON 结构
        """
        if not self.embed_url:
            raise ValueError("EMBED_API_URL 未配置")
        payload = {
            "model": model,
            "input": inputs
        }
        try:
            resp = requests.post(self.embed_url, headers=self.headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("call_embeddings 出错: %s", e)
            raise