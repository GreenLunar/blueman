from blueman.Service import Service
from blueman.Sdp import SERIAL_PORT_SVCLASS_ID


class SerialPort(Service):
    __group__ = 'serial'
    __svclass_id__ = SERIAL_PORT_SVCLASS_ID
    __icon__ = "blueman-serial"
    __priority__ = 50
