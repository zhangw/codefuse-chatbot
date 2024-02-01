import os
import sys
import logging
import torch
import openai
import base64
from .utils import is_running_in_docker
from .default_config import *
# 日志格式
LOG_FORMAT = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format=LOG_FORMAT)

VERSION = "v0.1.0"

import platform
system_name = platform.system()

try:
    # ignore these content
    from zdatafront import client, monkey, OPENAI_API_BASE
    # patch openai sdk
    monkey.patch_openai()
    secret_key = base64.b64decode('xx').decode('utf-8')
    # zdatafront 提供的统一加密密钥
    client.aes_secret_key = secret_key
    # zdatafront 分配的业务标记
    client.visit_domain = os.environ.get("visit_domain")
    client.visit_biz = os.environ.get("visit_biz")
    client.visit_biz_line = os.environ.get("visit_biz_line")
except:
    pass

# add your openai key
OPENAI_API_BASE = "http://openai.com/v1/chat/completions"
os.environ["API_BASE_URL"] = OPENAI_API_BASE
os.environ["OPENAI_API_KEY"] = "sk-xx"
openai.api_key = "sk-xx"
# os.environ["OPENAI_PROXY"] = "socks5h://127.0.0.1:13659"
os.environ["DUCKDUCKGO_PROXY"] = os.environ.get("DUCKDUCKGO_PROXY") or "socks5://127.0.0.1:13659"
# ignore if you dont's use baidu_ocr_api
os.environ["BAIDU_OCR_API_KEY"] = "xx"
os.environ["BAIDU_OCR_SECRET_KEY"] = "xx"

os.environ["log_verbose"] = "2"
# LLM 名称
EMBEDDING_ENGINE = 'model'  # openai or model
EMBEDDING_MODEL = "text2vec-base"
LLM_MODEL = "codellama_34b"
LLM_MODELs = ["codellama_34b"]
USE_FASTCHAT = "gpt" not in LLM_MODEL # 判断是否进行fastchat

# LLM 运行设备
LLM_DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# 在以下字典中修改属性值，以指定本地embedding模型存储位置
# 如将 "text2vec": "GanymedeNil/text2vec-large-chinese" 修改为 "text2vec": "User/Downloads/text2vec-large-chinese"
# 此处请写绝对路径
embedding_model_dict = {
    "ernie-tiny": "nghuyong/ernie-3.0-nano-zh",
    "ernie-base": "nghuyong/ernie-3.0-base-zh",
    "text2vec-base": "shibing624/text2vec-base-chinese",
    "text2vec": "GanymedeNil/text2vec-large-chinese",
    "text2vec-paraphrase": "shibing624/text2vec-base-chinese-paraphrase",
    "text2vec-sentence": "shibing624/text2vec-base-chinese-sentence",
    "text2vec-multilingual": "shibing624/text2vec-base-multilingual",
    "m3e-small": "moka-ai/m3e-small",
    "m3e-base": "moka-ai/m3e-base",
    "m3e-large": "moka-ai/m3e-large",
    "bge-small-zh": "BAAI/bge-small-zh",
    "bge-base-zh": "BAAI/bge-base-zh",
    "bge-large-zh": "BAAI/bge-large-zh"
}


LOCAL_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "embedding_models")
embedding_model_dict = {k: f"/home/user/chatbot/embedding_models/{v}" if is_running_in_docker() else f"{LOCAL_MODEL_DIR}/{v}" for k, v in embedding_model_dict.items()}

# Embedding 模型运行设备
EMBEDDING_DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

ONLINE_LLM_MODEL = {
    # 线上模型。请在server_config中为每个在线API设置不同的端口

    "openai-api": {
        "model_name": "gpt-3.5-turbo",
        "api_base_url": "https://api.openai.com/v1",
        "api_key": "",
        "openai_proxy": "",
    },
    "example": {
        "version": "gpt-3.5",  # 采用openai接口做示例
        "api_base_url": "https://api.openai.com/v1",
        "api_key": "",
        "provider": "ExampleWorker",
    },
}

