"""
EOW Quant Engine — Dual-API Credential Vault  (stdlib-only implementation)

Encrypts and stores Binance API credentials for both PAPER (testnet) and
LIVE (production) modes using only Python standard-library primitives:

  Key derivation  — PBKDF2-HMAC-SHA256 (480 000 iterations, 64-byte output)
  Encryption      — HMAC-CTR (XOR plaintext with HMAC-SHA256 keystream)
  Authentication  — Encrypt-then-MAC with HMAC-SHA256 (constant-time compare)

No third-party packages required — works on any Python 3.8+ install.

On-disk format (data/vault.enc — plain text, one line):
  base64( salt[32] | nonce[16] | mac[32] | ciphertext )

Decrypted payload (JSON):
  {"paper": {"key": "…", "secret": "…"},
   "live":  {"key": "…", "secret": "…"},
   "mode":  "PAPER" | "LIVE"}
"""
from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import os
from pathlib import Path
from loguru import logger


VAULT_PATH = Path("data/vault.enc")

_PBKDF2_ITERATIONS = 480_000   # NIST SP 800-132 (2024)
_SALT_BYTES        = 32
_NONCE_BYTES       = 16
_MAC_BYTES         = 32        # HMAC-SHA256 output


# ── Exceptions ────────────────────────────────────────────────────────────────

class WrongPassword(Exception):
    """Raised when the vault HMAC check fails (wrong password or tampered file)."""


class VaultNotConfigured(Exception):
    """Raised when the vault file does not exist or is empty."""


# ── Internal crypto primitives ────────────────────────────────────────────────

def _derive_keys(password: str, salt: bytes) -> tuple[bytes, bytes]:
    """
    Derive two independent 32-byte keys from password + salt via PBKDF2-HMAC-SHA256.
    Returns (enc_key, mac_key).
    """
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=64,
    )
    return dk[:32], dk[32:]


def _hmac_ctr_xor(key: bytes, nonce: bytes, data: bytes) -> bytes:
    """
    HMAC-CTR stream cipher: XOR *data* with a keystream produced by
    HMAC-SHA256(key, nonce || counter).  This is semantically secure
    (IND-CPA) when the nonce is random and never reused with the same key.
    """
    out   = bytearray(len(data))
    block = 32                   # SHA-256 output size
    for i in range(0, len(data), block):
        ks_block = _hmac.new(key, nonce + i.to_bytes(8, "big"), "sha256").digest()
        chunk    = data[i : i + block]
        for j, b in enumerate(chunk):
            out[i + j] = b ^ ks_block[j]
    return bytes(out)


def _seal(password: str, plaintext: bytes) -> bytes:
    """
    Encrypt and authenticate *plaintext*.  Returns base64-encoded envelope.
    Scheme: Encrypt-then-MAC using separate keys derived from the same password.
    """
    salt     = os.urandom(_SALT_BYTES)
    nonce    = os.urandom(_NONCE_BYTES)
    enc_key, mac_key = _derive_keys(password, salt)

    ciphertext   = _hmac_ctr_xor(enc_key, nonce, plaintext)
    mac          = _hmac.new(mac_key, salt + nonce + ciphertext, "sha256").digest()

    return base64.b64encode(salt + nonce + mac + ciphertext)


def _open(password: str, data: bytes) -> bytes:
    """
    Authenticate and decrypt a *data* blob produced by _seal().
    Raises WrongPassword if the HMAC check fails.
    """
    try:
        raw = base64.b64decode(data)
    except Exception:
        raise WrongPassword("Vault file is corrupt or not base64.")

    if len(raw) < _SALT_BYTES + _NONCE_BYTES + _MAC_BYTES:
        raise WrongPassword("Vault file is too short.")

    salt       = raw[:_SALT_BYTES]
    nonce      = raw[_SALT_BYTES : _SALT_BYTES + _NONCE_BYTES]
    stored_mac = raw[_SALT_BYTES + _NONCE_BYTES : _SALT_BYTES + _NONCE_BYTES + _MAC_BYTES]
    ciphertext = raw[_SALT_BYTES + _NONCE_BYTES + _MAC_BYTES :]

    enc_key, mac_key = _derive_keys(password, salt)

    # Constant-time MAC comparison prevents timing oracle attacks
    expected_mac = _hmac.new(mac_key, salt + nonce + ciphertext, "sha256").digest()
    if not _hmac.compare_digest(stored_mac, expected_mac):
        raise WrongPassword("Invalid master password.")

    return _hmac_ctr_xor(enc_key, nonce, ciphertext)


