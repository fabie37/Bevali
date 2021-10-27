"""
    This file contains tests for the class 'Blockchain' contained within the 'Blockchain' Module
"""
from blockchain import Blockchain
from blockchain import Block


def test_blockchain_integrity_valid():
    genisusBlock = Block()
    firstBlock = Block(1, genisusBlock.generate_hash())
    secondBlock = Block(2, firstBlock.generate_hash())
    thirdBlock = Block(3, secondBlock.generate_hash())

    blockchain = Blockchain()
    blockchain.add_block(genisusBlock)
    blockchain.add_block(firstBlock)
    blockchain.add_block(secondBlock)
    blockchain.add_block(thirdBlock)

    assert(blockchain.check_integrity())


def test_blockchain_integrity_invalid():
    genisusBlock = Block()
    firstBlock = Block(1, genisusBlock.generate_hash())
    secondBlock = Block(2, firstBlock.generate_hash())
    thirdBlock = Block(3, secondBlock.generate_hash())

    blockchain = Blockchain()
    blockchain.add_block(genisusBlock)
    blockchain.add_block(firstBlock)
    blockchain.add_block(secondBlock)
    blockchain.add_block(thirdBlock)

    blockchain.chain[1].nonce = 99

    assert(not blockchain.check_integrity())


def test_blockchain_proof_of_work():
    genisusBlock = Block()
    firstBlock = Block(1, genisusBlock.generate_hash())
    secondBlock = Block(2, firstBlock.generate_hash())
    thirdBlock = Block(3, secondBlock.generate_hash())

    blockchain = Blockchain()
    blockchain.add_block(genisusBlock)
    blockchain.add_block(firstBlock)
    blockchain.add_block(secondBlock)
    blockchain.add_block(thirdBlock)

    data = ["Test String", "Test Data"]
    minedBlock = blockchain.mine_block(data)

    assert(minedBlock.generate_hash().startswith(blockchain.target))
