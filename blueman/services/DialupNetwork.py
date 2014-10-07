from blueman.Service import Service
from blueman.Sdp import DIALUP_NET_SVCLASS_ID


class DialupNetwork(Service):
    __group__ = 'serial'
    __svclass_id__ = DIALUP_NET_SVCLASS_ID
    __icon__ = "modem"
    __priority__ = 50

    @property
    def connected(self):
        # TODO: Detect connection state
        return False
