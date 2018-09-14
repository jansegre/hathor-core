import hashlib
import base58
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def get_public_key_bytes(public_key, encoding=serialization.Encoding.DER,
                         format=serialization.PublicFormat.SubjectPublicKeyInfo):
    """Returns the bytes from a cryptography ec.EllipticCurvePublicKey

    TODO: secp256k1 public keys generated with cryptography are
    not 32/33 bytes long as expected. We'd have to manually convert
    the public numbers to get it
    """
    return public_key.public_bytes(
        encoding,
        format
    )


def get_private_key_bytes(private_key,
                          encoding=serialization.Encoding.DER,
                          format=serialization.PrivateFormat.PKCS8,
                          encryption_algorithm=serialization.NoEncryption()):
    return private_key.private_bytes(
        encoding=encoding,
        format=format,
        encryption_algorithm=encryption_algorithm
    )


def get_public_key_from_bytes(public_key_bytes, backend=default_backend()):
    """Returns the cryptography ec.EllipticCurvePublicKey from bytes"""
    return serialization.load_der_public_key(public_key_bytes, backend)


def get_private_key_from_bytes(private_key_bytes, password=None, backend=default_backend()):
    """Returns the cryptography ec.EllipticCurvePrivateKey from bytes"""
    return serialization.load_der_private_key(private_key_bytes, password, backend)


def sign_data(private_key, data_to_sign, sig_algorithm=ec.ECDSA(hashes.SHA256())):
    """Signs the provided data with the public key

    private_key: cryptography ec.EllipticCurvePrivateKey
    data_to_sign: bytes
    """
    return private_key.sign(data_to_sign, sig_algorithm)


def get_hash160(public_key_bytes):
    """The input is hashed twice: first with SHA-256 and then with RIPEMD-160

    :type: bytes

    :rtype: bytes
    """
    key_hash = hashlib.sha256(public_key_bytes)
    h = hashlib.new('ripemd160')
    h.update(key_hash.digest())
    return h.digest()


def get_address_from_public_key_bytes(public_key_bytes):
    """For now, we only do sha256 followed by ripmd160.

    :param public_key_bytes: public key in bytes
    :type public_key_bytes: bytes


    :return: address associated to public key
    :rtype: bytes
    """
    return get_hash160(public_key_bytes)


def get_address_from_public_key(public_key):
    """Wrapper function to pass a cryptography ec.EllipticCurvePrivateKey object
    to the function above
    """
    public_key_bytes = get_public_key_bytes(public_key)
    return get_address_from_public_key_bytes(public_key_bytes)


def get_address_b58_from_public_key(public_key):
    """Gets the b58 address from a public key.

    :param: ec.EllipticCurvePublicKey
    :return: the b58-encoded address
    :rtype: string
    """
    return base58.b58encode(get_address_from_public_key(public_key)).decode('utf-8')


def get_address_b58_from_public_key_bytes(public_key):
    return base58.b58encode(get_address_from_public_key_bytes(public_key)).decode('utf-8')


def get_address_b58_from_bytes(address):
    return base58.b58encode(address).decode('utf-8')


def generate_privkey_crt_pem():
    """ Generates a new certificate with a new private key. This certificate is
    used only for TLS connection, and won't be used to identify the peer.

    Adapted from:
    https://github.com/twisted/twisted/blob/trunk/src/twisted/test/server.pem

    :return: Private key and certificate in PEM format
    :rtype: string
    """
    from datetime import datetime

    from OpenSSL.crypto import FILETYPE_PEM, TYPE_RSA, X509, PKey, dump_privatekey, dump_certificate

    key = PKey()
    key.generate_key(TYPE_RSA, 2048)

    cert = X509()

    # It is optional to have a subject and an issue in a certificate.
    # It works with and without these fields.
    # issuer = cert.get_issuer()
    # subject = cert.get_subject()
    # for dn in [issuer, subject]:
    #     dn.C = b'XX'   # Country
    #     dn.ST = b'XX'  # State or Province
    #     dn.L = b'XX'   # Locality
    #     dn.CN = b'testnet.hathor.network'  # Common Name
    #     dn.O = b'Hathor Network'  # noqa: E741 ambiguous variable name 'O'
    #     dn.OU = b'testnet'   # Organization Unit
    #     dn.emailAddress = b'noreply@testnet.hathor.network'

    # Set the period in which the certificate is valid. In this case, the
    # reference time is now, and it will be valid between 10 minutes ago
    # and 100 years from now. This 10 minutes tolerance is to accomodate
    # differences in the time between peers.
    # To check the valid period, run a server with ssl and then run:
    # `openssl s_client -showcerts -connect localhost:8000 | openssl x509 -noout -dates`
    cert.set_serial_number(datetime.now().toordinal())
    cert.gmtime_adj_notBefore(-60 * 10)
    cert.gmtime_adj_notAfter(60 * 60 * 24 * 365 * 100)

    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    return dump_privatekey(FILETYPE_PEM, key) + dump_certificate(FILETYPE_PEM, cert)
