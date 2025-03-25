class DatabaseConfig:
    name: str
    host: str
    api_port: int
    ssh_port: int
    db_username: str
    db_password: str
    retry_count: int
    
    def __init__(self, name: str, host: str, api_port: int, ssh_port: int = 22,
                 db_username: str = "centos", db_password: str = "password", retry_count: int = 3):
        self.name = name
        self.host = host
        self.api_port = api_port
        self.ssh_port = ssh_port
        self.db_username = db_username
        self.db_password = db_password
        self.retry_count = retry_count

    def __str__(self):
        return (f"Database_Config({self.name}: host={str(self.host)}, ssh_port={self.ssh_port}, "
                f"api_port={self.api_port}, db_username={self.db_username})")
        
        
class ChaosConfig:
    name: str
    host: str
    ssh_port: int
    chaos_username: str
    chaos_password: str
    retry_count: int
    
    def __init__(self, name: str, host: str, ssh_port: int = 22, chaos_username: str = "root",
                  chaos_password: str = "password", retry_count: int = 3):
        self.name = name
        self.host = host
        self.ssh_port = ssh_port
        self.chaos_username = chaos_username
        self.chaos_password = chaos_password
        self.retry_count = retry_count

    def __str__(self):
        return (f"Chaos_Config({self.name}: host={self.host}, ssh_port={self.ssh_port}, chaos_username={self.chaos_username}")
    

alias_host_dict: dict[str, str] = {}