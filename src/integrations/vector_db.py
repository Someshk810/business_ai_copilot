"""
Vector database integration for knowledge search.
"""

from typing import Dict, Any, List, Optional
import logging

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config.settings import CHROMA_PERSIST_DIRECTORY

logger = logging.getLogger(__name__)


class VectorDatabase:
    """
    Vector database for semantic search over company knowledge.
    """
    
    def __init__(self):
        """Initialize vector database."""
        self.client = chromadb.Client(Settings(
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            anonymized_telemetry=False
        ))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="company_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        logger.info("Vector database initialized")
        
        # Add sample data if collection is empty
        if self.collection.count() == 0:
            self._add_sample_data()
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()
        
        # Build filter dict
        where_filter = None
        if filters:
            where_filter = {
                k: v for k, v in filters.items()
                if v is not None
            }
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )
        
        # Format results
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
        
        return formatted
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to the knowledge base.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: Optional list of document IDs
        """
        if not ids:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Generate embeddings
        embeddings = self.embedder.encode(documents).tolist()
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        
        logger.info(f"Added {len(documents)} documents to knowledge base")
    
    def _add_sample_data(self):
        """Add sample knowledge base documents for testing."""
        logger.info("Adding sample knowledge base data...")
        
        documents = [
            """Project Phoenix Team Structure

Core Team:
- Product Lead: Sarah Chen (VP Product) - sarah.chen@company.com
- Engineering Lead: Michael Rodriguez (Senior Director Engineering) - michael.r@company.com
- Design Lead: Jessica Wong (Design Manager) - jessica.wong@company.com

Executive Sponsors:
- David Park (CTO)
- Emily Thompson (VP Engineering)

External Stakeholders:
- Acme Corp - Primary Customer
- TechVendor Inc - API Integration Partner""",
            
            """Project Phoenix Communication Plan

Weekly status updates should be sent to:
- phoenix-team@company.com (internal team, ~15 people)
- executives-phoenix@company.com (CTO, VP Eng, VP Product)
- For external updates, include customer-success@acmecorp.com

Escalation path for blockers:
1. Team Lead (Michael Rodriguez)
2. VP Engineering (Emily Thompson)
3. CTO (David Park)

Status update cadence:
- Daily: Standup at 9:00 AM
- Weekly: Email update on Tuesdays
- Monthly: Executive review""",
            
            """Project Atlas Team

Project Atlas is focused on backend infrastructure improvements.

Team Members:
- Tech Lead: Alex Kumar
- Backend Engineers: 4 developers
- DevOps: 2 engineers

Status: On track
Timeline: Q1 2026 completion target"""
        ]
        
        metadatas = [
            {
                'source': 'confluence://projects/phoenix/team',
                'title': 'Project Phoenix - Team Structure',
                'project': 'Phoenix',
                'doc_type': 'confluence',
                'last_updated': '2026-02-01'
            },
            {
                'source': 'confluence://projects/phoenix/communication',
                'title': 'Project Phoenix - Communication Plan',
                'project': 'Phoenix',
                'doc_type': 'confluence',
                'last_updated': '2026-01-15'
            },
            {
                'source': 'confluence://projects/atlas/overview',
                'title': 'Project Atlas - Overview',
                'project': 'Atlas',
                'doc_type': 'confluence',
                'last_updated': '2026-02-01'
            }
        ]
        
        ids = ['doc_phoenix_team', 'doc_phoenix_comm', 'doc_atlas_overview']
        
        self.add_documents(documents, metadatas, ids)