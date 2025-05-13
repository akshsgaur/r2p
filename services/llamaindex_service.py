# services/llamaindex_service_simple.py - Simplified LlamaIndex service
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class LlamaIndexService:
    def __init__(self):
        """Initialize LlamaIndex service with fallback handling"""
        self.llm = None
        self.embed_model = None
        self.indices = {}
        self.documents_cache = {}
        self.service_available = False
        
        # Try to initialize LlamaIndex
        self._initialize_llama_index()
    
    def _initialize_llama_index(self):
        """Initialize LlamaIndex with version detection"""
        try:
            # Check if OpenAI API key is available
            if not os.getenv('OPENAI_API_KEY'):
                logger.warning("OpenAI API key not found. LlamaIndex will not work.")
                return
            
            # Try different import patterns based on version
            try:
                # New API (0.9+)
                from llama_index.core import VectorStoreIndex, Document, Settings
                from llama_index.embeddings.openai import OpenAIEmbedding
                from llama_index.llms.openai import OpenAI
                
                # Configure settings
                Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)
                Settings.embed_model = OpenAIEmbedding()
                
                self.VectorStoreIndex = VectorStoreIndex
                self.Document = Document
                self.use_settings = True
                self.service_available = True
                logger.info("Initialized LlamaIndex with new API (v0.9+)")
                
            except ImportError:
                # Old API (0.8.x)
                try:
                    from llama_index import VectorStoreIndex, Document, ServiceContext
                    from llama_index.embeddings import OpenAIEmbedding
                    from llama_index.llms import OpenAI
                    
                    self.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)
                    self.embed_model = OpenAIEmbedding()
                    self.service_context = ServiceContext.from_defaults(
                        llm=self.llm,
                        embed_model=self.embed_model
                    )
                    
                    self.VectorStoreIndex = VectorStoreIndex
                    self.Document = Document
                    self.use_settings = False
                    self.service_available = True
                    logger.info("Initialized LlamaIndex with old API (v0.8.x)")
                    
                except ImportError:
                    logger.error("Could not import LlamaIndex. Using mock mode.")
                    self.service_available = False
                    
        except Exception as e:
            logger.error(f"Error initializing LlamaIndex: {str(e)}")
            self.service_available = False
    
    def create_index(self, project_id: int):
        """Create a new index for a project"""
        if not self.service_available:
            logger.warning(f"LlamaIndex not available. Creating mock index for project {project_id}")
            self.indices[project_id] = {"mock": True}
            return True
        
        try:
            if self.use_settings:
                # New API
                self.indices[project_id] = self.VectorStoreIndex.from_documents([])
            else:
                # Old API
                self.indices[project_id] = self.VectorStoreIndex.from_documents(
                    [], 
                    service_context=self.service_context
                )
            
            self.documents_cache[project_id] = []
            logger.info(f"Created index for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            return False
    
    def index_papers(self, project_id: int, papers: List[Dict]):
        """Index research papers"""
        if not self.service_available:
            logger.warning(f"LlamaIndex not available. Mock indexing {len(papers)} papers")
            return len(papers)
        
        try:
            if project_id not in self.indices:
                self.create_index(project_id)
            
            documents = []
            
            for paper in papers:
                # Create text content from paper
                text_parts = []
                
                if paper.get('title'):
                    text_parts.append(f"Title: {paper['title']}")
                
                if paper.get('authors'):
                    text_parts.append(f"Authors: {paper['authors']}")
                
                if paper.get('abstract'):
                    text_parts.append(f"Abstract: {paper['abstract']}")
                elif paper.get('title'):
                    # If no abstract, use title as content
                    text_parts.append(f"Content: {paper['title']}")
                
                text_content = "\n\n".join(text_parts)
                
                # Create document
                doc = self.Document(
                    text=text_content,
                    metadata={
                        'title': paper.get('title', ''),
                        'authors': paper.get('authors', ''),
                        'url': paper.get('url', ''),
                        'source': paper.get('type', 'manual')
                    }
                )
                documents.append(doc)
            
            # Add documents to index
            index = self.indices[project_id]
            
            # Try to insert documents
            try:
                for doc in documents:
                    index.insert(doc)
            except Exception:
                # Fallback: recreate index with all documents
                all_docs = self.documents_cache.get(project_id, []) + documents
                if self.use_settings:
                    self.indices[project_id] = self.VectorStoreIndex.from_documents(all_docs)
                else:
                    self.indices[project_id] = self.VectorStoreIndex.from_documents(
                        all_docs, 
                        service_context=self.service_context
                    )
            
            # Update cache
            if project_id not in self.documents_cache:
                self.documents_cache[project_id] = []
            self.documents_cache[project_id].extend(documents)
            
            logger.info(f"Indexed {len(documents)} documents for project {project_id}")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error indexing papers: {str(e)}")
            return 0
    
    def query_research(self, project_id: int, query: str, top_k: int = 5):
        """Query the indexed research papers"""
        if not self.service_available:
            logger.warning("LlamaIndex not available. Returning mock response")
            return {
                "response": f"Mock response to query: {query}",
                "source_nodes": [
                    {
                        "text": "This is a mock response since LlamaIndex is not available...",
                        "metadata": {"source": "mock"}
                    }
                ]
            }
        
        try:
            if project_id not in self.indices:
                return {"error": "No index found for this project. Please index some papers first."}
            
            index = self.indices[project_id]
            
            # Create query engine
            if self.use_settings:
                query_engine = index.as_query_engine(similarity_top_k=top_k)
            else:
                query_engine = index.as_query_engine(
                    similarity_top_k=top_k,
                    service_context=self.service_context
                )
            
            # Query the index
            response = query_engine.query(query)
            
            # Extract source nodes
            source_nodes = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    node_info = {
                        "text": str(node.text)[:200] + "...",
                        "metadata": {}
                    }
                    
                    # Extract metadata safely
                    if hasattr(node, 'metadata') and node.metadata:
                        node_info["metadata"] = dict(node.metadata)
                    
                    source_nodes.append(node_info)
            
            return {
                "response": str(response),
                "source_nodes": source_nodes
            }
            
        except Exception as e:
            logger.error(f"Error querying research: {str(e)}")
            return {"error": str(e)}
    
    def extract_concepts(self, project_id: int, limit: int = 20):
        """Extract key concepts from the indexed papers"""
        if not self.service_available:
            logger.warning("LlamaIndex not available. Returning mock concepts")
            mock_concepts = [
                "machine learning", "neural networks", "deep learning",
                "artificial intelligence", "data science", "natural language processing",
                "computer vision", "reinforcement learning"
            ][:limit]
            
            return {
                "concepts": mock_concepts,
                "full_response": "Mock response with concepts extracted from papers"
            }
        
        try:
            if project_id not in self.indices:
                return {"error": "No index found for this project"}
            
            # Use a simple query to extract concepts
            query = "What are the main concepts, techniques, and methods discussed in these research papers?"
            
            result = self.query_research(project_id, query)
            
            if "error" in result:
                return result
            
            # Extract concepts from the response
            response_text = result.get("response", "")
            
            # Simple concept extraction
            concepts = []
            
            # Look for common academic terms and concepts
            concept_keywords = [
                "algorithm", "method", "technique", "approach", "framework",
                "model", "system", "architecture", "design", "concept",
                "theory", "analysis", "optimization", "learning", "network"
            ]
            
            # Split response into sentences and extract concepts
            sentences = response_text.split('.')
            for sentence in sentences:
                words = sentence.lower().split()
                for i, word in enumerate(words):
                    if any(keyword in word for keyword in concept_keywords):
                        # Get surrounding words as potential concepts
                        if i > 0:
                            prev_word = words[i-1].strip(',()[]')
                            if len(prev_word) > 2:
                                concepts.append(prev_word)
                        if i < len(words) - 1:
                            next_word = words[i+1].strip(',()[]')
                            if len(next_word) > 2:
                                concepts.append(next_word)
            
            # Also look for capitalized words (likely important terms)
            import re
            capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', response_text)
            concepts.extend(capitalized_words)
            
            # Remove duplicates and filter
            concepts = list(dict.fromkeys(concepts))
            concepts = [c for c in concepts if len(c) > 2 and c.lower() not in ['the', 'and', 'for', 'with']][:limit]
            
            return {
                "concepts": concepts,
                "full_response": response_text
            }
            
        except Exception as e:
            logger.error(f"Error extracting concepts: {str(e)}")
            return {"error": str(e)}