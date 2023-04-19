import json
import logging
import time
from datetime import datetime

import paho.mqtt.client as mqtt

from data import Network, StatRecord
from util.common import logging_config
from util.orm import Session


def main():
    db_session = Session()

    client = mqtt.Client(client_id='stat-client', protocol=mqtt.MQTTv5)

    client.on_message = lambda _, __, msg: handle_message(db_session, msg)

    client.connect('192.168.1.1', 1883)
    client.subscribe('home/router-stat', qos=2)

    logging.info('# MQTT subscribed.')

    client.loop_forever()

    db_session.close()


def handle_message(session: Session, msg: mqtt.MQTTMessage):
    logging.info(f'# Get new message.')

    timestamp = int(dict(msg.properties.UserProperty).get('timestamp', time.time()))
    the_time = datetime.fromtimestamp(timestamp)

    data = json.loads(msg.payload)
    count = 0

    for k, v in data.items():
        if isinstance(v, dict) and 'ip_list' in v:
            records = parse_records(v, the_time)

            for record in records:
                session.add(record)
                count += 1

    session.commit()

    logging.info(f'# {count} new records added.')


def parse_records(data: dict, the_time: datetime):
    network = Network.parse(data['ifname'])
    device = data['hostname']

    records = []

    for ip_data in data['ip_list']:
        ip = ip_data['ip']
        mac = ip_data['hw']
        rx_rate = ip_data['rx_rate']
        tx_rate = ip_data['tx_rate']

        if rx_rate > 0 or tx_rate > 0:
            record = StatRecord(ip=ip, mac=mac, network=network, device=device, rx_rate=rx_rate, tx_rate=tx_rate, timestamp=the_time)
            records.append(record)

    return records


if __name__ == '__main__':
    logging_config()
    main()
