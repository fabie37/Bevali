
from blockchain import Blockchain, Block
from datahandler import DataRequestMessages


class DataSink():
    """ 
    This is a wrapper class for data sinks. 
    These could be lists, queues or anything.

    Simply because different data structures 
    will have different append, add or put methods.

    It also makes it abstract the datatype 
    implementation from the data handler class.

    """

    def __init__(self, dataType, dataSink):
        self.dataSink = dataSink
        self.dataType = dataType

    def append(self, data):
        self.dataSink.append(data)


class BlockSink(DataSink):
    def __init__(self, dataSink):
        super().__init__(Block, dataSink)

    def append(self, data):
        self.dataSink.put(data)


class BlockChainSink(DataSink):
    def __init__(self, dataSink):
        super().__init__(Blockchain, dataSink)

    def append(self, data):
        self.dataSink.put(data)


class PoolSink(DataSink):
    def __init__(self, dataSink):
        super().__init__(object, dataSink)

    def append(self, data):
        self.dataSink.append(data)


class RequestsSink(DataSink):
    def __init__(self, dataSink):
        super().__init__(DataRequestMessages, dataSink)

    def append(self, data):
        self.dataSink.put(data)
