import json
import logging
import time
import traceback
from datetime import datetime

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

from config import Config
from data import Network, NetworkStatRecord, StorageStatRecord
from hyper_v_logger import HyperVLogger
from util.common import logging_config
from util.orm import Session


def main():
    NetworkStatRecord.create_table_if_not_exist()
    StorageStatRecord.create_table_if_not_exist()

    with Session() as db_session:
        logger = HyperVLogger(db_session, Config.HYPER_V_LOG_INTERVAL)
        logger.start()

    with Session() as db_session:
        client = make_client(db_session)
        client.loop_forever()


def make_client(db_session: Session) -> mqtt.Client:
    client = mqtt.Client(client_id='stat-client', protocol=mqtt.MQTTv5)

    client.on_connect = lambda *args: client.subscribe(Config.MQTT['topic'], qos=2)
    client.on_message = lambda _, __, msg: handle_message(db_session, msg)

    properties = Properties(PacketTypes.CONNECT)
    properties.SessionExpiryInterval = Config.MQTT['session_expiry_interval']

    client.connect(Config.MQTT['host'], Config.MQTT['port'], clean_start=False, properties=properties)

    logging.info('# MQTT subscribed.')
    return client


def handle_message(session: Session, msg: mqtt.MQTTMessage):
    logging.info(f'# Get new message.')

    try:
        timestamp = int(dict(msg.properties.UserProperty).get('timestamp', time.time()))
        the_time = datetime.fromtimestamp(timestamp)

        data = json.loads(msg.payload)
        count = 0

        for k, v in data.items():
            if isinstance(v, dict) and 'ip_list' in v:
                records = parse_records(v, the_time)
                session.add_all(records)
                count += len(records)

        session.commit()

        logging.info(f'# {count} new records added.')

    except Exception as e:
        logging.error(f'# Error when handling message, {msg=}:')

        for attr in dir(msg):
            if not attr.startswith('_'):
                logging.error(f'    >> {attr}: {getattr(msg, attr)}')

        traceback.print_exc()


def parse_records(data: dict, the_time: datetime) -> list[NetworkStatRecord]:
    network = Network.parse(data['ifname'])
    device = data['hostname']

    records = []

    for ip_data in data['ip_list']:
        ip = ip_data['ip']
        mac = ip_data['hw']
        rx_rate = ip_data['rx_rate']
        tx_rate = ip_data['tx_rate']

        if rx_rate > 0 or tx_rate > 0:
            record = NetworkStatRecord(ip=ip, mac=mac, network=network, device=device, rx_rate=rx_rate, tx_rate=tx_rate, timestamp=the_time)
            records.append(record)

    return records


if __name__ == '__main__':
    logging_config()
    main()
