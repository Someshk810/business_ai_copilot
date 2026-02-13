"""
Knowledge base search tool using vector embeddings.
"""

from typing import Dict, Any, List, Optional
import logging

from .base import BaseTool, retry_on_failure
from ..integrations.vector_db import VectorDatabase

logger = logging.getLogger(__name__)


class KnowledgeSearchTool(BaseTool):
    """
    Tool for searching company knowledge base using semantic search.
    """
    
    def __init__(self, vector_db: VectorDatabase):
        super().__init__(
            name="knowledge_search",
            description="Search internal knowledge base for documents, policies, and information using semantic search"
        )
        self.vector_db = vector_db
        self.cache_ttl = 3600  # 1 hour for knowledge search
    
    @retry_on_failure(max_retries=2, delay=0.5)
    def _execute(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute knowledge base search.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            Search results with relevance scores
        """
        logger.info(f"Searching knowledge base: '{query}'")
        
        if not query or len(query.strip()) < 3:
            return {
                'error': 'invalid_query',
                'message': 'Query must be at least 3 characters',
                'results': []
            }
        
        # Perform search
        results = self.vector_db.search(
            query=query,
            top_k=top_k,
            filters=filters
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'content': result.get('document'),
                'metadata': result.get('metadata', {}),
                'relevance_score': result.get('score', 0.0),
                'chunk_id': result.get('id')
            })
        
        return {
            'results': formatted_results,
            'total_found': len(formatted_results),
            'query': query,
            'filters_applied': filters or {}
        }