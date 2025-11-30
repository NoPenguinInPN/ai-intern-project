import os
import json
import logging
from src.api_client import APIClient


# 基本日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("无法加载 config.json: %s", e)
        return {}

# 读取 config.json 或环境变量
cfg = load_config()
CHAT_API_URL = os.getenv("CHAT_API_URL", cfg.get("CHAT_API_URL"))
EMBED_API_URL = os.getenv("EMBED_API_URL", cfg.get("EMBED_API_URL"))
API_KEY = os.getenv("MODEL_API_KEY", cfg.get("MODEL_API_KEY"))

client = APIClient(chat_url=CHAT_API_URL, embed_url=EMBED_API_URL, api_key=API_KEY)

if __name__ == "__main__":
    # 示例：调用 chat 接口
    try:
        messages = [{"role": "user", "content": "你是什么模型"}]
        res = client.call_chat(messages=messages, model="tclf90/qwen3-32b-gptq-int8", temperature=0.1, stream=False)
        print("Chat 返回：", json.dumps(res, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.error("调用 chat 接口失败: %s", e)

    # 示例：调用 embeddings 接口
    try:
        inputs = ["示例文本"]
        emb_res = client.call_embeddings(inputs=inputs, model="Xorbits/bge-m3")
        print("Embeddings 返回：", json.dumps(emb_res, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.error("调用 embeddings 接口失败: %s", e)