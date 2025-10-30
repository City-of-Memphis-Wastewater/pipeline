# src/pipeline_tests/variable_clarity.py
import sys
import logging

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
    
    Example:
    class Client:
        magic_word
        services_api_url
        
        def __init__(self):
            self.magic_number = magic_number
            self.services_api_url = None
            
        def _assign_services_api_url(self):
            self.services_api_url = services_api_url
            
        def foo(self,magic_number):
            compare_routes(client.services_api_url == services_api_url) # already known, ensure it
            
    def demo_login_and_get_data(services_api_url):
    
    """
    def __dict__(self):
        """
        Track explicity if the function is currently in service or not.
        Just because it is not in service, it does not mean delete it.
        """
      
        self.known_uses: list[str] = ['pipline.api.mission.demo_retrieve_analog_data_and_save_csv()','']
    
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
            
    def compare(match:bool=True):
        if not match:
            print("Redundancy.compare(): The rigorously documented redundant variable does not match. Beware.")
            sys.exit()

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