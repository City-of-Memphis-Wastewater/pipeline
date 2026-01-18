import pipeline_eds.config_loader as config_loader  # adjust to actual file

'''
Out here spoofing.
'''

def test_default_config_loads():
    config = config_loader.load_default_config()
    assert isinstance(config, dict)
    assert "workspace" in config  # adjust key names as needed
