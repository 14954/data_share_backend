import base64
import json
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return public_pem, private_pem


def encrypt_signed_url_for_consumer(signed_url: str, consumer_public_key_pem: str) -> str:
    if not signed_url:
        raise ValueError("signed_url required")
    if not consumer_public_key_pem:
        raise ValueError("consumer_public_key required")

    public_key = serialization.load_pem_public_key(
        consumer_public_key_pem.encode("utf-8"),
        backend=default_backend(),
    )
    aes_key = AESGCM.generate_key(bit_length=256)
    iv = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(iv, signed_url.encode("utf-8"), None)
    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return json.dumps(
        {
            "version": 1,
            "alg": "RSA-OAEP-256+A256GCM",
            "encryptedKey": base64.b64encode(encrypted_key).decode("ascii"),
            "iv": base64.b64encode(iv).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        },
        separators=(",", ":"),
    )


def decrypt_signed_url_for_consumer(encrypted_signed_url: str, private_key_pem: str) -> str:
    if not encrypted_signed_url:
        raise ValueError("encrypted_signed_url required")
    if not private_key_pem:
        raise ValueError("private_key required")

    try:
        payload = json.loads(encrypted_signed_url)
    except ValueError:
        return encrypted_signed_url

    if payload.get("alg") != "RSA-OAEP-256+A256GCM":
        return encrypted_signed_url

    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=None,
        backend=default_backend(),
    )
    aes_key = private_key.decrypt(
        base64.b64decode(payload["encryptedKey"]),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    plaintext = AESGCM(aes_key).decrypt(
        base64.b64decode(payload["iv"]),
        base64.b64decode(payload["ciphertext"]),
        None,
    )
    return plaintext.decode("utf-8")
