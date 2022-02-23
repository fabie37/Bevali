import transactions as tx
import encryption as crypt


def test_generate_signed_hash_of_transaction():
    sK = crypt.generate_private_key()
    pK = crypt.get_public_key(sK)
    serialPK = crypt.serialize_public_key(pK)
    serialPK = str(serialPK, encoding="UTF-8")
    transaction = tx.Transaction(serialPK, "1234", serialPK)
    prior_hash = transaction.hash
    tx.signHash(transaction, sK)
    assert(prior_hash != transaction.hash)


def test_verify_hash_of_transaction():
    sK = crypt.generate_private_key()
    pK = crypt.get_public_key(sK)
    serialPK = crypt.serialize_public_key(pK)
    serialPK = str(serialPK, encoding="UTF-8")
    transaction = tx.Transaction(serialPK, "1234", serialPK)
    tx.signHash(transaction, sK)
    assert(tx.verifyHash(transaction))


def test_verify_hash_of_tampered_transaction():
    sK = crypt.generate_private_key()
    pK = crypt.get_public_key(sK)
    serialPK = crypt.serialize_public_key(pK)
    serialPK = str(serialPK, encoding="UTF-8")
    transaction = tx.Transaction(serialPK, "1234", serialPK)
    tx.signHash(transaction, sK)
    transaction.data = [1, 2]
    assert(not tx.verifyHash(transaction))
