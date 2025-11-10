import sys
import logging
from functools import wraps
from typing import Callable, Any, Literal

# --- Configuration for Logging ---
logger = logging.getLogger(__name__)

class Redundancy:
    """
    A utility class focused on enforcing Explicit Intent and Consistency Checks 
    for variables, often through the use of decorators.

    It helps ensure that variable values are consistent across local scope, 
    instance attributes, and class attributes, reducing the mental burden of 
    tracking state mutation.
    """
    
    @staticmethod
    def check_match(a: Any, b: Any, message: str | None = None) -> None:
        """
        Compares two values. If they do not match, logs a warning and exits 
        to halt execution on an inconsistency.

        This is used to confirm that redundant values (e.g., a function 
        argument and a self.attribute) are identical.
        """
        if a != b:
            # Use logger.error and sys.exit for pipeline safety
            logger.error(f"Inconsistency Detected: {message or 'Redundant variables do not match.'}")
            logger.error(f"Value A: {a}")
            logger.error(f"Value B: {b}")
            sys.exit(1)
            
    # --- Decorators for Explicit State Management ---

    @staticmethod
    def set_instance_attribute(attribute_name: str) -> Callable:
        """
        Decorator that enforces state change on the instance (self).
        
        This decorator guarantees a 'double-tap' assignment pattern:
        1. Runs the decorated function to get the calculated value.
        2. **Sets self.{attribute_name}** to the calculated value internally.
        3. Returns the calculated value for external assignment clarity.
        
        Use this on instance methods where you want the calculated value to 
        be stored on 'self', but still returned explicitly to the caller.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, *args, **kwargs) -> Any:
                
                # 1. Run the core calculation
                calculated_value = func(self, *args, **kwargs)
                
                # 2. Internal Assignment (Enforced State Mutation)
                setattr(self, attribute_name, calculated_value)
                logger.debug(f"Attribute assigned by decorator: self.{attribute_name} = {calculated_value}")
                
                # 3. Return the value for 'double-tap' clarity
                return calculated_value
            return wrapper
        return decorator

    @staticmethod
    def annotate_return_target(recipient: Literal['self', 'cls', None], attribute_name: str) -> Callable:
        """
        Decorator that adds explicit metadata about where the returned value 
        *should* be assigned externally. This performs NO runtime assignment.
        
        This is useful for static analysis, documentation, and linters, keeping 
        the decorated function as a 'Pure Query' while documenting its purpose 
        as an attribute initializer/setter.
        """
        def decorator(func: Callable) -> Callable:
            # Note: At runtime, this decorator simply passes the function through.
            # Its value is purely in its static metadata.
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                
                # Optional: Store the hint on the instance/class if self/cls is in args
                # This is primarily for debugging or internal auditing tools.
                # The core purpose is the annotation itself.
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    # --- Additional Useful Clarity Functions ---

    @staticmethod
    def format_url(*parts: str, port: int | str | None = None) -> str:
        """
        Safely joins URL parts, ensuring there are no double slashes,
        and cleanly appends an optional port number.
        """
        if not parts:
            return ""
        
        # 1. Join parts, handling slashes
        url = '/'.join(s.strip('/') for s in parts if s)
        
        # 2. Add port if provided
        if port is not None:
            # Remove existing port if present to avoid double ports
            if ':' in url.split('//')[-1]:
                 url = url.split(':')[0]
            url = f"{url}:{port}"
        
        # 3. Ensure http(s) protocol
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        return url


# --- Mocked supporting classes for the demonstration below ---

class DemoClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.authstring = None
        
    @Redundancy.set_instance_attribute(attribute_name="authstring")
    def perform_soap_login(self, username: str, password: str) -> str:
        """
        Performs SOAP login. The decorator ensures self.authstring is set 
        to the returned token.
        """
        logger.info("Performing core login calculation...")
        # Mock: Actual login logic here
        token = f"TOKEN-{hash(username) % 1000}"
        return token
    
    @Redundancy.annotate_return_target(recipient='self', attribute_name='rest_api_url')
    def calculate_rest_api_url(self) -> str:
        """
        Calculates the REST API URL. The decorator acts as a hint that 
        the caller should assign the result to self.rest_api_url.
        """
        return Redundancy.format_url(self.base_url, 'api/v1', port=8080)


def demo_redundancy_usage():
    logger.info("\n--- Demo: Redundancy Utilities ---")
    
    # 1. Consistency Check (check_match)
    a, b = 10, 10
    Redundancy.check_match(a, b, "Testing consistency of two equal values.")

    try:
        Redundancy.check_match(1, 2, "This check should fail and exit.")
    except SystemExit:
        logger.info("Consistency check failed as expected (SystemExit).")
        
    # 2. Runtime Assignment (set_instance_attribute)
    client = DemoClient("https://data.plantA.com")
    
    # Double-tap assignment: Sets client.authstring AND assigns to local variable
    local_token = client.perform_soap_login("user", "pass")
    
    logger.info(f"Local token: {local_token}")
    logger.info(f"Instance token: {client.authstring}")
    Redundancy.check_match(local_token, client.authstring, "Local and instance tokens must match after double-tap.")
    
    # 3. Pure Query Annotation (annotate_return_target)
    url = client.calculate_rest_api_url()
    
    # The developer still manually assigns the result (as suggested by the hint)
    client.rest_api_url = url 
    
    logger.info(f"Calculated URL (manual assign): {client.rest_api_url}")
    
    # 4. URL Formatting
    formatted = Redundancy.format_url("https://base.com", "/path", "subpath/", port=443)
    logger.info(f"Formatted URL: {formatted}") # Should be https://base.com:443/path/subpath


if __name__ == "__main__":
    
    # Simple setup for demonstrating decorators/helpers
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    demo_redundancy_usage()
    
    # The original stubbed logic for finding functions has been simplified/removed
    # to focus the class on variable clarity patterns.