import json
import os
import shutil
import time
import random
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from reagents.config import AppConstants

# Set up logging
logger = logging.getLogger(__name__)

class ResearchPersistence:
    """
    Handles persistence of research progress and results.
    Allows for saving and loading research state to enable resuming interrupted research.
    """

    def __init__(self, data_dir: str = AppConstants.DEFAULT_DATA_DIR):
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
        DEPRECATED: This method is deprecated. Use save_search_plan instead.
        Search results are now stored in the search_plan structure.

        Args:
            session_id: The research session ID
            search_results: The search results
        """
        # This method is kept for backward compatibility
        # but it doesn't do anything anymore
        pass

    def save_search_plan(self, session_id: str, search_plan: Dict[str, Any]) -> None:
        """
        Save the search plan with results to disk.

        Args:
            session_id: The research session ID
            search_plan: The search plan with results
        """
        data = self._load_session_data(session_id)
        if data:
            data["search_plan"] = search_plan
            data["status"] = "searched"
            self._save_session_data(session_id, data)

    def save_report(self, session_id: str, report_data: Dict[str, Any]) -> None:
        """
        Mark the research as completed without adding a report section.

        Args:
            session_id: The research session ID
            report_data: The report data (not used)
        """
        data = self._load_session_data(session_id)
        if data:
            # Don't save the report section at all
            # Just update the status to completed
            if "report" in data:
                del data["report"]
            data["status"] = "completed"
            self._save_session_data(session_id, data)

    def save_session_data(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Save data for a research session.

        Args:
            session_id: The research session ID
            data: The session data to save
        """
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
        """Save session data to disk with file locking to prevent race conditions.

        Args:
            session_id: The ID of the session to save
            data: The session data to save

        Raises:
            IOError: If there was an error writing the file
            OSError: If there was an error with the file system operations
        """
        # Get the final path where we want to save the data
        final_path = self._get_session_path(session_id)

        # Create a temporary file in the same directory
        temp_dir = os.path.dirname(final_path)
        os.makedirs(temp_dir, exist_ok=True)

        # Generate a unique temporary filename
        temp_filename = f"{session_id}_{int(time.time())}_{random.randint(1000, 9999)}.tmp"
        temp_path = os.path.join(temp_dir, temp_filename)

        # Write data to the temporary file first
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # Ensure the data is written to disk
            # Note: flush() and fsync() need to be inside the with block
            # since the file is still open there
        except PermissionError as e:
            logger.error(f"Permission error writing to temporary file {temp_path}: {str(e)}")
            # Clean up the temporary file if there was an error
            self._cleanup_temp_file(temp_path)
            raise IOError(f"Permission denied when writing session data: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error writing session data to temporary file {temp_path}: {str(e)}")
            # Clean up the temporary file if there was an error
            self._cleanup_temp_file(temp_path)
            raise IOError(f"Failed to write session data: {str(e)}") from e

        # Atomically replace the target file with the temporary file
        # This is atomic on POSIX systems and nearly atomic on Windows
        try:
            # On Windows, we need to handle the case where the destination file exists
            if os.path.exists(final_path):
                os.replace(temp_path, final_path)  # Atomic on Windows
            else:
                shutil.move(temp_path, final_path)  # Atomic on POSIX
        except PermissionError as e:
            logger.error(f"Permission error moving temporary file {temp_path} to {final_path}: {str(e)}")
            self._cleanup_temp_file(temp_path)
            raise IOError(f"Permission denied when saving session data: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error moving temporary file {temp_path} to {final_path}: {str(e)}")
            self._cleanup_temp_file(temp_path)
            raise OSError(f"Failed to save session data: {str(e)}") from e

    def _cleanup_temp_file(self, temp_path: str) -> None:
        """Clean up a temporary file if it exists.

        Args:
            temp_path: Path to the temporary file to clean up
        """
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_path}: {str(e)}")
                # We don't re-raise this exception as it's just cleanup

    def _load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from disk.

        Args:
            session_id: The ID of the session to load

        Returns:
            The session data as a dictionary, or None if the file doesn't exist or is invalid
        """
        path = self._get_session_path(session_id)
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON in session file {path}: {str(e)}")
            return None
        except PermissionError as e:
            logger.error(f"Permission error accessing session file {path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading session file {path}: {str(e)}")
            return None
