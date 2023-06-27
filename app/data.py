from enum import Enum

from sqlalchemy import Column, types

from util.orm import Base


class Network(Enum):
    # wl0 for 5G, wl1 for 2.4G, empty for Ethernet
    WIFI_G_2_4 = '2.4G'
    WIFI_G_5 = '5G'
    ETHERNET = 'Ethernet'
    UNKNOWN = 'Unknown'

    @classmethod
    def parse(cls, if_name):
        if if_name == '':
            return Network.ETHERNET

        elif if_name == 'wl0':
            return Network.WIFI_G_5

        elif if_name == 'wl1':
            return Network.WIFI_G_2_4

        return Network.UNKNOWN


class StatRecord(Base):
    __tablename__ = 'router_stat'

    id = Column(types.Integer, primary_key=True)
    ip = Column(types.String(15), index=True)
    mac = Column(types.CHAR(17))
    network = Column(types.Enum(Network, values_callable=lambda enum: [x.value for x in enum]))
    device = Column(types.String(255))
    rx_rate = Column(types.Integer)
    tx_rate = Column(types.Integer)
    timestamp = Column(types.DateTime, index=True)
