import base64
import hashlib
import hmac
import json


class AccessDenied(Exception):
    pass


def verify_token(token, secret, now):
    try:
        payload_part, signature_part = token.split(".")
        signature = base64.urlsafe_b64decode(signature_part + "=" * (-len(signature_part) % 4))
        expected = hmac.new(secret, payload_part.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise AccessDenied("invalid token")
        payload = json.loads(base64.urlsafe_b64decode(payload_part + "=" * (-len(payload_part) % 4)))
        if not isinstance(payload, dict):
            raise AccessDenied("invalid claims")
        if not isinstance(payload.get("sub"), str) or not payload["sub"]:
            raise AccessDenied("invalid subject")
        expiry = payload.get("exp")
        if isinstance(expiry, bool) or not isinstance(expiry, (int, float)) or now >= expiry:
            raise AccessDenied("expired token")
        return payload
    except AccessDenied:
        raise
    except (ValueError, TypeError, UnicodeError, KeyError) as error:
        raise AccessDenied("invalid token") from error


def read_note(token, note_id, notes, secret, now):
    payload = verify_token(token, secret, now)
    note = notes.get(note_id)
    if note is None or payload["sub"] != note["owner"]:
        raise AccessDenied("access denied")
    return note["text"]
