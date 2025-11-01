# src/pipeline_tests/variable_clarity.py
import sys
import logging
from functools import wraps
from typing import Callable, Any

class Redundancy:
    
    """
    The variable is already known to self or to a class that was just born, with the attribute assigned at __init__().
    But, sometimes, it is prudent to be explicit, and repeating a variable passed explicitly into a function is fine.
    Clarity is value.
    Wrangling complex classes is pain.
    Clean functions are bliss.
    Disappearing output assigned internally but with no clear assignment is befuddling, 
    and an irresponsible but occasionally practival way to build spaghetti code and then 
    occasionally eat it with a spoon.

    from pipeline_tests.variable_clarity import Redundancy
    #if 'services_api_url' in locals() and hasattr(client,'services_api_url'): 
    #    Redundancy.compare(client.services_api_url == services_api_url) # already known
    
    Example:
    class Client:
        magic_word
        services_api_url
        
        def __init__(self):
            self.magic_word = magic_word
            self.salted_number = None
            
        def _assign_special_services_api_url(self, services_api_url):
            self.services_api_url = services_api_url
            
        def calc_salted_number(self,magic_number):
            salted_number = magic_number+256
            
            # unnecessary but explicit, commented out, but put this comment in 
            @psuedo_internal_setter_assignment
            def set_salted_number(self,salted_number)
                self.stash_for_future_checking("salted_number",salted_number) 
            
            return salted_number # which is right?
            
    def demo_login_and_get_data(services_api_url):
        client=Client()
        client.salted_number = client.calc_salted_number(magic_number=0)
    
        
    """
    
    def __init__(self):
        self.status = True 
    
    @classmethod
    def check_for_match_of_versions_or_terminate(sources:list=[])->bool:
        if len(sources) == 0:
            return False 
        if len(sources)==2 and (sources[0]!=sources[1]):
            logging.info("These are supposed to match and they do not \
            ")
            sys.exit()
        if len(sources)!=2:
            #if _all_match(sources)
            #return
            # 
            print("There are more than two inputs, \
            which this function is not yet built to handle.")
            return None
        return True
    
    @staticmethod
    def compare(match:bool=True):
        if not match:
            print("Redundancy.compare(): The rigorously documented redundant variable does not match. Beware.")
            sys.exit()

    @staticmethod
    def set_and_return(attribute_name: str) -> Callable:
        """
        Decorator that enforces a 'double-tap' assignment:
        1. Sets self.{attribute_name} to the value returned by the decorated function.
        2. Returns the calculated value for external assignment clarity.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, *args, **kwargs) -> Any:
                
                # 1. Run the core calculation (The Query part)
                calculated_value = func(self, *args, **kwargs)
                
                # 2. Internal Assignment (The Command part, enforced by the decorator)
                # This is where the 'internal assignment suggestion' happens
                # It's no longer a suggestion; it's a guarantee.
                setattr(self, attribute_name, calculated_value)
                
                # 3. Return the value for external assignment clarity (The Double-Tap)
                return calculated_value
            return wrapper
        return decorator

    @staticmethod
    def set_on_return_hint(recipient: str | None, attribute_name: str) -> Callable:
        """
        Decorator for Explicit Query Intent (The safest form of 'double-tap').
        1. Performs NO internal assignment, maintaining the pure Query principle.
        2. Stores the intended recipient and value on the instance for auditing/linter checks.
        3. Returns the calculated value for external assignment clarity.
        
        Requires the class instance to have a self._assignment_hints dictionary.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, *args, **kwargs) -> Any:
                
                # 1. Run the core calculation (The Pure Query part)
                value = func(self, *args, **kwargs)
                
                # 2. Store the Hint on the INSTANCE for auditing
                if not hasattr(self, '_assignment_hints'):
                    # Initializing it here as a fallback, though best practice is __init__
                    self._assignment_hints = {}
                    
                self._assignment_hints[func.__name__] = {
                    "recipient": recipient,
                    "target_attr": attribute_name,
                    "intended_value": value,
                    "hint": f"client.{attribute_name} = client.{func.__name__}()"
                }
                
                # 3. Return the value for external assignment (The necessary return)
                return value
            return wrapper
        return decorator
    

    

def instancemethod(func):
    """
    Decorator that allows explicit clarity about instance methods.
    """
    def wrapper(self, *args, **kwargs):
        return func(self, *args, **kwargs)
    return wrapper

class FindThatFunctionInTheCodeBase:
    pass
class MaintainUsageStatus:
    def __init__(self):
        
        self.status = ""
        
        from pipeline_tests.variable_clarity import compare_routes
        
        if FindThatFunctionInTheCodeBase(function=compare_routes).status() != (compare_routes.__dict__.status):
            logging.info("Your function {compare_routes.__name__} is registered as being used but is not being used. ")
            logging.info("Your function {compare_routes.__name__} is not being used but is registered as being used.")


if __name__ == "__main__":
    status = MaintainUsageStatus()
    logging.info(f"MaintainUsageStatus() = {status}")