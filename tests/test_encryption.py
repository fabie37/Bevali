from encryption import encrypt, decrypt, generate_private_key, get_public_key, sign, verify
from encryption.encryption import deserialize_private_key, deserialize_public_key, serialize_private_key, serialize_public_key


def test_gen_private_key():
    private_key = generate_private_key()
    assert(private_key)


def test_get_public_key():
    private_key = generate_private_key()
    public_key = get_public_key(private_key)
    assert(public_key)


def test_message_encrypted():
    private_key = generate_private_key()
    public_key = get_public_key(private_key)

    msg = "Foo Bar"
    e_msg = encrypt(msg.encode("UTF-8"), public_key)

    assert(msg != e_msg)


def test_message_decrypted():
    private_key = generate_private_key()
    public_key = get_public_key(private_key)
    msg = "Foo Bar"
    e_msg = encrypt(msg.encode("UTF-8"), public_key)
    msg2 = decrypt(e_msg, private_key).decode('UTF-8')

    assert(msg == msg2)


def test_sign_message():
    private_key = generate_private_key()
    msg = "Foo Bar"
    signed = sign(msg.encode('UTF-8'), private_key)
    assert (signed)


def test_verify_message():
    private_key = generate_private_key()
    public_key = get_public_key(private_key)
    msg = "Foo Bar"
    signed = sign(msg.encode('UTF-8'), private_key)
    valid = verify(signed, msg.encode('UTF-8'), public_key)
    assert (valid)


def test_verify_bad_message():
    private_key = generate_private_key()
    public_key = get_public_key(private_key)
    msg = "Foo Bar"
    signed = sign(msg.encode('UTF-8'), private_key)
    valid = verify(signed, "Foo Ba".encode('UTF-8'), public_key)
    assert (not valid)


def test_serialized_deserialize_pub_key():
    private_key = generate_private_key()
    public_key = get_public_key(private_key)
    string_key = serialize_public_key(public_key)
    pub_test_key = deserialize_public_key(string_key)
    assert(pub_test_key.__eq__(public_key))


def test_serialized_deserialize_private_key():
    private_key = generate_private_key()
    string_key = serialize_private_key(private_key)
    private_test_key = deserialize_private_key(string_key)
    assert(private_test_key.__eq__(private_key))
