"""
    This file contains tests for the class 'Blockchain' contained within the 'Blockchain' Module
"""
from blockchain import Blockchain, Block


def create_blockchain():
    genisusBlock = Block()

    blockchain = Blockchain(target='0')
    blockchain.add_block(genisusBlock)

    for x in range(0, 5):
        block = blockchain.mine_block("nothing")
        blockchain.add_block(block)

    return blockchain


def test_blockchain_integrity_valid():
    blockchain = create_blockchain()
    assert(blockchain.check_integrity())


def test_blockchain_integrity_invalid():
    blockchain = create_blockchain()
    blockchain.chain[1].nonce = 99

    assert(not blockchain.check_integrity())


def test_blockchain_proof_of_work():
    blockchain = create_blockchain()

    data = ["Test String", "Test Data"]
    minedBlock = blockchain.mine_block(data)

    assert(minedBlock.generate_hash().startswith(blockchain.target))


def test_block_in_chain():
    blockchain = create_blockchain()
    secondBlock = blockchain.chain[2]
    assert(blockchain.is_block_in_chain(secondBlock))


def test_block_belongs_to_chain():
    blockchain = create_blockchain()
    block = blockchain.mine_block("nothing")
    assert(blockchain.block_belongs(block))


def test_blockchain_is_equal():
    blockchain = create_blockchain()
    blockchain2 = create_blockchain()
    assert(blockchain.is_equal(blockchain2))


def test_blockchain_is_not_equal():
    blockchain = create_blockchain()
    blockchain2 = create_blockchain()
    blockchain2.chain[2].nonce = 99
    assert(not blockchain.is_equal(blockchain2))


def test_prev_hash_in_chain():
    blockchain = create_blockchain()
    blockchain2 = create_blockchain()
    forked_block = blockchain2.mine_block("something")
    blockchain.add_block(blockchain.mine_block("nothing"))
    assert(blockchain.is_prev_hash_in_chain(forked_block))


def test_blockchain_copy_3_blocks():
    blockchain = create_blockchain()
    blockchain2 = blockchain.copy(3)
    assert (blockchain.chain[:3 + 1] == blockchain2.chain)


def test_blockchain_copy():
    blockchain = create_blockchain()
    blockchain2 = blockchain.copy()
    assert (len(blockchain.chain) == len(blockchain2.chain))
