#!/usr/bin/env python3
#!/usr/bin/env python
from yaml import load


def parseConfig(self):
    with open('config.yaml', 'r') as f: 
        yaml_config = self.config.read()
    self.parsed_config = yaml.safe_load(yaml_config)
    self.top_sig = self.parsed_config["sig"]
    self.energy = self.parsed_config["energy"]