import os
import shutil
from typing import List
from functools import lru_cache
from loguru import logger

# from langchain.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain.docstore.document import Document
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.vectorstores.utils import DistanceStrategy

# from configs.model_config import (
#     KB_ROOT_PATH,
#     CACHED_VS_NUM,
#     EMBEDDING_MODEL,
#     EMBEDDING_DEVICE,
#     SCORE_THRESHOLD,
#     FAISS_NORMALIZE_L2
# )
# from configs.model_config import embedding_model_dict

from coagent.base_configs.env_config import (
    KB_ROOT_PATH,
    CACHED_VS_NUM, SCORE_THRESHOLD, FAISS_NORMALIZE_L2
)

from .base_service import KBService, SupportedVSType
from coagent.utils.path_utils import *
from coagent.orm.utils import DocumentFile
from coagent.utils.server_utils import torch_gc
from coagent.embeddings.utils import load_embeddings, load_embeddings_from_path
from coagent.embeddings.faiss_m import FAISS
from coagent.llm_models.llm_config import EmbedConfig


# make HuggingFaceEmbeddings hashable
def _embeddings_hash(self):
    return hash(self.model_name)


HuggingFaceEmbeddings.__hash__ = _embeddings_hash

_VECTOR_STORE_TICKS = {}


# @lru_cache(CACHED_VS_NUM)
def load_vector_store(
        knowledge_base_name: str,
        embed_config: EmbedConfig,
        embeddings: Embeddings = None,
        tick: int = 0,  # tick will be changed by upload_doc etc. and make cache refreshed.
        kb_root_path: str = KB_ROOT_PATH,
):
    print(f"loading vector store in '{knowledge_base_name}'.")
    vs_path = get_vs_path(knowledge_base_name, kb_root_path)
    if embeddings is None:
        embeddings = load_embeddings_from_path(embed_config.embed_model_path, embed_config.model_device)

    if not os.path.exists(vs_path):
        os.makedirs(vs_path)
    
    distance_strategy = DistanceStrategy.EUCLIDEAN_DISTANCE
    if "index.faiss" in os.listdir(vs_path):
        search_index = FAISS.load_local(vs_path, embeddings, normalize_L2=FAISS_NORMALIZE_L2, distance_strategy=distance_strategy)
    else:
        # create an empty vector store
        doc = Document(page_content="init", metadata={})
        search_index = FAISS.from_documents([doc], embeddings, normalize_L2=FAISS_NORMALIZE_L2, distance_strategy=distance_strategy)
        ids = [k for k, v in search_index.docstore._dict.items()]
        search_index.delete(ids)
        search_index.save_local(vs_path)
    
    if tick == 0: # vector store is loaded first time
        _VECTOR_STORE_TICKS[knowledge_base_name] = 0

    # search_index.embedding_function = embeddings.embed_documents
    return search_index


def refresh_vs_cache(kb_name: str):
    """
    make vector store cache refreshed when next loading
    """
    _VECTOR_STORE_TICKS[kb_name] = _VECTOR_STORE_TICKS.get(kb_name, 0) + 1
    print(f"知识库 {kb_name} 缓存刷新：{_VECTOR_STORE_TICKS[kb_name]}")


class FaissKBService(KBService):
    vs_path: str
    kb_path: str

    def vs_type(self) -> str:
        return SupportedVSType.FAISS

    @staticmethod
    def get_vs_path(knowledge_base_name: str):
        return os.path.join(FaissKBService.get_kb_path(knowledge_base_name), "vector_store")

    @staticmethod
    def get_kb_path(knowledge_base_name: str):
        return os.path.join(KB_ROOT_PATH, knowledge_base_name)

    def do_init(self):
        self.kb_path = FaissKBService.get_kb_path(self.kb_name)
        self.vs_path = FaissKBService.get_vs_path(self.kb_name)

    def do_create_kb(self):
        if not os.path.exists(self.vs_path):
            os.makedirs(self.vs_path)
        load_vector_store(self.kb_name, self.embed_config)

    def do_drop_kb(self):
        self.clear_vs()
        shutil.rmtree(self.kb_path)

    def do_search(self,
                  query: str,
                  top_k: int,
                  score_threshold: float = SCORE_THRESHOLD,
                  embeddings: Embeddings = None,
                  ) -> List[Document]:
        search_index = load_vector_store(self.kb_name,
                                         self.embed_config,
                                         embeddings=embeddings,
                                         tick=_VECTOR_STORE_TICKS.get(self.kb_name),
                                         kb_root_path=self.kb_root_path)
        docs = search_index.similarity_search_with_score(query, k=top_k, score_threshold=score_threshold)
        return docs
    
    def get_all_documents(self, embeddings: Embeddings = None,):
        search_index = load_vector_store(self.kb_name,
                                         self.embed_config,
                                         embeddings=embeddings,
                                         tick=_VECTOR_STORE_TICKS.get(self.kb_name),
                                         kb_root_path=self.kb_root_path)
        return search_index.get_all_documents()

    def do_add_doc(self,
                   docs: List[Document],
                   embeddings: Embeddings,
                   **kwargs,
                   ):
        vector_store = load_vector_store(self.kb_name,
                                         self.embed_config,
                                         embeddings=embeddings,
                                         tick=_VECTOR_STORE_TICKS.get(self.kb_name, 0),
                                         kb_root_path=self.kb_root_path)
        vector_store.embedding_function = embeddings.embed_documents
        logger.info("loaded docs, docs' lens is {}".format(len(docs)))
        vector_store.add_documents(docs)
        torch_gc()
        if not kwargs.get("not_refresh_vs_cache"):
            vector_store.save_local(self.vs_path)
            refresh_vs_cache(self.kb_name)

    def do_delete_doc(self,
                      kb_file: DocumentFile,
                      **kwargs):
        embeddings = self._load_embeddings()
        vector_store = load_vector_store(self.kb_name,
                                         self.embed_config,
                                         embeddings=embeddings,
                                         tick=_VECTOR_STORE_TICKS.get(self.kb_name, 0),
                                         kb_root_path=self.kb_root_path)

        ids = [k for k, v in vector_store.docstore._dict.items() if v.metadata["source"] == kb_file.filepath]
        if len(ids) == 0:
            return None

        vector_store.delete(ids)
        if not kwargs.get("not_refresh_vs_cache"):
            vector_store.save_local(self.vs_path)
            refresh_vs_cache(self.kb_name)

        return True

    def do_clear_vs(self):
        if os.path.exists(self.vs_path):
            shutil.rmtree(self.vs_path)
        os.makedirs(self.vs_path)
        refresh_vs_cache(self.kb_name)

    def exist_doc(self, file_name: str):
        if super().exist_doc(file_name):
            return "in_db"

        content_path = os.path.join(self.kb_path, "content")
        if os.path.isfile(os.path.join(content_path, file_name)):
            return "in_folder"
        else:
            return False
