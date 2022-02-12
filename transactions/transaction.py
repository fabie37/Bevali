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

    def exec(self, blockchain=None):
        """
            If a transaction needs to be verified
            during minning, the exec function will
            handle the transaction behaviour
        """
        return self

    def jsonize(self):
        """
            Used for when creating a hash of the block with
            a transcation in it
        """
        return {
            "creator": self.creator,
            "data": self.data,
            "timestamp": self.timestamp
        }


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
        self.state = state

    def exec(self, blockchain=None):
        return self

    def jsonize(self):
        """
            Used for when creating a hash of the block with
            a transcation in it
        """
        transaction = super().jsonize()
        contract = {
            "contract_id": self.contract_id,
            "code": self.code,
            "memory": self.memory,
            "state": self.state
        }
        transaction.update(contract)
        return transaction


class ContractUpdateTranscation(Transaction):
    """
        This transaction will typically only be returned by contracts
        themselves or by oracles. 
    """

    def __init__(self, creator, contract_id, state, data=None):
        super().__init__(creator, data)
        self.contract_id = contract_id
        self.state = state

    def exec(self, blockchain):
        return self

    def validate(self, blockchain, surrounding_transactions):
        pass

    def jsonize(self):
        """
            Used for when creating a hash of the block with
            a transcation in it
        """
        transaction = super().jsonize()
        update = {
            "contract_id": self.contract_id,
            "state": self.state
        }
        transaction.update(update)
        return transaction


class ContractInvokeTransaction(Transaction):
    """
        This will invoke or stimulate a contract be ran on peers.

    """

    def __init__(self, creator, contract_id, data=None):
        super().__init__(creator, data)
        self.contract_id = contract_id

    def exec(self, blockchain):
        try:
            # This will run the code found given contract id

            # 1. Find the contract in the blockchain
            contract = findContract(blockchain, self.contract_id)
            if not contract:
                return None

            # 2. Find contracts latest state
            state_keys = contract.state.keys()
            current_state = findState(blockchain, self.contract_id, state_keys)

            # 3. Run the code!

            # object that contains all the accessible blockchain related methods
            lib = {
                "Transaction": Transaction,
                "ContractCreateTransaction": ContractCreateTransaction,
                "ContractInvokeTransaction": ContractInvokeTransaction,
                "ContractUpdateTranscation": ContractUpdateTranscation
            }

            # Locals: This contains variables that are assigned in the code
            locals = {}

            # This is data we pass into exec
            globals = {
                "blockchain": blockchain,
                "state": current_state,
                "memory": contract.memory,
                "contract_id": contract.contract_id,
                "creator": contract.creator,
                "invoker": self.creator,
                "lib": lib,
                "timestamp": self.timestamp

            }
            code = contract.code
            try:

                # Executate the code
                exec(code, globals, locals)

                # Extract any transactions from the returned transactions
                computedTransactions = locals["transactions"]
                validTransactions = []

                # Ensure to check returned transactions are actually transactions
                validTransactions.append(self)
                for transaction in computedTransactions:
                    if issubclass(type(transaction), Transaction) or isinstance(transaction, Transaction):
                        validTransactions.append(transaction)

                return validTransactions
            except Exception as exc:
                print(exc)
                return self
        except (Exception):
            return None

    def jsonize(self):
        transaction = super().jsonize()
        invoke = {
            "contract_id": self.contract_id,
        }
        transaction.update(invoke)
        return transaction


"""
    This holds all the operations a transaction
    can do with a blockchain.

    Typically resorted for all use in the exec 
    method or validation of transactions
"""


def findContract(blockchain, contract_id):
    if blockchain:
        for block in blockchain.chain:
            for transaction in block.data:
                if isinstance(transaction, ContractCreateTransaction) and transaction.contract_id == contract_id:
                    return transaction
    return None


def findState(blockchain, contract_id, state_keys):
    state = {}
    if blockchain and contract_id and state_keys:
        for block in reversed(blockchain.chain):
            for transaction in block.data:
                # Is transaction in chain is apart of the chain, get the state
                if (isinstance(transaction, ContractUpdateTranscation) or isinstance(transaction, ContractCreateTransaction)) and transaction.contract_id == contract_id:
                    for key in state_keys:
                        if key in transaction.state:
                            state[key] = transaction.state[key]
                    state_keys = list(set(state_keys) - set(state.keys()))

                # If no new state to be found, return state
                if not state_keys:
                    return state
    return None
