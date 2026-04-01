#!/usr/bin/env python3

from __future__ import annotations

import base64
import hmac
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from hashlib import sha1
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from id_photo_common import download_file, ensure_directory, guess_extension_from_url

DEFAULT_BASE_URL = "https://openapi.liblibai.cloud"
TEXT_TEMPLATE_UUID = "5d7e67009b344550bc1aa6ccbfa1d7f4"
IMG2IMG_TEMPLATE_UUID = "07e00af4fc464c7ab55ff906f8acf1b7"


class LiblibApiError(RuntimeError):
    pass


class LiblibClient:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,
    ) -> None:
        self.access_key = access_key.strip()
        self.secret_key = secret_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @staticmethod
    def make_signature(secret_key: str, uri: str, timestamp: str, nonce: str) -> str:
        content = f"{uri}&{timestamp}&{nonce}".encode("utf-8")
        digest = hmac.new(secret_key.encode("utf-8"), content, sha1).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def signed_url(self, uri: str) -> str:
        timestamp = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex
        signature = self.make_signature(self.secret_key, uri, timestamp, nonce)
        query = urllib.parse.urlencode(
            {
                "AccessKey": self.access_key,
                "Signature": signature,
                "Timestamp": timestamp,
                "SignatureNonce": nonce,
            }
        )
        return f"{self.base_url}{uri}?{query}"

    def _request_json(self, uri: str, payload: dict) -> dict:
        url = self.signed_url(uri)
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "CopilotCLI/id-photo-maker 1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise LiblibApiError(f"HTTP {exc.code} calling {uri}: {body}") from exc
        except urllib.error.URLError as exc:
            raise LiblibApiError(f"Network error calling {uri}: {exc.reason}") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LiblibApiError(f"Invalid JSON response from {uri}: {raw}") from exc

        if payload.get("code", 0) != 0:
            raise LiblibApiError(payload.get("msg") or f"Liblib returned code {payload.get('code')}")

        data = payload.get("data")
        if not isinstance(data, dict):
            raise LiblibApiError(f"Liblib response missing data object for {uri}")
        return data

    def text_to_image(
        self,
        *,
        prompt: str,
        img_count: int = 1,
        aspect_ratio: str = "portrait",
        image_width: int | None = None,
        image_height: int | None = None,
        steps: int = 30,
        control_type: str | None = None,
        control_image: str | None = None,
        template_uuid: str = TEXT_TEMPLATE_UUID,
    ) -> dict:
        params: dict[str, object] = {
            "prompt": prompt,
            "imgCount": img_count,
            "steps": steps,
        }

        if image_width and image_height:
            params["imageSize"] = {"width": image_width, "height": image_height}
        else:
            params["aspectRatio"] = aspect_ratio

        if control_type or control_image:
            if not (control_type and control_image):
                raise LiblibApiError("Both controlType and controlImage are required together.")
            params["controlnet"] = {
                "controlType": control_type,
                "controlImage": control_image,
            }

        return self._request_json(
            "/api/generate/webui/text2img/ultra",
            {"templateUuid": template_uuid, "generateParams": params},
        )

    def image_to_image(
        self,
        *,
        prompt: str,
        source_image: str,
        img_count: int = 1,
        control_type: str | None = None,
        control_image: str | None = None,
        template_uuid: str = IMG2IMG_TEMPLATE_UUID,
    ) -> dict:
        params: dict[str, object] = {
            "prompt": prompt,
            "sourceImage": source_image,
            "imgCount": img_count,
        }

        if control_type or control_image:
            if not (control_type and control_image):
                raise LiblibApiError("Both controlType and controlImage are required together.")
            params["controlnet"] = {
                "controlType": control_type,
                "controlImage": control_image,
            }

        return self._request_json(
            "/api/generate/webui/img2img/ultra",
            {"templateUUID": template_uuid, "generateParams": params},
        )

    def get_status(self, generate_uuid: str) -> dict:
        return self._request_json(
            "/api/generate/webui/status",
            {"generateUuid": generate_uuid},
        )

    def wait_for_completion(
        self,
        generate_uuid: str,
        *,
        poll_interval: float = 5.0,
        timeout: float = 300.0,
    ) -> dict:
        deadline = time.monotonic() + timeout
        last_status: int | None = None

        while time.monotonic() < deadline:
            data = self.get_status(generate_uuid)
            status = data.get("generateStatus")
            images = data.get("images") or []
            if images:
                return data

            if status != last_status:
                message = data.get("generateMsg") or ""
                print(f"[liblib] status={status} {message}".strip(), file=sys.stderr)
                last_status = status

            if status in {-1, 6, 7}:
                raise LiblibApiError(
                    f"Generation failed with status {status}: {data.get('generateMsg') or 'unknown error'}"
                )

            time.sleep(max(0.5, poll_interval))

        raise TimeoutError(f"Timed out waiting for Liblib task {generate_uuid}")

    def download_images(
        self,
        images: list[dict],
        output_dir: str | Path,
        *,
        prefix: str = "liblib",
    ) -> list[dict]:
        destination_dir = ensure_directory(output_dir)
        downloaded: list[dict] = []

        for index, image_info in enumerate(images, start=1):
            image_url = image_info.get("imageUrl")
            if not image_url:
                continue

            suffix = guess_extension_from_url(image_url)
            target = destination_dir / f"{prefix}-{index}{suffix}"
            saved_path = download_file(image_url, target, timeout=self.timeout)
            downloaded.append(
                {
                    "imageUrl": image_url,
                    "localPath": str(saved_path),
                    "seed": image_info.get("seed"),
                    "auditStatus": image_info.get("auditStatus"),
                }
            )

        return downloaded
