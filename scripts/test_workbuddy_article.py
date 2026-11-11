"""Tests for the workbuddy-wechat-article skill.

These cover the deterministic parts: profile validation, AI-flavour scoring,
rewrite verification, image tiers and rendering.  Network calls are never made.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import urllib.parse
import urllib.request

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/workbuddy-wechat-article"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import blocks  # noqa: E402
import images  # noqa: E402
import profile as profile_module  # noqa: E402
import publish  # noqa: E402
import render  # noqa: E402
import rewrite  # noqa: E402
import voice  # noqa: E402

ARTICLE = SCRIPTS / "article.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(ARTICLE), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


class ProfileTests(unittest.TestCase):
    def test_answers_produce_valid_profile_and_round_trip(self):
        selected = profile_module.from_answers(
            {
                "name": "阿柯",
                "city": "杭州",
                "members": [{"relation": "daughter", "nickname": "豆豆", "age": 6}],
                "topics": ["亲子日常"],
                "tone": "warm",
                "person": "first",
                "sentence_len": "mixed",
                "emoji": "sparing",
                "whitespace": "airy",
            }
        )
        self.assertEqual(selected["identity"]["name"], "阿柯")
        self.assertEqual(selected["family"]["members"][0]["nickname"], "豆豆")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "profile.yaml"
            profile_module.save(selected, target)
            loaded = profile_module.load(target)
            self.assertEqual(loaded, selected)

    def test_unknown_field_is_rejected(self):
        with self.assertRaises(profile_module.ProfileError) as caught:
            profile_module.from_answers({"name": "阿柯", "topics": ["日常"], "nope": 1})
        self.assertIn("answers.nope", str(caught.exception))

    def test_child_requires_age_and_enum_is_checked(self):
        with self.assertRaises(profile_module.ProfileError):
            profile_module.from_answers(
                {"name": "阿柯", "topics": ["日常"], "members": [{"relation": "daughter", "nickname": "豆豆"}]}
            )
        with self.assertRaises(profile_module.ProfileError):
            profile_module.from_answers({"name": "阿柯", "topics": ["日常"], "tone": "loud"})
        with self.assertRaises(profile_module.ProfileError):
            profile_module.from_answers({"name": "阿柯", "topics": []})

    @unittest.skipIf(profile_module.yaml is None, "PyYAML is not installed")
    def test_example_is_valid(self):
        data = profile_module.yaml.safe_load(profile_module.example())
        self.assertEqual(profile_module.validate(data)["identity"]["name"], "阿柯")


class VoiceTests(unittest.TestCase):
    AI_TEXT = (
        "首先，我们要认识到这件事的底层逻辑。它不是一次简单的搬家，而是人生阶段的跃迁。"
        "值得注意的是，在这个过程中，我们需要形成闭环——从认知到行动。"
        "其次，未来的日子一定会越来越好，愿我们都能被生活温柔以待。"
    )
    HUMAN_TEXT = (
        "豆豆在门口蹲了十分钟。我问她看什么，她说蚂蚁在搬一粒比她指甲盖还小的饼干屑。"
        "昨天下午三点，雨刚停，水泥地上还有水。她不肯走，我就陪她蹲着。"
        "后来饼干屑掉进了砖缝，她伸手去抠，抠了半天，指甲缝里全是灰。"
        "回家路上她一句话没说，进门才说：妈妈，蚂蚁会不会哭。"
    )

    def test_ai_text_scores_lower_than_human_text(self):
        ai = voice.analyze_text(self.AI_TEXT)
        human = voice.analyze_text(self.HUMAN_TEXT)
        self.assertLess(ai["scores"]["final"], human["scores"]["final"])
        self.assertLessEqual(ai["scores"]["final"], 69)
        self.assertGreaterEqual(human["scores"]["final"], 70)
        self.assertTrue(any(issue["code"] == "hard_word" for issue in ai["issues"]))
        self.assertTrue(ai["targets"])
        self.assertTrue(any(item["code"] == "detail_density" for item in human["positive"]))

    def test_is_deterministic(self):
        first = json.dumps(voice.analyze_text(self.AI_TEXT), ensure_ascii=False, sort_keys=True)
        second = json.dumps(voice.analyze_text(self.AI_TEXT), ensure_ascii=False, sort_keys=True)
        self.assertEqual(first, second)

    def test_quoted_hard_word_is_kept(self):
        document = {
            "blocks": [
                {"type": "p", "text": "这本书反复讲“底层逻辑”，我没读完。"},
                {"type": "p", "text": "豆豆在门口蹲了十分钟。她看蚂蚁搬饼干屑。"},
            ]
        }
        report = voice.analyze(document)
        kept = [item for item in report["keep"] if item["code"] == "hard_word"]
        self.assertTrue(kept)
        self.assertFalse(any(item["penalized"] and item["code"] == "hard_word" for item in report["issues"]))

    def test_single_dash_is_kept(self):
        document = {"blocks": [{"type": "p", "text": "我推开门——屋里没人。豆豆在沙发上睡着了。"}]}
        report = voice.analyze(document)
        self.assertFalse(any(item["code"] == "em_dash" and item["penalized"] for item in report["issues"]))
        self.assertTrue(any(item["code"] == "em_dash" for item in report["keep"]))

    def test_ending_cliche_is_flagged(self):
        document = {
            "blocks": [
                {"type": "p", "text": "那天我们把最后一箱书搬上楼，手上全是灰。"},
                {"type": "p", "text": "未来的日子一定会越来越好。"},
            ]
        }
        report = voice.analyze(document)
        self.assertTrue(any(item["code"] == "empty_ending" and item["penalized"] for item in report["issues"]))


class RewriteTests(unittest.TestCase):
    def setUp(self):
        self.document = {
            "blocks": [
                {
                    "type": "p",
                    "text": "这不是一次普通的搬家——而是我们第一次真正离开父母。这不是一次简单的告别，而是重新开始。",
                },
                {"type": "p", "text": "豆豆在门口蹲了十分钟。"},
            ]
        }
        self.report = voice.analyze(self.document)

    def test_valid_rewrite_is_applied(self):
        target = self.report["targets"][0]
        result = rewrite.apply(
            self.document,
            self.report,
            [{"sentence_id": target["sentence_id"], "rewrite": "那天搬家，我第一次觉得，离开父母是件具体的事。"}],
        )
        self.assertEqual(result["applied"], 1)
        self.assertIn("那天搬家", result["document"]["blocks"][0]["text"])
        self.assertNotIn("这不是一次普通的搬家", result["document"]["blocks"][0]["text"])

    def test_fact_loss_is_rejected(self):
        target = next(item for item in self.report["targets"] if "搬家" in item["text"])
        result = rewrite.apply(
            self.document,
            self.report,
            [{"sentence_id": target["sentence_id"], "rewrite": "那天我们走了。"}],
        )
        self.assertEqual(result["applied"], 0)
        self.assertTrue(result["rejected"])
        self.assertIn("丢失事实", " ".join(result["rejected"][0]["check"]["reasons"]))

    def test_two_sentence_rewrite_is_rejected(self):
        target = self.report["targets"][0]
        result = rewrite.apply(
            self.document,
            self.report,
            [{"sentence_id": target["sentence_id"], "rewrite": "那天搬家。我忽然明白了很多。"}],
        )
        self.assertEqual(result["applied"], 0)
        self.assertIn("不是一句话", " ".join(result["rejected"][0]["check"]["reasons"]))

    def test_multiple_rewrites_in_one_field(self):
        targets = {item["sentence_index"]: item for item in self.report["targets"]}
        self.assertIn(0, targets)
        self.assertIn(1, targets)
        result = rewrite.apply(
            self.document,
            self.report,
            [
                {"sentence_id": targets[0]["sentence_id"], "rewrite": "那天搬家，我第一次觉得，离开父母是件具体的事。"},
                {"sentence_id": targets[1]["sentence_id"], "rewrite": "这是第一次简单的告别，也是重新开始。"},
            ],
        )
        self.assertEqual(result["applied"], 2)
        text = result["document"]["blocks"][0]["text"]
        self.assertNotIn("这不是一次普通的搬家", text)
        self.assertNotIn("这不是一次简单的告别", text)
        self.assertEqual(text.count("。"), 2)

    def test_keep_is_not_applied(self):
        target = self.report["targets"][0]
        result = rewrite.apply(
            self.document,
            self.report,
            [{"sentence_id": target["sentence_id"], "keep": True, "reason": "作者语感"}],
        )
        self.assertEqual(result["applied"], 0)
        self.assertTrue(result["keep"])


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_lossless_png_is_pixel_equal(self):
        source = self.root / "chart.png"
        image = Image.new("RGBA", (320, 200), (20, 30, 40, 255))
        image.putpixel((10, 10), (255, 0, 0, 128))
        image.save(source)
        result = images.prepare(source, self.root / "out", "chart", "lossless")
        self.assertTrue(result["lossless"])
        self.assertTrue(result["pixel_equal"])
        self.assertEqual(result["src_px"], result["output_px"])

    def test_noise_png_over_limit_raises_exit_7(self):
        source = self.root / "noise.png"
        pixels = random.Random(1526).randbytes(900 * 900 * 3)
        Image.frombytes("RGB", (900, 900), pixels).save(source)
        with self.assertRaises(images.LosslessError) as caught:
            images.prepare(source, self.root / "out", "noise", "lossless")
        self.assertTrue(getattr(caught.exception, "options"))
        balanced = images.prepare(source, self.root / "out2", "noise", "balanced")
        self.assertLess(balanced["output_bytes"], images.LIMITS["body"])
        self.assertFalse(balanced["lossless"])

    def test_jpeg_lossless_is_reported_as_lossy(self):
        source = self.root / "photo.jpg"
        Image.frombytes("RGB", (640, 480), random.Random(9).randbytes(640 * 480 * 3)).save(source, quality=85)
        result = images.prepare(source, self.root / "out", "photo", "lossless")
        self.assertFalse(result["lossless"])
        self.assertIn("JPEG", result["reason"])

    def test_remote_verify_detects_resize(self):
        expected = self.root / "expected.png"
        Image.new("RGB", (40, 20), "navy").save(expected)
        same = self.root / "same.png"
        same.write_bytes(expected.read_bytes())
        shrunk = self.root / "shrunk.png"
        Image.new("RGB", (20, 10), "navy").save(shrunk)
        self.assertTrue(images.verify(expected, same)["lossless"])
        self.assertFalse(images.verify(expected, shrunk)["lossless"])


class RenderTests(unittest.TestCase):
    def document(self) -> dict:
        return {
            "title": "测试",
            "scene": "family",
            "blocks": [
                {"type": "lead", "text": "豆豆在门口蹲了十分钟。"},
                {"type": "p", "text": "第一段。"},
                {"type": "photo_polaroid", "src": "a.jpg", "caption": "拍立得"},
                {"type": "kid_quote", "text": "蚂蚁会不会哭", "nickname": "豆豆", "age": 6},
                {"type": "dialogue", "lines": [{"who": "left", "text": "你蹲多久了"}, {"who": "right", "text": "十分钟"}]},
                {"type": "timeline", "items": [{"time": "08:10", "title": "出门"}]},
                {"type": "compare_pair", "a": "b.jpg", "b": "c.jpg", "cap_a": "那年", "cap_b": "今年"},
                {"type": "memory_band", "year": "2019", "text": "第一次见面"},
                {"type": "drop_cap", "text": "早上出门的时候，风很大。"},
                {"type": "countdown_card", "number": "365", "unit": "天", "label": "到今天"},
            ],
        }

    def test_all_scenes_preserve_text_and_avoid_forbidden_css(self):
        keywords = ["豆豆在门口蹲了十分钟。", "拍立得", "蚂蚁会不会哭", "你蹲多久了", "十分钟", "08:10 出门", "那年", "今年", "2019 第一次见面", "早上出门的时候，风很大。", "365 天 到今天"]
        for scene in ("family", "travel", "daily", "anniversary"):
            document = self.document()
            document["scene"] = scene
            html, warnings, meta = render.render_article(document, {}, scene)
            plain = re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", html))
            for keyword in keywords:
                self.assertIn(re.sub(r"\s+", "", keyword), plain, f"{scene}: {keyword}")
            self.assertNotIn("display:flex", html)
            self.assertNotIn("position:absolute", html)
            self.assertNotIn("transform:", html)
            self.assertNotIn("calc(", html)
            self.assertEqual(meta["scene"], scene)

    def test_preview_page_contains_images_and_report(self):
        document = self.document()
        html, warnings, meta = render.render_article(document, {}, "family")
        page = render.render_preview(document, html, meta, images=[], voice_report=None)
        self.assertIn("公众号预览", page)
        self.assertIn("375px", page)
        self.assertIn("430px", page)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.image = self.root / "photo.jpg"
        Image.frombytes("RGB", (640, 480), random.Random(3).randbytes(640 * 480 * 3)).save(self.image, quality=90)
        self.blocks = self.root / "blocks.json"
        self.blocks.write_text(
            json.dumps(
                {
                    "title": "豆豆的蚂蚁",
                    "author": "阿柯",
                    "scene": "family",
                    "blocks": [
                        {"type": "p", "text": "豆豆在门口蹲了十分钟。她看蚂蚁搬饼干屑。"},
                        {"type": "photo_polaroid", "src": str(self.image), "caption": "门口"},
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def test_preview_and_confirm(self):
        workdir = self.root / "article"
        result = run_cli(
            "preview", "--blocks", str(self.blocks), "--workdir", str(workdir),
            "--quality", "balanced", "--account", "wx-test", "--action", "draft",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertTrue(Path(payload["previewPath"]).is_file())
        self.assertTrue((workdir / "bundle.json").is_file())
        self.assertEqual(payload["confirmation"], publish.confirm_code("wx-test", "draft", payload["version"]))
        confirm = run_cli("confirm", "--workdir", str(workdir), "--account", "wx-test", "--action", "draft")
        self.assertEqual(confirm.returncode, 0)
        self.assertEqual(json.loads(confirm.stdout)["confirmation"], payload["confirmation"])

    def test_lossless_over_limit_returns_exit_7(self):
        noisy = self.root / "noise.png"
        Image.frombytes("RGB", (900, 900), random.Random(7).randbytes(900 * 900 * 3)).save(noisy)
        document = json.loads(self.blocks.read_text(encoding="utf-8"))
        document["blocks"][1]["src"] = str(noisy)
        path = self.root / "noise-blocks.json"
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        result = run_cli(
            "qc", "--blocks", str(path), "--quality", "lossless", "--out-dir", str(self.root / "qc"),
        )
        self.assertEqual(result.returncode, 7, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["options"])

    def test_draft_rejects_wrong_confirmation(self):
        workdir = self.root / "article"
        result = run_cli(
            "preview", "--blocks", str(self.blocks), "--workdir", str(workdir), "--quality", "balanced",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        draft = run_cli(
            "draft", "--workdir", str(workdir), "--account", "wx-test", "--action", "draft",
            "--confirmed", "000000000000", "--appid", "wx-test", "--secret", "secret",
        )
        self.assertEqual(draft.returncode, 2)
        self.assertIn("确认码", json.loads(draft.stdout)["error"])

    def test_privacy_boundary_is_enforced(self):
        profile = {
            "version": 1,
            "identity": {"name": "阿柯"},
            "family": {"ok_to_write": False, "members": [{"relation": "daughter", "nickname": "豆豆", "age": 6}]},
            "topics": {"frequent": ["亲子日常"], "never": [], "series": []},
            "voice": {"tone": "warm", "person": "first", "sentence_len": "mixed", "emoji": "sparing"},
            "typesetting": {"scene": "family", "whitespace": "normal"},
            "taboo": {},
        }
        profile_path = self.root / "profile.yaml"
        profile_module.save(profile_module.validate(profile), profile_path)
        result = run_cli(
            "check", "--blocks", str(self.blocks), "--profile", str(profile_path),
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("不写家人", json.loads(result.stdout)["error"])


class PublishTests(unittest.TestCase):
    """Exercise the draft path with a fake WeChat endpoint (no network)."""

    class Response:
        def __init__(self, payload: dict):
            self.payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        def read(self, *args):
            return self.payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def test_draft_uploads_replaces_urls_and_reads_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "chart.png"
            Image.new("RGBA", (320, 200), (20, 30, 40, 255)).save(image)
            document = {
                "title": "一张图",
                "author": "阿柯",
                "scene": "daily",
                "blocks": [
                    {"type": "p", "text": "豆豆在门口蹲了十分钟。"},
                    {"type": "image", "src": str(image), "caption": "图"},
                ],
            }
            blocks_path = root / "blocks.json"
            blocks_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
            workdir = root / "article"
            preview = run_cli("preview", "--blocks", str(blocks_path), "--workdir", str(workdir), "--quality", "lossless")
            self.assertEqual(preview.returncode, 0, preview.stderr + preview.stdout)
            payload = json.loads(preview.stdout)
            code = publish.confirm_code("wx-test", "draft", payload["version"])
            requests: list[urllib.request.Request] = []
            stored: dict[str, str] = {}

            def fake_urlopen(request, timeout=30):
                url = str(request.full_url)
                requests.append(request)
                path = urllib.parse.urlparse(url).path
                if path.endswith("/stable_token"):
                    return self.Response({"access_token": "TOKEN"})
                if path.endswith("/media/uploadimg"):
                    return self.Response({"url": "https://cdn.example/body.png"})
                if path.endswith("/material/add_material"):
                    return self.Response({"media_id": "COVER", "url": "https://cdn.example/cover.png"})
                if path.endswith("/draft/add"):
                    body = json.loads(request.data.decode("utf-8"))
                    stored["title"] = body["articles"][0]["title"]
                    stored["thumb"] = body["articles"][0]["thumb_media_id"]
                    stored["content"] = body["articles"][0]["content"]
                    return self.Response({"media_id": "DRAFT"})
                if path.endswith("/draft/get"):
                    return self.Response(
                        {
                            "news_item": [
                                {
                                    "title": stored.get("title", ""),
                                    "content": "<section>ok</section>",
                                    "thumb_media_id": stored.get("thumb", ""),
                                }
                            ]
                        }
                    )
                return self.Response({"errcode": 0})

            def fake_download(url, target):
                source = workdir / ("images/cover.png" if "cover" in url else "images/body-01.png")
                target.write_bytes(source.read_bytes())

            with mock.patch.object(publish.urllib.request, "urlopen", side_effect=fake_urlopen), \
                    mock.patch.object(publish, "download", side_effect=fake_download):
                result = publish.draft(
                    workdir, "wx-test", "draft", code, appid="wx-test", secret="secret", verify=True,
                )
            self.assertTrue(result["ok"])
            self.assertEqual(result["media_id"], "DRAFT")
            self.assertTrue(result["quality"][0]["lossless"])
            self.assertTrue(result["draft_readback"]["ok"])
            self.assertTrue(result["draft_readback"]["title_matches"])
            self.assertIn("https://cdn.example/body.png", stored["content"])
            self.assertNotIn("images/body-01.png", stored["content"])
            cover_requests = [request for request in requests if "type=image" in str(request.full_url)]
            self.assertTrue(cover_requests)
            self.assertTrue(any("access_token=TOKEN" in str(request.full_url) for request in requests))


if __name__ == "__main__":
    unittest.main()
