# Manual

* Typical setup is done by the make file
```
    $: make install
```

## Creating an agent
* Creating an agent is done by `bevali` module.
* Here is some example code for creating an agent
* This will create an agent called alice with:
    * IP: 127.0.0.1
    * Port: 2000
```
from bevali import Bevali

 alice = Bevali(127.0.0.1, 2000)
 alice.createNewChain()
 alice.start()
```

## Connecting two agents
* This code shows you an example of connecting to another agent
* This will send the apprioate messages and connect two agents
* The process does take a second
* Bob will receive alice's blockchain upon connection.
* Bob is also a minner so any new transactions sent his way and he will begin to mine them.
```
bob = Bevali(127.0.0.1, 2001)
bob.start()
bob.start_minning()

alice.connect(bob.ip, bob.port)
```

## Submitting a smart contract
* To log behaviour, a smart contract has to be made.
* An example of a contract may look like this

`contract.py`
```
transactions = []


def createSumLog(invoker, data, contract_id):
    return lib["Transaction"](contract_id, {
        "logger": invoker,
        "result": data["var_1"] + data["var_2"],
        "contract_id": contract_id,
        "timestamp": timestamp
    })


tx = createSumLog(invoker, data, contract_id)

transactions.append(tx)
```

* This contract simply logs the addition of two variables send to it over the blockchain.
* To submit it to the chain, we need to use ContractCreationTransaction from the `transactions` module.
* Here we sign the transaction too by adding Alices public key as the owner of the transaction, and send it public key in a seperate field

```
from transactions import ContractInvokeTransaction, ContractCreateTransaction, Transaction
import os

def import_code(filename):
    code = ""
    cwd = os.getcwd()
    with open(cwd + filename, "r") as f:
        code = ''.join(f.readlines())
    return code

contract_code = import_code('contract.py')

SumContract = ContractCreateTransaction("Alice", "contract_id_3", contract_code, None, None, None, None)
alice.sendTransaction(SumContract)

```

## Invoking a smart contract
* Now to actually get our blockchain to add two numbers we need to invoke the contract.
* Here we will get alice to add 1 and 2
* We specify who is sending the contract

```
add12 = ContractInvokeTransaction("Alice", "contract_id_3", data={
    "var_1": 1,
    "var_2": 2
})

alice.sendTransaction(add12)
```

* Bob will then mine the transactions, placing them into a new block
* Alice will then receive this new block, validate it and add it to her blockchain
* Now both alice and bob will have the invocation and the result on their blockchains


## Signing Transactions

* If you want to write a smart contract that verifies the user sending it, you can use the public key cryptography.
* Instead of having the owner and public key attributes on the transactions being just a string and none, you can use 
```
alice.getSerialPublicKey()
```
* To return an agents serial key
* This can be passed onto transaction at which the network layer will confirm the message digest of the transaction was indeed signed by the agent.
```
pubkey = alice.getSerialPublicKey()

SumContract = ContractCreateTransaction(pubkey, "contract_id_3", contract_code, None, None, None, pubkey)
```

# More Examples

Refer to the tests folder for more indepth examples of how to create various networks and contracts.