from blueman.Service import Service
from blueman.Sdp import NAP_SVCLASS_ID
from blueman.bluez.Network import Network


class NetworkAccessPoint(Service):
    __group__ = 'network'
    __svclass_id__ = NAP_SVCLASS_ID
    __icon__ = "network-wireless"
    __priority__ = 81
    __interface__ = Network
