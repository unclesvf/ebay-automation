import chromadb
from chromadb.utils import embedding_functions
import logging
import uuid
from typing import List, Dict, Any

import os

class KnowledgeBase:
    """
    Interface for the Vector Database (ChromaDB).
    Manages storing email content with embeddings for semantic search.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, 'data', 'knowledge_base')
        else:
            self.db_path = db_path
        self.client = None
        self.collection = None
        self.logger = logging.getLogger("KnowledgeBase")
        
        self._initialize_db()

    def _initialize_db(self):
        """Connect to DB and Get/Create Collection."""
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            # Use default embedding function (all-MiniLM-L6-v2)
            # This downloads a small model on first run
            self.ef = embedding_functions.DefaultEmbeddingFunction()
            
            self.collection = self.client.get_or_create_collection(
                name="uncles_wisdom",
                embedding_function=self.ef,
                metadata={"description": "Email knowledge base for synthesis"}
            )
            self.logger.info(f"Connected to Knowledge Base at {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Knowledge Base: {e}")
            raise

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str] = None):
        """
        Add items to the vector store.
        """
        if not documents:
            return

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            self.logger.info(f"Ingested {len(documents)} items into Knowledge Base.")
        except Exception as e:
            self.logger.error(f"Error adding documents: {e}")

    def query(self, query_text: str, n_results: int = 5):
        """
        Search for similar content.
        """
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
