"""
SearchGraph - Dedicated workflow for web search operations
Handles query analysis, web search execution, and result synthesis
"""

import time
import logging
from typing import Dict, Any
from datetime import datetime

from .base import BaseWorkflow, WorkflowState, WorkflowError
from app.core.websocket import websocket_manager

logger = logging.getLogger(__name__)


class SearchGraph(BaseWorkflow):
    """Dedicated graph for web search operations"""
    
    def __init__(self):
        from .base import WorkflowType
        super().__init__(WorkflowType.SEARCH)
    
    def get_workflow_name(self) -> str:
        return "search_workflow"
    
    def define_nodes(self) -> Dict[str, Any]:
        """Define workflow nodes"""
        return {
            "query_analyzer": self.query_analyzer_node,
            "web_search": self.web_search_node,
            "result_synthesizer": self.result_synthesizer_node,
            "result_processor": self.result_processor_node,
            "error_handler": self.error_handler_node
        }
    
    def define_edges(self) -> list:
        """Define workflow edges"""
        return [
            ("query_analyzer", "web_search"),
            ("web_search", "result_synthesizer"),
            ("result_synthesizer", "result_processor"),
            ("error_handler", "result_processor")
        ]
    
    def get_entry_point(self) -> str:
        return "query_analyzer"
    
    def get_entry_nodes(self) -> list:
        """Override to use query_analyzer as entry point instead of input_validator"""
        return ["query_analyzer"]
    
    async def query_analyzer_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze and optimize the search query"""
        state["current_node"] = "query_analyzer"
        state["visited_nodes"].append("query_analyzer")
        
        query = state["input_data"].get("query", "")
        user_id = state.get("user_id", "unknown")
        workflow_id = state.get("trace_id", "unknown")
        
        print(f"🔍 [QUERY ANALYZER] Analyzing search query: '{query}' for user: {user_id}")
        print(f"🔍 [QUERY ANALYZER] State keys: {list(state.keys())}")
        
        # Emit node start event
        await websocket_manager.emit_node_update(workflow_id, "query_analyzer", "executing")
        
        if not query:
            print("❌ [QUERY ANALYZER] Empty query provided")
            state["error"] = "Empty search query"
            state["next_node"] = "error_handler"
            await websocket_manager.emit_node_update(workflow_id, "query_analyzer", "failed", {"error": "Empty search query"})
            return state
        
        try:
            # Clean and optimize the search query
            cleaned_query = self._clean_search_query(query)
            search_params = self._determine_search_params(cleaned_query)
            
            state["search_data"] = {
                "original_query": query,
                "cleaned_query": cleaned_query,
                "search_params": search_params,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"🔍 [QUERY ANALYZER] Query optimized: '{cleaned_query}'")
            print(f"🔍 [QUERY ANALYZER] Set search_data: {state['search_data']}")
            print(f"🔍 [QUERY ANALYZER] Returning state with keys: {list(state.keys())}")
            
            # Emit node completion event
            await websocket_manager.emit_node_update(workflow_id, "query_analyzer", "completed", {
                "cleaned_query": cleaned_query,
                "search_params": search_params
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            state["error"] = str(e)
            state["next_node"] = "error_handler"
            await websocket_manager.emit_node_update(workflow_id, "query_analyzer", "failed", {"error": str(e)})
            return state
    
    async def web_search_node(self, state: WorkflowState) -> WorkflowState:
        """Execute web search using WebSearchTool"""
        state["current_node"] = "web_search"
        state["visited_nodes"].append("web_search")
        
        search_data = state["search_data"]
        query = search_data["cleaned_query"]
        user_id = state.get("user_id", "unknown")
        workflow_id = state.get("trace_id", "unknown")
        
        print(f"🔍 [WEB SEARCH] Searching for: '{query}'")
        
        # Emit node start and tool execution events
        await websocket_manager.emit_node_update(workflow_id, "web_search", "executing")
        await websocket_manager.emit_tool_update(workflow_id, "WebSearchTool", "executing")
        
        try:
            # Import and initialize web search tool
            from ..tools.web_search import WebSearchTool
            web_search_tool = WebSearchTool()
            
            # Prepare search input with optimized parameters
            search_input = {
                "query": query,
                "max_results": search_data["search_params"]["max_results"],
                "search_depth": search_data["search_params"]["search_depth"],
                "include_answer": True,
                "include_raw_content": False
            }
            
            # Execute web search
            search_result = await web_search_tool.execute(
                search_input, 
                {"user_id": user_id, "workflow": "search"}
            )
            
            if search_result.success:
                state["search_data"]["search_results"] = search_result.data
                state["search_data"]["search_successful"] = True
                state["search_data"]["execution_time"] = search_result.execution_time
                
                print(f"🔍 [WEB SEARCH] Found {len(search_result.data.get('results', []))} results")
                
                # Emit tool completion and node completion events
                await websocket_manager.emit_tool_update(
                    workflow_id, 
                    "WebSearchTool", 
                    "completed", 
                    f"Found {len(search_result.data.get('results', []))} results",
                    search_result.execution_time
                )
                await websocket_manager.emit_node_update(workflow_id, "web_search", "completed", {
                    "results_count": len(search_result.data.get('results', [])),
                    "execution_time": search_result.execution_time
                })
                
            else:
                state["search_data"]["search_successful"] = False
                state["search_data"]["search_error"] = search_result.error
                print(f"❌ [WEB SEARCH] Search failed: {search_result.error}")
                
                # Emit tool and node failure events
                await websocket_manager.emit_tool_update(workflow_id, "WebSearchTool", "failed", search_result.error)
                await websocket_manager.emit_node_update(workflow_id, "web_search", "failed", {"error": search_result.error})
            
            return state
            
        except Exception as e:
            logger.error(f"Web search execution failed: {e}")
            state["error"] = str(e)
            state["next_node"] = "error_handler"
            await websocket_manager.emit_tool_update(workflow_id, "WebSearchTool", "failed", str(e))
            await websocket_manager.emit_node_update(workflow_id, "web_search", "failed", {"error": str(e)})
            return state
    
    async def result_synthesizer_node(self, state: WorkflowState) -> WorkflowState:
        """Synthesize and format search results"""
        state["current_node"] = "result_synthesizer"
        state["visited_nodes"].append("result_synthesizer")
        
        search_data = state["search_data"]
        original_query = search_data["original_query"]
        workflow_id = state.get("trace_id", "unknown")
        
        # Debug: Log the trace_id to see what's happening
        print(f"🔍 [DEBUG] Result synthesizer - trace_id from state: {state.get('trace_id')}")
        print(f"🔍 [DEBUG] Result synthesizer - workflow_id being used: {workflow_id}")
        
        print(f"🔍 [RESULT SYNTHESIZER] Processing results for: '{original_query}'")
        
        # Emit node start event
        await websocket_manager.emit_node_update(workflow_id, "result_synthesizer", "executing")
        
        try:
            if not search_data.get("search_successful"):
                # Handle failed search
                error_msg = search_data.get("search_error", "Search failed")
                state["output_data"] = {
                    "workflow_type": "search",
                    "message": f"I encountered an issue while searching for '{original_query}'. {error_msg}",
                    "search_results": [],
                    "query": original_query,
                    "success": False,
                    "error": error_msg
                }
                return state
            
            # Process successful search results
            search_results = search_data["search_results"]
            results = search_results.get("results", [])
            answer = search_results.get("answer", "")
            
            # Format results for display
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": self._truncate_snippet(result.get("content", "")),
                    "source": result.get("source", ""),
                    "score": result.get("score", 0.0),
                    "favicon": result.get("favicon")
                })
            
            # Generate targeted LLM synthesis based on user's specific question
            synthesis_message = self._generate_targeted_synthesis(original_query, formatted_results, answer)
            
            # Add follow-up suggestions if available
            follow_ups = search_results.get("follow_up_questions", [])
            
            state["output_data"] = {
                "workflow_type": "search",
                "message": synthesis_message,
                "search_results": formatted_results,
                "search_answer": answer,
                "follow_up_questions": follow_ups,
                "query": original_query,
                "total_results": len(results),
                "execution_time": search_data.get("execution_time", 0),
                "success": True
            }
            
            print(f"🔍 [RESULT SYNTHESIZER] Synthesized response with {len(formatted_results)} results")
            
            # Emit search results via WebSocket
            print(f"🔍 [WEBSOCKET] Emitting search results for workflow {workflow_id}")
            print(f"🔍 [WEBSOCKET] Results: {len(formatted_results)} items, synthesis: {len(synthesis_message)} chars")
            
            await websocket_manager.emit_search_results(workflow_id, {
                "search_results": formatted_results,
                "search_answer": synthesis_message,
                "follow_up_questions": follow_ups,
                "query": original_query,
                "total_results": len(results),
                "execution_time": search_data.get("execution_time", 0),
                "success": True
            })
            
            print(f"🔍 [WEBSOCKET] Search results emitted successfully")
            
            # Emit node completion event
            await websocket_manager.emit_node_update(workflow_id, "result_synthesizer", "completed", {
                "results_count": len(formatted_results),
                "synthesis_length": len(synthesis_message)
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Result synthesis failed: {e}")
            state["error"] = str(e)
            state["next_node"] = "error_handler"
            await websocket_manager.emit_node_update(workflow_id, "result_synthesizer", "failed", {"error": str(e)})
            return state
    
    async def result_processor_node(self, state: WorkflowState) -> WorkflowState:
        """Process and finalize results"""
        state["current_node"] = "result_processor"
        state["visited_nodes"].append("result_processor")
        
        workflow_id = state.get("trace_id", "unknown")
        
        print(f"🔍 [RESULT PROCESSOR] Finalizing search results")
        
        # Emit node start event
        await websocket_manager.emit_node_update(workflow_id, "result_processor", "executing")
        
        # Add metadata
        if "output_data" in state:
            state["output_data"]["metadata"] = {
                "workflow": "search",
                "nodes_visited": state["visited_nodes"],
                "processing_time": time.time() - state.get("start_time", time.time()),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        state["status"] = "completed"
        
        # Emit final workflow completion event
        await websocket_manager.emit_workflow_status(workflow_id, "completed", state.get("output_data"))
        await websocket_manager.emit_node_update(workflow_id, "result_processor", "completed")
        
        return state
    
    async def error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle workflow errors"""
        state["current_node"] = "error_handler"
        state["visited_nodes"].append("error_handler")
        
        error = state.get("error", "Unknown error occurred")
        query = state.get("input_data", {}).get("query", "unknown query")
        workflow_id = state.get("trace_id", "unknown")
        
        print(f"❌ [ERROR HANDLER] Handling search error: {error}")
        
        # Emit error events
        await websocket_manager.emit_node_update(workflow_id, "error_handler", "executing")
        
        state["output_data"] = {
            "workflow_type": "search",
            "message": f"I encountered an unexpected error while searching for '{query}'. Please try again with a different query.",
            "search_results": [],
            "query": query,
            "success": False,
            "error": error,
            "metadata": {
                "workflow": "search",
                "nodes_visited": state["visited_nodes"],
                "error_occurred": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        state["status"] = "failed"
        
        # Emit workflow failure events
        await websocket_manager.emit_workflow_status(workflow_id, "failed", state.get("output_data"))
        await websocket_manager.emit_node_update(workflow_id, "error_handler", "completed")
        
        return state
    
    def _generate_targeted_synthesis(self, original_query: str, search_results: list, answer: str) -> str:
        """Generate targeted synthesis that directly answers the user's specific question"""
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        
        # Prepare search results context
        results_context = ""
        for i, result in enumerate(search_results[:5], 1):
            results_context += f"Source {i} ({result['source']}):\n"
            results_context += f"Title: {result['title']}\n"
            results_context += f"Content: {result['snippet']}\n\n"
        
        prompt = f"""
        Based on the search results below, provide a targeted response to answer this user's specific question: "{original_query}"

        Search Results:
        {results_context}

        Instructions:
        1. Answer the user's EXACT question format - don't provide generic summaries
        2. If they ask for specific facts/numbers (e.g., "3 monkey facts"), give exactly that format
        3. If they ask "what is X?", give a concise definition/explanation
        4. If they ask "how to X?", give step-by-step guidance
        5. Always include source attribution in parentheses like (source.com)
        6. Keep it concise and directly relevant to their question
        7. Don't list all search results - synthesize information to answer their question

        Examples:
        - Query: "Give me 3 monkey facts" → Response: "Here are 3 monkey facts: 1. [fact with source] 2. [fact with source] 3. [fact with source]"
        - Query: "What is photosynthesis?" → Response: "Photosynthesis is [concise definition] (source.com). [Additional key details] (source2.com)."
        - Query: "How to bake a cake?" → Response: "To bake a cake: 1. [step] 2. [step] 3. [step] (source.com)"

        Provide a natural, conversational response that directly addresses their question:
        """
        
        try:
            response = llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"❌ [SYNTHESIS] LLM synthesis failed: {e}")
            # Fallback to simple answer if available
            if answer:
                return f"Based on my search: {answer}"
            else:
                return f"I found information about '{original_query}' from {len(search_results)} sources. Check the search results above for details."

    def _clean_search_query(self, query: str) -> str:
        """Clean and optimize search query"""
        # Remove common search prefixes
        prefixes_to_remove = [
            "search for ", "search the web for ", "look up ", "find information about ",
            "find ", "search ", "google ", "look for "
        ]
        
        cleaned = query.lower().strip()
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Capitalize properly
        return cleaned.strip()
    
    def _determine_search_params(self, query: str) -> Dict[str, Any]:
        """Determine optimal search parameters based on query"""
        params = {
            "max_results": 5,
            "search_depth": "basic"
        }
        
        # Adjust based on query characteristics
        if len(query.split()) > 10:  # Complex queries
            params["max_results"] = 8
            params["search_depth"] = "advanced"
        elif any(word in query.lower() for word in ["recent", "latest", "new", "current"]):
            params["max_results"] = 6
            params["search_depth"] = "basic"
        
        return params
    
    def _truncate_snippet(self, content: str, max_length: int = 150) -> str:
        """Truncate content snippet to readable length"""
        if not content:
            return ""
        
        if len(content) <= max_length:
            return content
        
        # Find last complete sentence or word within limit
        truncated = content[:max_length]
        last_period = truncated.rfind('.')
        last_space = truncated.rfind(' ')
        
        if last_period > max_length * 0.8:  # If period is reasonably close to end
            return content[:last_period + 1]
        elif last_space > max_length * 0.8:  # If space is reasonably close to end
            return content[:last_space] + "..."
        else:
            return truncated + "..."