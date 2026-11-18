# AES-256-GCM encryption demonstration

## Purpose and security boundary

The repository includes a standalone classroom utility at scripts/encryption_demo.py to demonstrate authenticated file encryption and decryption. It is intentionally separate from the browser dashboard.

The utility demonstrates:

- AES-256-GCM authenticated encryption.
- A fresh random 16-byte salt and 12-byte nonce for each encryption.
- A 256-bit key derived from a passphrase with scrypt.
- Authentication of the versioned file header as additional authenticated data.
- Authentication failure when the passphrase is wrong or encrypted bytes are modified.
- Passphrases entered through a hidden terminal prompt, not command-line arguments.

**This does not mean the dashboard itself encrypts files at rest or in transit.** It does not configure GitHub Pages encryption, TLS, server-side storage encryption, enterprise key management, or encrypted backups. Those remain deployment controls. The local dashboard continues to serve read-only data on loopback.

## Run the demonstration

Install project dependencies first using the normal project setup, which now includes the cryptography package.

Windows PowerShell:

    python .\scripts\encryption_demo.py encrypt .\data\processed\reviewed\trusted_data.csv .\trusted_data.csv.enc
    python .\scripts\encryption_demo.py decrypt .\trusted_data.csv.enc .\trusted_data.restored.csv

macOS/Linux:

    python3 scripts/encryption_demo.py encrypt data/processed/reviewed/trusted_data.csv trusted_data.csv.enc
    python3 scripts/encryption_demo.py decrypt trusted_data.csv.enc trusted_data.restored.csv

Enter the same strong passphrase twice when encrypting and once when decrypting. The output file is not overwritten unless --force is supplied. Compare the restored file with the original using a SHA-256 tool or the project's integrity workflow. Keep the passphrase separately; it cannot be recovered from the encrypted file.

To demonstrate authenticated integrity, make a copy of the encrypted file, alter one byte, and attempt decryption. The tool must reject the modified file and must not write a plaintext output. A wrong passphrase must produce the same authentication failure.

## File format and implementation notes

The binary container contains a fixed version marker, random salt, random nonce, and AES-GCM ciphertext with its authentication tag. The marker, salt, and nonce are authenticated as additional authenticated data. The scrypt parameters are fixed in the script for reproducibility and should be reviewed before any production use.

The implementation writes encrypted/decrypted output to a separate path and applies owner-only permissions on POSIX systems where supported. It is an educational local utility, not a reviewed production encryption product. Do not reuse a nonce with the same key; the implementation generates a new random salt and nonce for each encryption.

## What to say during the presentation

“SHA-256 hashing and AES-GCM encryption solve different problems. The dashboard's SHA-256 check detects byte changes relative to a trusted reference. This separate utility encrypts file contents and authenticates them so modified ciphertext is rejected. The encryption utility is not integrated into the dashboard's storage or transport path.”
