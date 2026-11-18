"""Demonstrate authenticated file encryption with AES-256-GCM.

This utility is a standalone classroom demonstration. It does not encrypt the
dashboard's stored data, network traffic, or GitHub Pages content.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import os
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"SC-CLIMATE-ENC\x01"
SALT_BYTES = 16
NONCE_BYTES = 12
KEY_BYTES = 32
TAG_BYTES = 16
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
MIN_PASSPHRASE_LENGTH = 12


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    if len(passphrase) < MIN_PASSPHRASE_LENGTH:
        raise ValueError(
            f"Passphrase must contain at least {MIN_PASSPHRASE_LENGTH} characters."
        )
    return hashlib.scrypt(
        passphrase.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=KEY_BYTES,
    )


def encrypt_bytes(plaintext: bytes, passphrase: str) -> bytes:
    """Return a versioned salt+nonce+ciphertext AES-GCM container."""
    salt = os.urandom(SALT_BYTES)
    nonce = os.urandom(NONCE_BYTES)
    header = MAGIC + salt + nonce
    key = _derive_key(passphrase, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, header)
    return header + ciphertext


def decrypt_bytes(encrypted: bytes, passphrase: str) -> bytes:
    """Authenticate and decrypt a container; never return unauthenticated bytes."""
    header_length = len(MAGIC) + SALT_BYTES + NONCE_BYTES
    if not encrypted.startswith(MAGIC):
        raise ValueError("File is not a supported climate-demo encrypted file.")
    if len(encrypted) < header_length + TAG_BYTES:
        raise ValueError("Encrypted file is truncated or malformed.")

    header = encrypted[:header_length]
    salt_start = len(MAGIC)
    salt = encrypted[salt_start : salt_start + SALT_BYTES]
    nonce = encrypted[salt_start + SALT_BYTES : header_length]
    key = _derive_key(passphrase, salt)
    try:
        return AESGCM(key).decrypt(nonce, encrypted[header_length:], header)
    except InvalidTag as exc:
        raise ValueError(
            "Authentication failed: wrong passphrase or encrypted file was modified."
        ) from exc


def _write_output(path: Path, content: bytes, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {path} (use --force to replace it)")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
        if os.name == "posix":
            temporary.chmod(0o600)
        if path.exists() and not overwrite:
            raise FileExistsError(f"Output already exists: {path}")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _same_file(input_path: Path, output_path: Path) -> bool:
    return input_path.resolve() == output_path.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Encrypt or decrypt a file with AES-256-GCM for the project demo."
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in ("encrypt", "decrypt"):
        command = subparsers.add_parser(operation)
        command.add_argument("input", type=Path, help="input file")
        command.add_argument("output", type=Path, help="new output file")
        command.add_argument(
            "--force", action="store_true", help="allow replacing an existing output"
        )
    args = parser.parse_args()

    if _same_file(args.input, args.output):
        parser.error("Input and output must be different files.")
    if not args.input.is_file():
        parser.error(f"Input file does not exist: {args.input}")

    if args.operation == "encrypt":
        passphrase = getpass.getpass("Encryption passphrase (12+ characters): ")
        confirmation = getpass.getpass("Confirm passphrase: ")
        if passphrase != confirmation:
            parser.error("Passphrases do not match.")
        try:
            encrypted = encrypt_bytes(args.input.read_bytes(), passphrase)
            _write_output(args.output, encrypted, args.force)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        print(f"Encrypted file written: {args.output}")
        print("Algorithm: AES-256-GCM; key derivation: scrypt; authentication: enabled")
        print("Keep the passphrase safe. It cannot be recovered from the encrypted file.")
        return 0

    passphrase = getpass.getpass("Decryption passphrase: ")
    try:
        plaintext = decrypt_bytes(args.input.read_bytes(), passphrase)
        _write_output(args.output, plaintext, args.force)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Authenticated decryption successful: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
