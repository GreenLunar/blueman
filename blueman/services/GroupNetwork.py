from blueman.Service import Service
from blueman.Sdp import GN_SVCLASS_ID
from blueman.bluez.Network import Network


class GroupNetwork(Service):
    __group__ = 'network'
    __svclass_id__ = GN_SVCLASS_ID
    __icon__ = "network-wireless"
    __priority__ = 80
    __interface__ = Network
