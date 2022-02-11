"""
    This defines the class for all transactions 
    that can be send over the blockchain.

    This will also include contract creation,
    invocation and updating.
"""
from time import time


class Transaction():
    """
        Transcation is a parent class, and every object 
        on the blockchain is a transaction to some degree
    """

    def __init__(self, creator, data=None):
        self.creator = creator
        self.data = data
        self.timestamp = time()


class ContractCreateTransaction(Transaction):
    """
        This will create a contract, these will
        be searched for in the blockchain to run
        contrat code
    """

    def __init__(self, creator, contract_id, code, memory, state, data=None):
        super().__init__(creator, data)
        self.contract_id = contract_id
        self.code = code
        self.memory = memory
        state = state


class ContractInvokeTransaction(Transaction):
    """
        This will invoke or stimulate a contract be ran on peers.

    """

    def __init__(self, creator, contract_id, data=None):
        super().__init__(creator, data)
        self.contract_id = contract_id


class ContractUpdateTranscation(Transaction):
    """
        This transaction will typically only be returned by contracts
        themselves or by oracles. 
    """

    def __init__(self, creator, contract_id, state, data=None):
        super().__init__(creator, data)
        self.contract_id = contract_id
        self.state = state
