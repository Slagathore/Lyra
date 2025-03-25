import logging
import json
import requests
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger("knowledge_integration")

class KnowledgeIntegrator:
    """
    Integrates external knowledge sources to enhance the AI's understanding
    and provide more accurate information during conversations.
    """
    
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.knowledge_sources = {}
        self.cache = {}
        self.cache_dir = Path(self.config.get("cache_dir", "knowledge_cache"))
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize knowledge sources
        self._init_knowledge_sources()
        
        logger.info(f"Knowledge integrator initialized with {len(self.knowledge_sources)} sources")
    
    def _load_config(self, config_path):
        """Load configuration from file or use defaults."""
        default_config = {
            "sources": {
                "wikipedia": {
                    "enabled": True,
                    "api_url": "https://en.wikipedia.org/w/api.php",
                    "max_results": 3
                },
                "arxiv": {
                    "enabled": True,
                    "api_url": "http://export.arxiv.org/api/query",
                    "max_results": 5
                },
                "local_database": {
                    "enabled": True,
                    "path": "knowledge_base/facts.json"
                }
            },
            "cache_dir": "knowledge_cache",
            "cache_expiry": 86400  # 24 hours
        }
        
        if not config_path:
            return default_config
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
                elif isinstance(value, dict) and key in config:
                    for subkey, subvalue in value.items():
                        if subkey not in config[key]:
                            config[key][subkey] = subvalue
            
            return config
        except Exception as e:
            logger.error(f"Error loading config, using defaults: {e}")
            return default_config
    
    def _init_knowledge_sources(self):
        """Initialize all enabled knowledge sources."""
        sources_config = self.config.get("sources", {})
        
        for source_name, source_config in sources_config.items():
            if source_config.get("enabled", False):
                self.knowledge_sources[source_name] = source_config
                logger.info(f"Enabled knowledge source: {source_name}")
    
    def query_knowledge(self, query, sources=None, max_results=None):
        """
        Query knowledge sources for information related to the query.
        
        Args:
            query: The search query
            sources: Specific sources to query (None for all enabled sources)
            max_results: Maximum number of results per source
            
        Returns:
            Dict containing information from various sources
        """
        if not query:
            return {"error": "Empty query"}
        
        # Check cache first
        cache_key = f"{query}_{sources}_{max_results}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Knowledge query cache hit: {query}")
            return cached_result
        
        # If no specific sources provided, use all enabled ones
        if not sources:
            sources = list(self.knowledge_sources.keys())
        else:
            # Filter to make sure we only use enabled sources
            sources = [s for s in sources if s in self.knowledge_sources]
        
        results = {}
        
        for source in sources:
            try:
                source_results = self._query_source(source, query, max_results)
                results[source] = source_results
            except Exception as e:
                logger.error(f"Error querying {source}: {e}")
                results[source] = {"error": str(e)}
        
        # Cache the results
        self._add_to_cache(cache_key, results)
        
        return results
    
    def _query_source(self, source_name, query, max_results=None):
        """Query a specific knowledge source."""
        source_config = self.knowledge_sources.get(source_name)
        if not source_config:
            return {"error": f"Source {source_name} not found or not enabled"}
        
        # If max_results not specified, use the source default
        if max_results is None:
            max_results = source_config.get("max_results", 3)
        
        # Wikipedia source
        if source_name == "wikipedia":
            return self._query_wikipedia(query, max_results, source_config)
        
        # arXiv source
        elif source_name == "arxiv":
            return self._query_arxiv(query, max_results, source_config)
        
        # Local database
        elif source_name == "local_database":
            return self._query_local_database(query, max_results, source_config)
        
        else:
            return {"error": f"Unsupported source: {source_name}"}
    
    def _query_wikipedia(self, query, max_results, config):
        """Query Wikipedia for information."""
        api_url = config.get("api_url")
        
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|pageimages",
            "exintro": True,
            "explaintext": True,
            "pithumbsize": 100,
            "generator": "search",
            "gsrlimit": max_results,
            "gsrsearch": query
        }
        
        response = requests.get(api_url, params=params)
        data = response.json()
        
        results = []
        if "query" in data and "pages" in data["query"]:
            for page_id, page_data in data["query"]["pages"].items():
                results.append({
                    "title": page_data.get("title", "Unknown"),
                    "extract": page_data.get("extract", "No information available"),
                    "page_id": page_id,
                    "url": f"https://en.wikipedia.org/?curid={page_id}"
                })
        
        return {
            "results": results,
            "count": len(results),
            "source": "wikipedia",
            "timestamp": time.time()
        }
    
    def _query_arxiv(self, query, max_results, config):
        """Query arXiv for papers."""
        api_url = config.get("api_url")
        
        params = {
            "search_query": f"all:{query}",
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        response = requests.get(api_url, params=params)
        
        # Parse XML response
        from xml.etree import ElementTree
        root = ElementTree.fromstring(response.content)
        
        # Define namespace mapping
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        results = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text
            summary = entry.find('atom:summary', ns).text
            link = entry.find('atom:id', ns).text
            
            # Extract authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns).text
                authors.append(name)
            
            # Extract published date
            published = entry.find('atom:published', ns).text
            
            results.append({
                "title": title,
                "summary": summary,
                "authors": authors,
                "url": link,
                "published": published
            })
        
        return {
            "results": results,
            "count": len(results),
            "source": "arxiv",
            "timestamp": time.time()
        }
    
    def _query_local_database(self, query, max_results, config):
        """Query local knowledge database."""
        db_path = Path(config.get("path", "knowledge_base/facts.json"))
        
        if not db_path.exists():
            return {
                "results": [],
                "count": 0,
                "source": "local_database",
                "error": "Database file not found"
            }
        
        try:
            with open(db_path, 'r') as f:
                database = json.load(f)
            
            # Simple search implementation
            # In a real system, this would use more sophisticated search algorithms
            query_terms = query.lower().split()
            results = []
            
            for item in database:
                # Calculate a simple relevance score
                score = 0
                for term in query_terms:
                    if term in item.get("keywords", []):
                        score += 3
                    if term in item.get("title", "").lower():
                        score += 2
                    if term in item.get("content", "").lower():
                        score += 1
                
                if score > 0:
                    item["relevance_score"] = score
                    results.append(item)
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            results = results[:max_results]
            
            return {
                "results": results,
                "count": len(results),
                "source": "local_database",
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error querying local database: {e}")
            return {
                "results": [],
                "count": 0,
                "source": "local_database",
                "error": str(e)
            }
    
    def _get_from_cache(self, cache_key):
        """Get results from cache if available and not expired."""
        # Check in-memory cache first
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry["timestamp"] < self.config.get("cache_expiry", 86400):
                return entry["data"]
        
        # Check file cache
        cache_file = self.cache_dir / f"{hash(cache_key)}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    entry = json.load(f)
                
                if time.time() - entry["timestamp"] < self.config.get("cache_expiry", 86400):
                    # Update in-memory cache
                    self.cache[cache_key] = entry
                    return entry["data"]
            except:
                pass
        
        return None
    
    def _add_to_cache(self, cache_key, data):
        """Add results to cache."""
        entry = {
            "timestamp": time.time(),
            "data": data
        }
        
        # Add to in-memory cache
        self.cache[cache_key] = entry
        
        # Add to file cache
        cache_file = self.cache_dir / f"{hash(cache_key)}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(entry, f)
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
