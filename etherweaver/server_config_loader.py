import yaml

def get_server_config(config_path="/etc/etherweaver/server_config.yml"):
    '''
    :param config_path: path to server config yaml file
    :return: dict
    '''
    with open(config_path, 'r') as f:
        config = f.read()
        return yaml.safe_load(config)
