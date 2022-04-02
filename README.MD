# Bevali: Behaviour Validation Using Smart Contracts

This project aims to show the efficacy of using smart contracts for behaviour validation. Each component of the project is broken down into modules. 

* `bevali` module ties all the modules together to produce the instantiation for a runnable agent. 
* `blockchain` module contains all the class for creating a blockchain object and block objects. 
* `datahandler` module handles passing data from the networking module to the bevali module
* `encryption` module neatly wraps an cryptography library for ease of use
* `evaluation` contains the scripts to run throughput experiments
* `multithreading` module contains a class to manage threads to start and stop them during execution, as well as protected datastructures.
* `networking` module contains a class to perform P2P comms
* `tests` contains all the functional tests for the project
* `transactions` contains the class for transactions used by the bevali and handle the smart contract implementation

The source directory is such:
```
📦project
 ┣📦bevali
 ┃  ┣ 📜bevali.py
 ┃  ┗ 📜__init__.py
 ┣📦blockchain
 ┃  ┣ 📜block.py
 ┃  ┣ 📜blockchain.py
 ┃  ┗ 📜__init__.py
 ┣📦datahandler
 ┃  ┣ 📜data_handler.py
 ┃  ┣ 📜data_requests_messages.py
 ┃  ┣ 📜data_sink.py
 ┃  ┗ 📜__init__.py
 ┣📦encryption
 ┃  ┣ 📜encryption.py
 ┃  ┗ 📜__init__.py
 ┣📦evaluation
 ┃  ┣ 📜contract.py
 ┃  ┣ 📜graph_throughput.py
 ┃  ┗ 📜test_throughput.py
 ┣📦multithreading
 ┃  ┣ 📜managed_thread.py
 ┃  ┣ 📜protected_list.py
 ┃  ┣ 📜thread_manager.py
 ┃  ┗ 📜__init__.py
 ┣📦networking
 ┃  ┣ 📜config.py
 ┃  ┣ 📜messages.py
 ┃  ┣ 📜peer_router.py
 ┃  ┗ 📜__init__.py
 ┣📦tests
 ┃  ┣ 📜contract.py
 ┃  ┣ 📜contract_1.py
 ┃  ┣ 📜contract_2.py
 ┃  ┣ 📜sum_contract.py
 ┃  ┣ 📜test_attackers.py
 ┃  ┣ 📜test_bevali.py
 ┃  ┣ 📜test_block.py
 ┃  ┣ 📜test_blockchain.py
 ┃  ┣ 📜test_contracts.py
 ┃  ┣ 📜test_datahandler.py
 ┃  ┣ 📜test_encryption.py
 ┃  ┣ 📜test_networking.py
 ┃  ┣ 📜test_transactions.py
 ┃  ┗ 📜__init__.py
 ┣📦transactions
 ┃  ┣ 📜transaction.py
 ┃  ┗ 📜__init__.py
 ┣ 📜.gitignore
 ┣ 📜bitbucket-pipelines.yml
 ┣ 📜conftest.py
 ┣ 📜Makefile
 ┣ 📜readme.md
 ┣ 📜requirements.txt
 ┗ 📜timelog.md
```

## Build instructions

### Requirements


* Python 3.10
* Make
* Packages: listed in `requirements.txt` 
* Tested on Windows 10, Linux Mint 18, MacOS Big Sir



### Build steps

* Building the software is done via the make file.
* If you have trouble with the installation, it's due to this make file.
* It attempts to install on windows and unix based system but it is only tested properly on the OSs described above.
* Run these commands:

```
    $: make install
```

### Test steps

To run automated testing run this command
```
    $: make test
```

### Evaluation Steps

To produce throughput analysis results, run this command. <br />
`note:` There is a known bug on windows that causes the evaluation to sometimes stop. The solution is to restart the evaluation, changing the parmeters that were missed.
```
    $: make evaluate
```

### Clean Step

To clean the repo, run this command
```
    $: make clean
```
