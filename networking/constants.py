""" Networking constants """
from enum import Enum
HEADERSIZE = 20


""" Networking enumations """


class ServerStatus(Enum):
    INIT = 1
    RUNNING = 2
    STOPPED = 3
    ERROR = 4
