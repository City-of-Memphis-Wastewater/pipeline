import threading
import uuid
from typing import Dict, Any, Optional

class PromptManager:
    """
    Manages the state of active configuration prompts and submitted results.
    Designed to be instantiated once and shared across FastAPI threads.
    """
    def __init__(self):
        # Stores active prompt details waiting for frontend detection
        # Key: request_id (str), Value: prompt_data (Dict[str, Any])
        self.active_prompt_request: Dict[str, Any] = {}
        self.active_prompt_lock = threading.Lock()
        
        # Stores results submitted by the frontend, waiting to unblock Python thread
        # Key: request_id (str), Value: submitted_value (str)
        self.prompt_results: Dict[str, str] = {}
        self.results_lock = threading.Lock()
        
        # Store the dynamically found server URL
        self.server_host_port: str = ""

    def register_prompt(self, key: str, message: str, is_credential: bool) -> str:
        """Stores a new prompt request and returns its ID."""
        request_id = str(uuid.uuid4())
        prompt_data = {
            "request_id": request_id,
            "key": key,
            "message": message,
            "is_credential": is_credential,
        }
        with self.active_prompt_lock:
            # Critical: Ensure only one prompt is active at a time for simplicity
            if self.active_prompt_request:
                 raise RuntimeError("A configuration prompt is already active.")
            self.active_prompt_request[request_id] = prompt_data
        return request_id

    def get_active_prompt(self) -> Optional[Dict[str, Any]]:
        """Retrieves the active prompt data for the frontend."""
        with self.active_prompt_lock:
            if not self.active_prompt_request:
                return None
            
            # Retrieve the single active prompt
            return next(iter(self.active_prompt_request.values()))

    def submit_result(self, request_id: str, value: str):
        """Stores a submitted result and clears the active request."""
        with self.results_lock:
            self.prompt_results[request_id] = value
        
        with self.active_prompt_lock:
            self.active_prompt_request.pop(request_id, None)

    def get_and_clear_result(self, request_id: str) -> Optional[str]:
        """Retrieves a result and removes it to unblock the waiting thread."""
        with self.results_lock:
            return self.prompt_results.pop(request_id, None)

    def set_server_host_port(self, host_port_str: str):
        """Sets the dynamically found server host and port."""
        self.server_host_port = host_port_str
        
    def get_server_url(self) -> str:
        """Returns the full server URL."""
        if not self.server_host_port:
             return "http://127.0.0.1:8083" 
        return f"http://{self.server_host_port}"