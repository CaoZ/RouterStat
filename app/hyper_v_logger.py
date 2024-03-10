import locale
import logging
import re
import subprocess
import time
from collections import defaultdict, Counter
from collections.abc import Callable
from datetime import datetime
from threading import Thread

from sqlalchemy.orm import Session

from config import Config
from data import Network, Storage, NetworkStatRecord, StorageStatRecord
from util.orm import Base

VIRTUAL_MACHINES = Config.Hyper_V_VIRTUAL_MACHINES

NETWORK_MAP = {
    'Bytes Sent': NetworkStatRecord.tx_rate,
    'Bytes Received': NetworkStatRecord.rx_rate
}

STORAGE_MAP = {
    'Read Bytes': StorageStatRecord.read_rate,
    'Write Bytes': StorageStatRecord.write_rate
}

PATTERN_NETWORK = re.compile(rf'Network Adapter\((\w+?)_.*({"|".join(NETWORK_MAP.keys())})')
PATTERN_STORAGE = re.compile(rf'Storage Device.*-(\w+?)(Data.*)?\.vhdx.*({"|".join(STORAGE_MAP.keys())})')

COUNTERS_NETWORK = [rf'\Hyper-V Virtual Network Adapter({vm}_*)\{op}/sec' for vm in VIRTUAL_MACHINES for op in NETWORK_MAP]
COUNTERS_STORAGE = [rf'\Hyper-V Virtual Storage Device(*{vm}*)\{op}/sec' for vm in VIRTUAL_MACHINES for op in STORAGE_MAP]

COMMAND_NETWORK = ['typeperf', '-sc', '1', *COUNTERS_NETWORK]
COMMAND_STORAGE = ['typeperf', '-sc', '1', *COUNTERS_STORAGE]


class HyperVLogger:
    def __init__(self, db_session: Session, log_interval: int):
        self.db_session = db_session
        self.log_interval = log_interval
        self.log_thread = Thread(target=self.log_forever)

    def log_forever(self):
        while True:
            start = time.monotonic()

            network_stats = get_network_stats()
            storage_stats = get_storage_stats()

            self.db_session.add_all(network_stats)
            self.db_session.add_all(storage_stats)

            try:
                self.db_session.commit()
                logging.info(f'# {len(network_stats) + len(storage_stats)} new Hyper-V records added.')

            except Exception as e:
                logging.error(f'# Error when updating db: ', e)
                self.db_session.rollback()

            wait_time = max(self.log_interval - (time.monotonic() - start), 0)
            time.sleep(wait_time)

    def start(self):
        self.log_thread.start()


def get_network_stats():
    """
    网络上传 / 下载速度信息
    """
    return get_stats(COMMAND_NETWORK, PATTERN_NETWORK, parse_network_records)


def get_storage_stats():
    """
    硬盘读取 / 写入速度信息
    """
    return get_stats(COMMAND_STORAGE, PATTERN_STORAGE, parse_storage_records)


def parse_network_records(records: list[tuple[re.Match, int]], timestamp):
    data = defaultdict(Counter)
    db_records = []

    for match, value in records:
        vm, traffic_type = match.groups()

        if vm in VIRTUAL_MACHINES:
            data[vm][traffic_type] += value

    for vm, vm_data in data.items():
        record = NetworkStatRecord(ip=VIRTUAL_MACHINES[vm], network=Network.ETHERNET, device='Hyper-V', timestamp=timestamp)
        db_records.append(record)

        for key, db_field in NETWORK_MAP.items():
            setattr(record, db_field.name, vm_data[key])

    return db_records


def parse_storage_records(records: list[tuple[re.Match, int]], timestamp):
    data = defaultdict(lambda: defaultdict(Counter))
    db_records = []

    for match, value in records:
        vm, data_label, op_type = match.groups()
        storage_type = Storage.DATA if data_label else Storage.SYSTEM

        if vm in VIRTUAL_MACHINES:
            # data['BspOne']['System']['Read Bytes'] = 123
            data[vm][storage_type][op_type] += value

    for vm, vm_data in data.items():
        for storage_type, op_data in vm_data.items():
            record = StorageStatRecord(device=vm, storage_type=storage_type, timestamp=timestamp)
            db_records.append(record)

            for key, db_field in STORAGE_MAP.items():
                setattr(record, db_field.name, op_data[key])

    return db_records


def get_stats(command: list, pattern: re.Pattern, parse_func: Callable) -> list[Base]:
    timestamp = datetime.now()

    r = subprocess.run(command, capture_output=True, encoding=locale.getencoding())

    if r.returncode != 0:
        logging.error(f'# Error when call perf command: stderr={r.stderr}; stdout={r.stdout}')
        return []

    lines = r.stdout.strip().splitlines()
    headers = lines[0].split(',')[1:]
    # 具有首尾引号之字符串 to int: "123.456" -> 123
    values = [round(float(v[1:-1])) for v in lines[1].split(',')[1:]]

    data_records = []

    for item, value in zip(headers, values):
        if m := pattern.search(item):
            data_records.append((m, value))

    db_records = parse_func(data_records, timestamp)
    return db_records


def main():
    get_network_stats()
    get_storage_stats()


if __name__ == '__main__':
    main()
