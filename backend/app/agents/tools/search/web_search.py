"""
Web search tools for PulsePlan agents.
Handles information retrieval and research using Tavily API.
"""
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
import httpx
import os
import logging
from ..core.base import BaseTool, ToolResult, ToolError

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Web search tool using Tavily API for high-quality search results with sources"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for current information and research using Tavily"
        )
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.tavily_base_url = "https://api.tavily.com"
    
    def get_required_tokens(self) -> list[str]:
        return []  # Uses search API keys, not OAuth tokens
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate web search input"""
        query = input_data.get("query")
        if not query or not isinstance(query, str) or len(query.strip()) == 0:
            return False
        
        max_results = input_data.get("max_results", 5)
        if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
            return False
        
        return True
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute web search using Tavily"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data - query string required", self.name)
            
            query = input_data["query"].strip()
            max_results = input_data.get("max_results", 5)
            search_depth = input_data.get("search_depth", "basic")  # basic or advanced
            include_answer = input_data.get("include_answer", True)
            include_raw_content = input_data.get("include_raw_content", False)
            
            # Perform Tavily search
            search_results = await self._perform_tavily_search(
                query, max_results, search_depth, include_answer, include_raw_content, context
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = ToolResult(
                success=True,
                data={
                    "query": query,
                    "answer": search_results.get("answer"),
                    "results": search_results.get("results", []),
                    "total_results": len(search_results.get("results", [])),
                    "search_metadata": {
                        "search_depth": search_depth,
                        "max_results": max_results,
                        "include_answer": include_answer,
                        "search_timestamp": datetime.utcnow().isoformat(),
                        "provider": "tavily"
                    }
                },
                execution_time=execution_time,
                metadata={"operation": "search", "query": query, "provider": "tavily"}
            )
            
            self.log_execution(input_data, result, context)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_result = ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time
            )
            
            self.log_execution(input_data, error_result, context)
            return error_result
    
    async def _perform_tavily_search(
        self, 
        query: str, 
        max_results: int, 
        search_depth: str, 
        include_answer: bool,
        include_raw_content: bool,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform search using Tavily API"""
        
        if not self.tavily_api_key:
            raise ToolError("Tavily API key not configured. Please set TAVILY_API_KEY environment variable.", self.name)
        
        try:
            async with httpx.AsyncClient() as client:
                # Prepare Tavily API request
                payload = {
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "include_answer": include_answer,
                    "include_raw_content": include_raw_content,
                    "include_favicon": True,
                    "max_results": max_results,
                    "include_domains": [],
                    "exclude_domains": []
                }
                
                # Make API request to Tavily
                response = await client.post(
                    f"{self.tavily_base_url}/search",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    tavily_data = response.json()
                    return self._process_tavily_response(tavily_data)
                else:
                    raise ToolError(
                        f"Tavily API error: {response.status_code} - {response.text}",
                        self.name,
                        recoverable=True
                    )
                    
        except httpx.TimeoutException:
            raise ToolError("Tavily API timeout", self.name, recoverable=True)
        except httpx.RequestError as e:
            raise ToolError(f"Tavily API request failed: {e}", self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Tavily search failed: {e}", self.name, recoverable=True)
    
    def _process_tavily_response(self, tavily_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize Tavily API response"""
        processed_results = []
        
        # Debug: Log the structure of the first result to understand the format
        if tavily_data.get("results"):
            first_result = tavily_data["results"][0]
            logger.debug(f"First result structure: {list(first_result.keys())}")
            logger.debug(f"Favicon field: {first_result.get('favicon')}")
            logger.debug(f"Answer field: {tavily_data.get('answer')}")
        
        # Process search results
        for result in tavily_data.get("results", []):
            # Extract favicon - Tavily returns it as a simple string URL
            favicon = result.get("favicon")
            
            # If no favicon from images, try to construct from domain
            if not favicon:
                domain = self._extract_domain(result.get("url", ""))
                if domain and domain != "unknown":
                    favicon = f"https://{domain}/favicon.ico"
            
            processed_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "raw_content": result.get("raw_content"),
                "score": result.get("score", 0.0),
                "published_date": result.get("published_date"),
                "source": self._extract_domain(result.get("url", "")),
                "favicon": favicon,
                "provider": "tavily"
            }
            processed_results.append(processed_result)
        
        return {
            "query": tavily_data.get("query"),
            "answer": tavily_data.get("answer"),
            "results": processed_results,
            "response_time": tavily_data.get("response_time"),
            "follow_up_questions": tavily_data.get("follow_up_questions", [])
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except:
            return "unknown"
    


class NewsSearchTool(WebSearchTool):
    """Specialized tool for news search using Tavily with news focus"""
    
    def __init__(self):
        super().__init__()
        self.name = "news_search"
        self.description = "Search for current news and breaking stories using Tavily"
    
    async def _perform_tavily_search(
        self, 
        query: str, 
        max_results: int, 
        search_depth: str, 
        include_answer: bool,
        include_raw_content: bool,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform news-specific search using Tavily"""
        
        if not self.tavily_api_key:
            raise ToolError("Tavily API key not configured. Please set TAVILY_API_KEY environment variable.", self.name)
        
        try:
            async with httpx.AsyncClient() as client:
                # Prepare Tavily API request with news focus
                payload = {
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "include_answer": include_answer,
                    "include_raw_content": include_raw_content,
                    "include_favicon": True,
                    "max_results": max_results,
                    "include_domains": ["news.google.com", "reuters.com", "bbc.com", "cnn.com", "apnews.com"],
                    "exclude_domains": []
                }
                
                # Make API request to Tavily
                response = await client.post(
                    f"{self.tavily_base_url}/search",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    tavily_data = response.json()
                    return self._process_tavily_response(tavily_data)
                else:
                    raise ToolError(
                        f"Tavily API error: {response.status_code} - {response.text}",
                        self.name,
                        recoverable=True
                    )
                    
        except httpx.TimeoutException:
            raise ToolError("Tavily API timeout", self.name, recoverable=True)
        except httpx.RequestError as e:
            raise ToolError(f"Tavily API request failed: {e}", self.name, recoverable=True)
        except Exception as e:
            raise ToolError(f"Tavily news search failed: {e}", self.name, recoverable=True)
    


class ResearchTool(BaseTool):
    """Comprehensive research tool combining multiple search sources"""
    
    def __init__(self):
        super().__init__(
            name="research_tool",
            description="Comprehensive research across multiple sources and formats"
        )
        
        # Initialize search tools
        self.web_search = WebSearchTool()
        self.news_search = NewsSearchTool()
    
    def get_required_tokens(self) -> list[str]:
        return []  # Uses search APIs, not OAuth tokens
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate research input"""
        research_query = input_data.get("research_query")
        if not research_query or not isinstance(research_query, str):
            return False
        
        sources = input_data.get("sources", ["web", "news"])
        if not isinstance(sources, list) or not sources:
            return False
        
        valid_sources = ["web", "news", "academic", "social"]
        return all(source in valid_sources for source in sources)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute comprehensive research"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data - research_query and sources required", self.name)
            
            research_query = input_data["research_query"]
            sources = input_data.get("sources", ["web", "news"])
            max_results_per_source = input_data.get("max_results_per_source", 5)
            
            # Perform research across multiple sources
            research_results = await self._perform_comprehensive_research(
                research_query, sources, max_results_per_source, context
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = ToolResult(
                success=True,
                data={
                    "research_query": research_query,
                    "sources_searched": sources,
                    "results_by_source": research_results,
                    "total_results": sum(len(results) for results in research_results.values()),
                    "research_summary": self._generate_research_summary(research_results),
                    "research_metadata": {
                        "sources": sources,
                        "max_results_per_source": max_results_per_source,
                        "research_timestamp": datetime.utcnow().isoformat()
                    }
                },
                execution_time=execution_time,
                metadata={"operation": "research", "query": research_query}
            )
            
            self.log_execution(input_data, result, context)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_result = ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time
            )
            
            self.log_execution(input_data, error_result, context)
            return error_result
    
    async def _perform_comprehensive_research(
        self, 
        query: str, 
        sources: List[str], 
        max_results_per_source: int, 
        context: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform research across multiple sources concurrently"""
        
        research_tasks = []
        source_mapping = {}
        
        # Prepare search tasks for each source
        for source in sources:
            if source == "web":
                search_input = {
                    "query": query,
                    "max_results": max_results_per_source,
                    "search_type": "general"
                }
                task = self.web_search.execute(search_input, context)
                research_tasks.append(task)
                source_mapping[len(research_tasks) - 1] = "web"
                
            elif source == "news":
                search_input = {
                    "query": query,
                    "max_results": max_results_per_source,
                    "search_type": "news"
                }
                task = self.news_search.execute(search_input, context)
                research_tasks.append(task)
                source_mapping[len(research_tasks) - 1] = "news"
        
        # Execute all searches concurrently
        search_results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Process results by source
        results_by_source = {}
        
        for i, result in enumerate(search_results):
            source_name = source_mapping[i]
            
            if isinstance(result, Exception):
                results_by_source[source_name] = {
                    "error": str(result),
                    "results": []
                }
            elif isinstance(result, ToolResult) and result.success:
                results_by_source[source_name] = {
                    "results": result.data.get("results", []),
                    "total": result.data.get("total_results", 0)
                }
            else:
                results_by_source[source_name] = {
                    "error": result.error if hasattr(result, 'error') else "Unknown error",
                    "results": []
                }
        
        return results_by_source
    
    def _generate_research_summary(self, research_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of research findings"""
        total_results = 0
        sources_with_results = []
        key_findings = []
        
        for source, data in research_results.items():
            if "results" in data and data["results"]:
                total_results += len(data["results"])
                sources_with_results.append(source)
                
                # Extract key findings from top results
                for result in data["results"][:2]:  # Top 2 from each source
                    key_findings.append({
                        "source": source,
                        "title": result.get("title", ""),
                        "relevance": result.get("relevance_score", 0)
                    })
        
        return {
            "total_results": total_results,
            "sources_with_results": sources_with_results,
            "key_findings": sorted(key_findings, key=lambda x: x["relevance"], reverse=True)[:5],
            "research_completeness": len(sources_with_results) / len(research_results) if research_results else 0
        }
