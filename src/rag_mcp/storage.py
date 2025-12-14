import os
import shutil
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import httpx
from typing import List, Optional
from .config import AppConfig

from .logger import logger

class RemoteEmbeddingFunction(EmbeddingFunction):
    def __init__(self, config: AppConfig):
        self.config = config
        self.url = f"{config.llm.base_url}/embeddings"
        self.model = config.model.name

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        if not input:
            return []

        try:
            payload = {
                "model": self.model,
                "input": input
            }
            headers = {"Content-Type": "application/json"}
            if self.config.llm.api_key:
                headers["Authorization"] = f"Bearer {self.config.llm.api_key}"

            response = httpx.post(
                self.url, 
                json=payload, 
                headers=headers, 
                timeout=self.config.llm.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            data_list = sorted(data['data'], key=lambda x: x['index'])
            return [item['embedding'] for item in data_list]
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise e

class RAGStorage:
    def __init__(self, target_dir: str, config: AppConfig):
        self.target_dir = target_dir
        self.db_path = os.path.join(target_dir, ".muxue_rag")
        self.config = config
        self.embedding_fn = RemoteEmbeddingFunction(config)
        self.client = None
        self.collection = None

    def initialize(self):
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path, exist_ok=True)
            
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name="rag_collection",
            embedding_function=self.embedding_fn
        )

    def add_documents(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        if not self.client:
            self.initialize()
            
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            end = min(i + batch_size, len(documents))
            self.collection.add(
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end]
            )

    def search(self, query: str, n_results: int = 5):
        if not self.client:
            self.initialize()
            
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def clear(self):
        if os.path.exists(self.db_path):
            shutil.rmtree(self.db_path)
            logger.info(f"Cleaned up {self.db_path}")
