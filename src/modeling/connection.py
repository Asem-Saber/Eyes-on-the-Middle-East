from src.config import CONFIG, get_setting


def settings():
    config = CONFIG.get("warehouse", {})
    return {
        "connect_timeout": 10,
        "host": get_setting("DWH_HOST", config.get("host", "localhost")),
        "port": int(get_setting("DWH_PORT", config.get("port", 5433))),
        "dbname": get_setting("DWH_DATABASE", config.get("database", "news_dwh")),
        "user": get_setting("DWH_USER", config.get("user", "news_admin")),
        "password": get_setting("DWH_PASSWORD", config.get("password", "postgres_password")),
    }
