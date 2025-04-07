import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

class ResearchPersistence:
    """
    Handles persistence of research progress and results.
    Allows for saving and loading research state to enable resuming interrupted research.
    """
    
    def __init__(self, data_dir: str = "research_data"):
        """
        Initialize the persistence manager.
        
        Args:
            data_dir: Directory to store research data
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def save_search_plan(self, query: str, search_plan: Dict[str, Any]) -> str:
        """
        Save a search plan to disk.
        
        Args:
            query: The research query
            search_plan: The search plan data
            
        Returns:
            The ID of the saved research session
        """
        session_id = self._generate_session_id(query)
        data = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "search_plan": search_plan,
            "status": "planned"
        }
        
        self._save_session_data(session_id, data)
        return session_id
    
    def save_search_results(self, session_id: str, search_results: List[str]) -> None:
        """
        Save search results to disk.
        
        Args:
            session_id: The research session ID
            search_results: The search results
        """
        data = self._load_session_data(session_id)
        if data:
            data["search_results"] = search_results
            data["status"] = "searched"
            self._save_session_data(session_id, data)
    
    def save_report(self, session_id: str, report_data: Dict[str, Any]) -> None:
        """
        Save a final report to disk.
        
        Args:
            session_id: The research session ID
            report_data: The report data
        """
        data = self._load_session_data(session_id)
        if data:
            data["report"] = report_data
            data["status"] = "completed"
            self._save_session_data(session_id, data)
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get data for a research session.
        
        Args:
            session_id: The research session ID
            
        Returns:
            The session data, or None if not found
        """
        return self._load_session_data(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all research sessions.
        
        Returns:
            A list of session metadata
        """
        sessions = []
        if not os.path.exists(self.data_dir):
            return sessions
            
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]  # Remove .json extension
                data = self._load_session_data(session_id)
                if data:
                    sessions.append({
                        "session_id": session_id,
                        "query": data.get("query", "Unknown"),
                        "timestamp": data.get("timestamp", "Unknown"),
                        "status": data.get("status", "Unknown")
                    })
        
        # Sort by timestamp, newest first
        sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return sessions
    
    def _generate_session_id(self, query: str) -> str:
        """Generate a unique session ID based on the query and timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # Create a simplified version of the query for the filename
        query_part = "".join(c if c.isalnum() else "_" for c in query[:30])
        return f"{timestamp}_{query_part}"
    
    def _get_session_path(self, session_id: str) -> str:
        """Get the file path for a session."""
        return os.path.join(self.data_dir, f"{session_id}.json")
    
    def _save_session_data(self, session_id: str, data: Dict[str, Any]) -> None:
        """Save session data to disk."""
        with open(self._get_session_path(session_id), "w") as f:
            json.dump(data, f, indent=2)
    
    def _load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from disk."""
        path = self._get_session_path(session_id)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None
        return None
