from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization


def generate_private_key():
    """
        Generates a private key
    """
    return rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())


def get_public_key(private_key):
    """
        returns public key from private key
    """
    return private_key.public_key()


def encrypt(message_bytes, public_key):
    """
        Given a message and a private key, return bytes
    """
    return public_key.encrypt(
        message_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


def decrypt(encrypted_message, private_key):
    """
        Given a message, decrypt message
    """
    return private_key.decrypt(
        encrypted_message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


def sign(message_bytes, private_key):
    """
        Given a message, sign it using the private key
    """
    return private_key.sign(message_bytes, padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
        hashes.SHA256()
    )


def verify(signature, message_bytes, public_key):
    """
        Given a signed message digest and a message, verify it
    """
    valid = True
    try:
        public_key.verify(
            signature,
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    except Exception as e:
        valid = False
    return valid


def serialize_public_key(public_key):
    """
        Returns the public key in a serialize string format
    """
    return public_key.public_bytes(encoding=serialization.Encoding.PEM,
                                   format=serialization.PublicFormat.SubjectPublicKeyInfo
                                   )


def deserialize_public_key(key_encoding):
    """
        Returns a public key object from an serialized key
    """
    public_key = serialization.load_pem_public_key(
        key_encoding,
    )
    return public_key


def deserialize_private_key(key_encoding):
    """
        Returns a public key object from an serialized key
    """
    private_key = serialization.load_pem_private_key(
        key_encoding,
        password=None,
    )
    return private_key


def serialize_private_key(private_key):
    """
        Returns the private key in a serialize string format
    """
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
