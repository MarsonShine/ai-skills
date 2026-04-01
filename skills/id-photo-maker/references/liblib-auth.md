# Liblib Auth Notes

## Query parameters required on every request

Every Liblib API request must include these query parameters:

- `AccessKey`
- `Signature`
- `Timestamp`
- `SignatureNonce`

`Timestamp` is a millisecond timestamp string and is valid for 5 minutes.

## Signature formula

1. Build the plaintext:

```text
{uri_path}&{timestamp}&{signature_nonce}
```

Example:

```text
/api/generate/webui/status&1725458584000&random1232
```

2. Sign with `HMAC-SHA1` using the `SecretKey`.

3. Encode the digest as URL-safe Base64 and strip trailing `=`.

## Paths used by this skill

- `POST /api/generate/webui/text2img/ultra`
- `POST /api/generate/webui/img2img/ultra`
- `POST /api/generate/webui/status`

## Default template UUIDs

- Text to image: `5d7e67009b344550bc1aa6ccbfa1d7f4`
- Image to image: `07e00af4fc464c7ab55ff906f8acf1b7`

## Notes

- The signature is generated from the URI path, not the full absolute URL.
- Do not place the secret in logs or user-facing output.
- The bundled `liblib_client.py` already implements this signing flow.
