"""
    This defines the class for all transactions
    that can be send over the blockchain.

    This will also include contract creation,
    invocation and updating.
"""
from time import time
import encryption as crypt
import hashlib
import json
import pickle


class Transaction():
    """
        Transcation is a parent class, and every object
        on the blockchain is a transaction to some degree
    """

    def __init__(self, creator, data=None, public_key=None):
        self.creator = creator
        self.data = data
        self.timestamp = time()
        self.hash = ""
        self.public_key = public_key

    def exec(self, blockchain=None):
        """
            If a transaction needs to be verified
            during minning, the exec function will
            handle the transaction behaviour
        """
        return self

    def validate(self, blockchain, block):
        """
            Used for when peers need to validate
            a transaction when a new block comes
            in.
        """
        # If condition to not break testing
        if self.public_key:
            return verifyHash(self)
        return True

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

    def __init__(self, creator, contract_id, code, memory, state, data=None, public_key=None):
        super().__init__(creator, data, public_key)
        self.contract_id = contract_id
        self.code = code
        self.memory = memory
        self.state = state
        self.hash = ""

    def exec(self, blockchain=None):
        return self

    def validate(self, blockchain, block):
        """
            There shouldn't be any need to
            validate a contract, other
            than to parse it to see
            if the code is correct.
            Beyond the scope.
        """
        if self.public_key:
            return verifyHash(self)
        return True

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

    def __init__(self, creator, contract_id, state, data=None, public_key=None):
        super().__init__(creator, data, public_key)
        self.contract_id = contract_id
        self.state = state
        self.hash = ""

    def exec(self, blockchain):
        return self

    def validate(self, blockchain, block):
        """
            Updates to state should only happen when an invocation
            made the update.
            Find the invocation, run it and make sure it's returns
            this.

            Error with circular dependances for the time being, we'll leave this.
        """
        return True

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

    def __init__(self, creator, contract_id, data=None, public_key=None):
        super().__init__(creator, data, public_key)
        self.contract_id = contract_id
        self.hash = ""

    def exec(self, blockchain, blockNumber=None):
        try:
            # This will run the code found given contract id

            # 1. Find the contract in the blockchain
            contract = findContract(blockchain, self.contract_id)
            if not contract:
                return None

            # 2. Find contracts latest state
            state_keys = contract.state.keys()
            current_state = findState(
                blockchain, self.contract_id, state_keys, blockNumber)

            # 3. Run the code!

            # object that contains all the accessible blockchain related methods
            lib = {
                "Transaction": Transaction,
                "ContractCreateTransaction": ContractCreateTransaction,
                "ContractInvokeTransaction": ContractInvokeTransaction,
                "ContractUpdateTransaction": ContractUpdateTranscation
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
                "timestamp": self.timestamp,
                "data": self.data

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
        except Exception as exc:
            print(exc)
            return None

    def validate(self, blockchain, block):
        """
            Basically re-run the code to see if you get the same result.

            UPDATE TO FUTURE SELF:
                Make sure to double check this
                Nothing here to stop someone from just
                adding a transaction that didn't come
                from a contract.
        """
        try:
            # First check that the hash is correct
            if self.public_key:
                if not verifyHash(self):
                    return False

            blocknumber = block.blockNumber
            computedTransactions = self.exec(blockchain, blocknumber)
            jsonTransactions = [tx.jsonize() for tx in computedTransactions]

            # Wipe timestamps
            for tx in jsonTransactions:
                tx["timestamp"] = None

            blockdata = []
            for tx in block.data:
                cpy = dict(tx.jsonize())
                cpy["timestamp"] = None
                blockdata.append(cpy)

            # Check that our computed results are in block
            for computedTx in jsonTransactions:
                if computedTx not in blockdata:
                    return False
            return True

        except Exception:
            return False

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


def verifyHash(transaction):
    if isinstance(transaction, Transaction):
        if transaction.creator != transaction.public_key:
            return False

        hash = hashlib.sha256(json.dumps(
            transaction.jsonize()).encode("UTF-8")).hexdigest()

        public_key = crypt.deserialize_public_key(
            bytes(transaction.public_key, encoding="UTF-8"))

        return crypt.verify(transaction.hash, hash.encode("UTF-8"), public_key)
    return False


def signHash(transaction, private_key):
    """
        Signs the hash of the transaction
    """
    if isinstance(transaction, Transaction):
        hash = hashlib.sha256(json.dumps(
            transaction.jsonize()).encode("UTF-8")).hexdigest()

        signedHash = crypt.sign(hash.encode("UTF-8"), private_key)
        transaction.hash = signedHash


def findContract(blockchain, contract_id):
    if blockchain:
        for block in blockchain.chain:
            for transaction in block.data:
                if isinstance(transaction, ContractCreateTransaction) and transaction.contract_id == contract_id:
                    return transaction
    return None


def findState(blockchain, contract_id, state_keys, blocknumber=None):
    state = {}

    if blocknumber:
        chain = blockchain.chain[:blocknumber]
    else:
        chain = blockchain.chain

    if blockchain and contract_id and state_keys:
        for block in reversed(chain):
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
