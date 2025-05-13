# services/weaviate_service_v4.py - Updated Weaviate service for v4 API
import weaviate
from weaviate.auth import AuthApiKey
import os
import json
import logging

logger = logging.getLogger(__name__)

class WeaviateService:
    def __init__(self):
        self.client = None
        self.connect()
        
    def connect(self):
        """Connect to Weaviate instance using v4 API"""
        try:
            # Check if we have credentials for Weaviate Cloud
            weaviate_url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
            weaviate_api_key = os.getenv('WEAVIATE_API_KEY')
            
            if weaviate_api_key:
                # Connect to Weaviate Cloud with API key
                auth_config = AuthApiKey(api_key=weaviate_api_key)
                self.client = weaviate.WeaviateClient(
                    url=weaviate_url,
                    auth_client_secret=auth_config
                )
            else:
                # Connect to local Weaviate instance
                self.client = weaviate.WeaviateClient(url=weaviate_url)
            
            # Test connection
            if self.client:
                # For v4, we use connect() method
                self.client.connect()
                logger.info("Connected to Weaviate successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {str(e)}")
            self.client = None
    
    def create_schema(self, project_id: int):
        """Create schema for storing research concepts and implementations"""
        try:
            if not self.client:
                return False
            
            # Use collections API for v4
            collections = self.client.collections
            
            # Define schema for research concepts
            concept_collection_name = f"ResearchConcept_Project_{project_id}"
            
            # Check if collection already exists
            try:
                collections.get(concept_collection_name)
                logger.info(f"Collection {concept_collection_name} already exists")
            except:
                # Create collection if it doesn't exist
                collections.create(
                    name=concept_collection_name,
                    description="Research concepts extracted from papers",
                    properties=[
                        {"name": "title", "dataType": "string", "description": "Concept title or name"},
                        {"name": "description", "dataType": "text", "description": "Detailed description of the concept"},
                        {"name": "keywords", "dataType": "string[]", "description": "Related keywords and tags"},
                        {"name": "source_paper", "dataType": "string", "description": "Source paper title"},
                        {"name": "implementation_difficulty", "dataType": "int", "description": "Difficulty score for implementation (1-10)"}
                    ],
                    vectorizer_config=weaviate.Configure.Vectorizer.text2vec_openai()
                )
                logger.info(f"Created collection {concept_collection_name}")
            
            # Define schema for implementations
            impl_collection_name = f"Implementation_Project_{project_id}"
            
            try:
                collections.get(impl_collection_name)
                logger.info(f"Collection {impl_collection_name} already exists")
            except:
                collections.create(
                    name=impl_collection_name,
                    description="Practical implementations and code examples",
                    properties=[
                        {"name": "title", "dataType": "string", "description": "Implementation title"},
                        {"name": "description", "dataType": "text", "description": "Implementation description"},
                        {"name": "code_snippet", "dataType": "text", "description": "Code example or snippet"},
                        {"name": "language", "dataType": "string", "description": "Programming language"},
                        {"name": "complexity", "dataType": "string", "description": "Implementation complexity level"}
                    ],
                    vectorizer_config=weaviate.Configure.Vectorizer.text2vec_openai()
                )
                logger.info(f"Created collection {impl_collection_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating schema: {str(e)}")
            return False
    
    def store_concepts(self, project_id: int, concepts: list):
        """Store research concepts in Weaviate using v4 API"""
        try:
            if not self.client:
                return 0
                
            collection_name = f"ResearchConcept_Project_{project_id}"
            collection = self.client.collections.get(collection_name)
            
            stored_count = 0
            
            # Batch insert for better performance
            with collection.batch.dynamic() as batch:
                for concept in concepts:
                    data_object = {
                        "title": concept.get("title", ""),
                        "description": concept.get("description", ""),
                        "keywords": concept.get("keywords", []),
                        "source_paper": concept.get("source_paper", ""),
                        "implementation_difficulty": concept.get("difficulty", 5)
                    }
                    
                    batch.add_object(properties=data_object)
                    stored_count += 1
            
            logger.info(f"Stored {stored_count} concepts for project {project_id}")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing concepts: {str(e)}")
            return 0
    
    def store_implementations(self, project_id: int, implementations: list):
        """Store implementation examples in Weaviate using v4 API"""
        try:
            if not self.client:
                return 0
                
            collection_name = f"Implementation_Project_{project_id}"
            collection = self.client.collections.get(collection_name)
            
            stored_count = 0
            
            with collection.batch.dynamic() as batch:
                for impl in implementations:
                    data_object = {
                        "title": impl.get("title", ""),
                        "description": impl.get("description", ""),
                        "code_snippet": impl.get("code", ""),
                        "language": impl.get("language", "python"),
                        "complexity": impl.get("complexity", "medium")
                    }
                    
                    batch.add_object(properties=data_object)
                    stored_count += 1
            
            logger.info(f"Stored {stored_count} implementations for project {project_id}")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing implementations: {str(e)}")
            return 0
    
    def find_connections(self, project_id: int, concept_query: str, limit: int = 5):
        """Find connections between research concepts and implementations using v4 API"""
        try:
            if not self.client:
                return {"error": "Not connected to Weaviate"}
                
            concept_collection_name = f"ResearchConcept_Project_{project_id}"
            impl_collection_name = f"Implementation_Project_{project_id}"
            
            # Search for related concepts
            try:
                concept_collection = self.client.collections.get(concept_collection_name)
                concept_result = concept_collection.query.near_text(
                    query=concept_query,
                    limit=limit
                )
            except:
                concept_result = None
            
            # Search for related implementations
            try:
                impl_collection = self.client.collections.get(impl_collection_name)
                impl_result = impl_collection.query.near_text(
                    query=concept_query,
                    limit=limit
                )
            except:
                impl_result = None
            
            connections = {
                "concepts": [obj.properties for obj in (concept_result.objects if concept_result else [])],
                "implementations": [obj.properties for obj in (impl_result.objects if impl_result else [])]
            }
            
            return connections
            
        except Exception as e:
            logger.error(f"Error finding connections: {str(e)}")
            return {"error": str(e)}
    
    def get_implementation_suggestions(self, project_id: int, concept: str, limit: int = 3):
        """Get implementation suggestions for a given concept using v4 API"""
        try:
            if not self.client:
                return {"error": "Not connected to Weaviate"}
                
            collection_name = f"Implementation_Project_{project_id}"
            
            try:
                collection = self.client.collections.get(collection_name)
                result = collection.query.near_text(
                    query=concept,
                    limit=limit,
                    return_metadata=["distance"]
                )
                
                suggestions = []
                for obj in result.objects:
                    suggestions.append({
                        **obj.properties,
                        "distance": obj.metadata.distance if obj.metadata else None
                    })
                
                return {
                    "concept": concept,
                    "suggestions": suggestions
                }
            except Exception as e:
                logger.error(f"Collection not found or query failed: {e}")
                return {
                    "concept": concept,
                    "suggestions": []
                }
            
        except Exception as e:
            logger.error(f"Error getting implementation suggestions: {str(e)}")
            return {"error": str(e)}
    
    def close(self):
        """Close the Weaviate client connection"""
        if self.client:
            self.client.close()