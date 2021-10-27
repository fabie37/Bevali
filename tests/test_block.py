"""
    This file contains tests for the class 'Block' contained within the 'Blockchain' Module
"""
from blockchain import Block


def test_genisus_block_hash():
    testBlock = Block()
    genisusBlock = Block(blockNumber=0, previousHash=0,
                         timestamp=testBlock.timestamp)
    testHash = testBlock.generate_hash()
    genisusHash = genisusBlock.generate_hash()
    assert testHash == genisusHash


def test_data_is_added():
    testBlock = Block()
    testBlock.add_data("")
    assert len(testBlock.data) == 1
