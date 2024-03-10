class Config:
    DB = {
        'db': 'home',
        'host': 'localhost',
        'user': 'root',
        'password': 'password'
    }

    MQTT = {
        'host': '192.168.1.1',
        'port': 1883,
        'topic': 'home/router-stat',
        'session_expiry_interval': 86400 * 10
    }

    Hyper_V_VIRTUAL_MACHINES = {
        'BspOne': '192.168.1.31',
        'BspTwo': '192.168.1.32',
        'DianXinV': '192.168.1.33'
    }

    HYPER_V_LOG_INTERVAL = 60
