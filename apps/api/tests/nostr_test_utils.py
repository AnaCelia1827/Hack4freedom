from datetime import datetime, timezone

from bluejet_api.auth import (
    SECP256K1_G,
    SECP256K1_ORDER,
    _point_multiply,
    _tagged_hash,
    nostr_event_id,
)


def pubkey_for_private_key(private_key: int = 1) -> str:
    point = _point_multiply(private_key, SECP256K1_G)
    return point[0].to_bytes(32, "big").hex()


def _sign(message: bytes, private_key: int) -> tuple[str, str]:
    public_point = _point_multiply(private_key, SECP256K1_G)
    effective_key = private_key if public_point[1] % 2 == 0 else SECP256K1_ORDER - private_key
    pubkey = public_point[0].to_bytes(32, "big")
    aux = bytes(32)
    masked = bytes(
        left ^ right
        for left, right in zip(
            effective_key.to_bytes(32, "big"), _tagged_hash("BIP0340/aux", aux)
        )
    )
    nonce = int.from_bytes(_tagged_hash("BIP0340/nonce", masked + pubkey + message), "big")
    nonce %= SECP256K1_ORDER
    nonce_point = _point_multiply(nonce, SECP256K1_G)
    effective_nonce = nonce if nonce_point[1] % 2 == 0 else SECP256K1_ORDER - nonce
    r_bytes = nonce_point[0].to_bytes(32, "big")
    challenge = int.from_bytes(
        _tagged_hash("BIP0340/challenge", r_bytes + pubkey + message), "big"
    ) % SECP256K1_ORDER
    signature = r_bytes + ((effective_nonce + challenge * effective_key) % SECP256K1_ORDER).to_bytes(32, "big")
    return pubkey.hex(), signature.hex()


def signed_auth_payload(challenge_response: dict, private_key: int = 1, created_at: int | None = None) -> dict:
    challenge = challenge_response["challenge"]
    signing = challenge_response["signing"]
    pubkey = pubkey_for_private_key(private_key)
    event = {
        "pubkey": pubkey,
        "created_at": created_at or int(datetime.now(timezone.utc).timestamp()),
        "kind": signing["kind"],
        "tags": [
            ["u", signing["url"]],
            ["method", signing["method"]],
            ["challenge", challenge],
            ["payload", signing["payload_hash"]],
        ],
        "content": challenge,
    }
    event["id"] = nostr_event_id(event)
    _, event["sig"] = _sign(bytes.fromhex(event["id"]), private_key)
    return {
        "challenge": challenge,
        "pubkey": pubkey,
        "signature": event["sig"],
        "event": event,
    }