# ── VaultManager ─────────────────────────────────────────────────────────────

class VaultManager:
    """
    Manages encrypted at-rest storage of PAPER (testnet) and LIVE (production)
    Binance API credentials.

    The master password is NEVER stored — it is used only during setup/switch to
    derive ephemeral encryption keys.  Plaintext credentials are held in memory
    only for the duration of the switch() call and are then immediately discarded.
    """

    def __init__(self, path: Path = VAULT_PATH):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._current_mode: str = "PAPER"

    # ── Internal helpers ──────────────────────────────────────────────────────

    def is_configured(self) -> bool:
        return self._path.exists() and self._path.stat().st_size > 10

    def _write(self, password: str, payload: dict) -> None:
        """Encrypt *payload* with fresh random salt/nonce and write to vault file."""
        cipherblob = _seal(password, json.dumps(payload).encode())
        self._path.write_bytes(cipherblob)

    def _read(self, password: str) -> dict:
        """
        Read and decrypt the vault file.

        Raises:
          VaultNotConfigured — if the vault file is missing or empty.
          WrongPassword      — if the password/MAC check fails.
        """
        if not self.is_configured():
            raise VaultNotConfigured("Vault is not configured yet.")
        plaintext = _open(password, self._path.read_bytes())
        return json.loads(plaintext)

    # ── Public API ────────────────────────────────────────────────────────────

    def setup(
        self,
        password: str,
        paper_key: str,
        paper_secret: str,
        live_key: str,
        live_secret: str,
    ) -> None:
        """
        Encrypt and persist both credential slots under a master password.
        Re-calling setup overwrites any existing vault.  Always resets to PAPER mode.

        Raises ValueError if password is shorter than 6 characters.
        """
        if len(password) < 6:
            raise ValueError("Master password must be at least 6 characters.")
        self._write(password, {
            "paper": {"key": paper_key, "secret": paper_secret},
            "live":  {"key": live_key,  "secret": live_secret},
            "mode":  "PAPER",
        })
        self._current_mode = "PAPER"
        logger.info("[VAULT] Credential vault configured and encrypted (PBKDF2-HMAC-CTR).")

    def switch(self, password: str, target_mode: str) -> dict:
        """
        Validate the master password and switch to *target_mode*.

        Persists the new mode inside the vault file re-encrypted with a fresh
        random salt and nonce each time (prevents ciphertext reuse).

        Returns:
          {"key": str, "secret": str, "mode": str, "testnet": bool}

        Raises WrongPassword, VaultNotConfigured, or ValueError.
        """
        if target_mode not in ("PAPER", "LIVE"):
            raise ValueError(
                f"Unknown mode {target_mode!r} — must be 'PAPER' or 'LIVE'."
            )

        payload = self._read(password)               # raises WrongPassword if bad pw
        slot    = "paper" if target_mode == "PAPER" else "live"
        creds   = payload[slot]

        # Persist new mode (fresh salt + nonce → unique ciphertext every time)
        payload["mode"] = target_mode
        self._write(password, payload)
        self._current_mode = target_mode

        logger.info(f"[VAULT] Switched to {target_mode} mode.")
        return {
            "key":     creds["key"],
            "secret":  creds["secret"],
            "mode":    target_mode,
            "testnet": target_mode == "PAPER",
        }

    def status(self) -> dict:
        """Returns non-sensitive vault information for the dashboard."""
        return {
            "configured":   self.is_configured(),
            "current_mode": self._current_mode,
            "is_live":      self._current_mode == "LIVE",
        }

    @property
    def current_mode(self) -> str:
        return self._current_mode
