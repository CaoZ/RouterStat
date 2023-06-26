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
