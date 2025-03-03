import yaml
import psycopg2
import os

def get_db_connection(config_path=None):
    
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "config.yaml")
    
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    
    db_cfg = cfg["database"]
    
    conn = psycopg2.connect(
        dbname=db_cfg["name"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        host=db_cfg["host"],
        port=db_cfg["port"]
    )
    return conn
