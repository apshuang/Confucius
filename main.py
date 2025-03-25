from pathlib import Path

from src import *

def init_mapping(yaml_parser: YamlParser):
    for node_name in yaml_parser.get_nodes_name_list():
        database_config: DatabaseConfig = yaml_parser.get_database_config(node_name)
        db = Database(database_config)
        alias_host_dict[node_name] = database_config.host
        alias_database_dict[node_name] = db
        
        chaos_config: ChaosConfig = yaml_parser.get_chaos_config(node_name)
        injector = FaultInjector(chaos_config)
        alias_injector_dict[node_name] = injector
        

def init_databases_and_injectors():
    for node_name, db in alias_database_dict.items():
        db.setupDB()
    for node_name, injector in alias_injector_dict.items():
        injector.connect()
        

def close_databases_and_injectors():
    for node_name, db in alias_database_dict.items():
        try:
            db.teardownDB()
        except Exception as e:
            logging.error(f"Error occured when tearing down db: {str(e)}")
    for node_name, injector in alias_injector_dict.items():
        try:
            injector.close()
        except Exception as e:
            logging.error(f"Error occured when close injector's connection: {str(e)}")   
        
        
def run(mode: str, cluster_config_path: Path, direct_json_path: Path = None):
    yaml_parser = YamlParser(cluster_config_path)
    init_mapping(yaml_parser)
    init_databases_and_injectors()
    
    if mode == "direct":
        with open(direct_json_path, "r", encoding="utf-8") as file:
            plan_data = json.load(file)
    else:
        plan_data = []
    
    plan_parser = PlanParser(plan_data)
    total_time: int = plan_parser.total_time
    for event in plan_parser.events_list:
        if isinstance(event, Nemesis):
            event.inject()
        elif isinstance(event, Workload):
            event.start()
        elif isinstance(event, Check):
            event.start()
    asyncio.sleep(total_time)
    
    close_databases_and_injectors()
    

if __name__ == "__main__":
    mode = "direct"
    cluster_config_path: Path = "E:/Confucius/rqlite_cluster.yaml"
    direct_json_path: Path = "E:/Confucius/plan.json"
    # cluster_config_path: Path = "/home/centos/Confucius/rqlite_cluster.yaml"
    # direct_json_path: Path = "/home/centos/Confucius/plan.json"
    run(mode, cluster_config_path, direct_json_path)