# 建议使用chat模型，不要使用base，无法获取正确输出
llm_model_dict = {
    "chatglm-6b": {
        "local_model_path": "THUDM/chatglm-6b",
        "api_base_url": "http://localhost:8888/v1",  # "name"修改为fastchat服务中的"api_base_url"
        "api_key": "EMPTY"
    },
     "codellama_34b": {
        "local_model_path": "codefuse-ai/CodeFuse-CodeLlama-34B-4bits",
        "api_base_url": "http://localhost:20002/v1",  # "name"修改为fastchat服务中的"api_base_url"
        "api_key": "EMPTY"
    },
    # 以下模型经过测试可接入，配置仿照上述即可
    # 'codellama_34b', 'Baichuan2-13B-Base', 'Baichuan2-13B-Chat', 'baichuan2-7b-base', 'baichuan2-7b-chat', 
    # 'internlm-7b-base', 'internlm-chat-7b', 'chatglm2-6b', 'qwen-14b-base', 'qwen-14b-chat', 'qwen-1-8B-Chat', 
    # 'Qwen-7B', 'Qwen-7B-Chat', 'qwen-7b-base-v1.1', 'qwen-7b-chat-v1.1', 'chatglm3-6b', 'chatglm3-6b-32k', 
    # 'chatglm3-6b-base', 'Qwen-72B-Chat-Int4'
    # 调用chatgpt时如果报出： urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='api.openai.com', port=443):
    #  Max retries exceeded with url: /v1/chat/completions
    # 则需要将urllib3版本修改为1.25.11
    # 如果依然报urllib3.exceptions.MaxRetryError: HTTPSConnectionPool，则将https改为http
    # 参考https://zhuanlan.zhihu.com/p/350015032

    # 如果报出：raise NewConnectionError(
    # urllib3.exceptions.NewConnectionError: <urllib3.connection.HTTPSConnection object at 0x000001FE4BDB85E0>:
    # Failed to establish a new connection: [WinError 10060]
    # 则是因为内地和香港的IP都被OPENAI封了，需要切换为日本、新加坡等地
    "gpt-3.5-turbo": {
        "local_model_path": "gpt-3.5-turbo",
        "api_base_url": os.environ.get("API_BASE_URL"),
        "api_key": os.environ.get("OPENAI_API_KEY")
    },
    "gpt-3.5-turbo-16k": {
        "local_model_path": "gpt-3.5-turbo-16k",
        "api_base_url": os.environ.get("API_BASE_URL"),
        "api_key": os.environ.get("OPENAI_API_KEY")
    },
    "gpt-3.5-turbo-0613": {
        "local_model_path": "gpt-3.5-turbo-0613",
        "api_base_url": os.environ.get("API_BASE_URL"),
        "api_key": os.environ.get("OPENAI_API_KEY")
    },
    "gpt-4": {
        "local_model_path": "gpt-4",
        "api_base_url": os.environ.get("API_BASE_URL"),
        "api_key": os.environ.get("OPENAI_API_KEY")
    },
    "gpt-3.5-turbo-1106": {
        "local_model_path": "gpt-3.5-turbo-1106",
        "api_base_url": os.environ.get("API_BASE_URL"),
        "api_key": os.environ.get("OPENAI_API_KEY")
    },
}

# 建议使用chat模型，不要使用base，无法获取正确输出
VLLM_MODEL_DICT = {
 'chatglm2-6b':  "THUDM/chatglm-6b",
 }
# 以下模型经过测试可接入，配置仿照上述即可
# 'codellama_34b', 'Baichuan2-13B-Base', 'Baichuan2-13B-Chat', 'baichuan2-7b-base', 'baichuan2-7b-chat', 
# 'internlm-7b-base', 'internlm-chat-7b', 'chatglm2-6b', 'qwen-14b-base', 'qwen-14b-chat', 'qwen-1-8B-Chat', 
# 'Qwen-7B', 'Qwen-7B-Chat', 'qwen-7b-base-v1.1', 'qwen-7b-chat-v1.1', 'chatglm3-6b', 'chatglm3-6b-32k', 
# 'chatglm3-6b-base', 'Qwen-72B-Chat-Int4'


LOCAL_LLM_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "llm_models")
# 模型路径重置
llm_model_dict_c = {}
for k, v in llm_model_dict.items():
    v_c = {}
    for kk, vv in v.items():
        if kk=="local_model_path":
            v_c[kk] = f"/home/user/chatbot/llm_models/{vv}" if is_running_in_docker() else f"{LOCAL_LLM_MODEL_DIR}/{vv}" 
        else:
            v_c[kk] = vv
    llm_model_dict_c[k] = v_c

llm_model_dict = llm_model_dict_c
# 
VLLM_MODEL_DICT_c = {}
for k, v in VLLM_MODEL_DICT.items():
    VLLM_MODEL_DICT_c[k] = f"/home/user/chatbot/llm_models/{v}" if is_running_in_docker() else f"{LOCAL_LLM_MODEL_DIR}/{v}" 
VLLM_MODEL_DICT = VLLM_MODEL_DICT_c
