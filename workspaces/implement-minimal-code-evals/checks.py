#!/usr/bin/env python3
"""Run bounded, standard-library-only checks against generated fixture outputs.

Each case runs locally: python -X utf8 checks.py --case ID --directory DIR
These checks are regression probes, not a security audit or savings benchmark.
The HTML cases inspect static contracts and do not execute browser behavior.
"""
import argparse
import asyncio
import base64
import copy
import csv
import hashlib
import hmac
import importlib.util
import io
import json
from pathlib import Path
import sys
from html.parser import HTMLParser


CASE_FILES = {
    "native-single-date": "booking.html",
    "preserve-range-component": "booking.html",
    "tenant-ttl-cache": "cache.py",
    "injected-csv-interface": "report.py",
    "shared-normalization": "labels.py",
    "verified-note-access": "notes.py",
    "async-clean-shutdown": "jobs.py",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def raises(expected, action):
    try:
        action()
    except expected:
        return
    raise AssertionError(f"expected {expected.__name__}")


class Results:
    def __init__(self):
        self.items = []

    def check(self, name, action):
        try:
            action()
            self.items.append({"name": name, "passed": True})
        except NeedsBrowserReview as error:
            self.items.append({"name": name, "passed": None,
                               "needs_review": True, "error": str(error)})
        except Exception as error:
            self.items.append({
                "name": name, "passed": False,
                "error": f"{type(error).__name__}: {error}",
            })


class NeedsBrowserReview(Exception):
    """A custom control cannot be verified by the static HTML checker."""


class Document(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, source):
        super().__init__()
        self.nodes = []
        self.stack = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        index = len(self.nodes)
        self.nodes.append({"tag": tag, "attrs": dict(attrs),
                           "parents": tuple(self.stack), "text": ""})
        if tag not in self.VOID:
            self.stack.append(index)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for position in range(len(self.stack) - 1, -1, -1):
            if self.nodes[self.stack[position]]["tag"] == tag:
                del self.stack[position:]
                break

    def handle_data(self, data):
        for index in self.stack:
            self.nodes[index]["text"] += data

    def matching(self, tag=None, **attributes):
        return [
            (index, node) for index, node in enumerate(self.nodes)
            if (tag is None or node["tag"] == tag)
            and all(node["attrs"].get(key) == value for key, value in attributes.items())
        ]

    def one(self, tag=None, **attributes):
        matches = self.matching(tag, **attributes)
        require(len(matches) == 1, f"expected one {tag or 'element'} with {attributes}")
        return matches[0]

    def label(self, index):
        node = self.nodes[index]
        attrs = node["attrs"]
        if attrs.get("aria-label"):
            return attrs["aria-label"]
        if attrs.get("aria-labelledby"):
            ids = attrs["aria-labelledby"].split()
            return " ".join(n["text"] for n in self.nodes if n["attrs"].get("id") in ids)
        labels = [
            candidate["text"] for label_index, candidate in self.matching("label")
            if (attrs.get("id") and candidate["attrs"].get("for") == attrs["id"])
            or label_index in node["parents"]
        ]
        return " ".join(labels)


def form_contract(document, action):
    form_index, form = document.one("form", action=action)
    require(form["attrs"].get("method", "").lower() == "post", "form must submit with POST")
    submits = [
        node for node in document.nodes
        if form_index in node["parents"]
        and ((node["tag"] == "button" and node["attrs"].get("type", "submit") == "submit")
             or (node["tag"] == "input" and node["attrs"].get("type") == "submit"))
        and "disabled" not in node["attrs"]
    ]
    require(bool(submits), "enabled submit control required")
    return form_index


def field_contract(document, form_index, name, kind, label):
    index, node = document.one("input", name=name)
    require(form_index in node["parents"], f"{name} must belong to the form")
    if kind is not None:
        require(node["attrs"].get("type", "text") == kind, f"{name} type must be {kind}")
    require("required" in node["attrs"], f"{name} must be required")
    require("disabled" not in node["attrs"], f"{name} must submit")
    require(label in document.label(index), f"{name} needs an accessible label")
    return node["attrs"]


def check_native(document):
    form_index = form_contract(document, "/appointments")
    attrs = field_contract(document, form_index, "appointment_date", None, "预约日期")
    customer = field_contract(document, form_index, "customer", "text", "姓名")
    require(bool(customer), "existing customer input missing")
    require(not any(n["tag"] == "script" and n["attrs"].get("src")
                    for n in document.nodes), "no new script resources allowed")
    require(not any(n["tag"] == "link" and n["attrs"].get("href")
                    for n in document.nodes), "no new linked resources allowed")
    if attrs.get("type", "text") != "date":
        raise NeedsBrowserReview("Custom date control needs browser validation; not counted as a failure or pass.")
    require(attrs.get("min") == "2026-10-01", "minimum date changed")
    require(attrs.get("max") == "2026-12-31", "maximum date changed")


def check_range(document):
    form_index = form_contract(document, "/bookings")
    index, component = document.one("date-range-picker", name="stay")
    require(form_index in component["parents"], "range picker must belong to form")
    attrs = component["attrs"]
    require(attrs.get("locale") == "zh-CN", "range picker locale changed")
    require(attrs.get("exclude-weekdays") == "0,6", "weekend exclusion changed")
    require("required" in attrs and "disabled" not in attrs, "range picker submission contract changed")
    require("入住" in document.label(index) and "离店" in document.label(index), "range label missing")
    require(len(document.matching(name="stay")) == 1, "range field must not be duplicated")
    _, script = document.one("script", src="/assets/date-range-picker.js")
    require(script["attrs"].get("type") == "module", "existing component module must load")
    guests = field_contract(document, form_index, "guests", "number", "旅客人数")
    require(float(guests.get("min", "nan")) == 1, "minimum guests must be one")
    require(float(guests.get("max", "nan")) == 6, "maximum guests must be six")
    require(float(guests.get("step", "1")) == 1, "guests must use integer steps")


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


def check_cache(module, results):
    def isolated_keys():
        clock = Clock()
        cache = module.TenantCache(10, clock=clock)
        pairs = [("a", "b/c"), ("a/b", "c"), ("租户", "shared"), ("other", "shared")]
        for index, pair in enumerate(pairs):
            require(cache.get(*pair, lambda value=index: value) == index, "wrong loaded value")
        for index, pair in enumerate(pairs):
            require(cache.get(*pair, lambda: 999) == index, "tenant/key cache collision")
    results.check("tenant and composite-key isolation", isolated_keys)

    def falsey_values():
        cache = module.TenantCache(10, clock=Clock())
        for index, value in enumerate([None, False, 0, "", [], {}]):
            calls = []
            def loader():
                calls.append(1)
                return value
            first = cache.get("t", str(index), loader)
            second = cache.get("t", str(index), loader)
            require(first is value and second is value, "cached object identity/value changed")
            require(len(calls) == 1, "falsey cache entry reloaded")
    results.check("falsey values are valid cache hits", falsey_values)

    def expiry():
        clock = Clock()
        cache = module.TenantCache(10, clock=clock)
        require(cache.get("t", "k", lambda: "first") == "first", "initial load failed")
        clock.value = 9.999
        require(cache.get("t", "k", lambda: "early") == "first", "expired too early")
        clock.value = 10
        require(cache.get("t", "k", lambda: "second") == "second", "exact expiry must reload")
        clock.value = 19.999
        require(cache.get("t", "k", lambda: "early") == "second", "refresh expiry wrong")
    results.check("expiry boundaries", expiry)

    def completion_time():
        clock = Clock()
        cache = module.TenantCache(5, clock=clock)
        def slow_loader():
            clock.value += 4
            return "loaded"
        cache.get("t", "k", slow_loader)
        clock.value = 8.999
        require(cache.get("t", "k", lambda: "too early") == "loaded", "TTL must begin after loading")
        clock.value = 9
        require(cache.get("t", "k", lambda: "fresh") == "fresh", "post-load expiry wrong")
    results.check("TTL starts when loader completes", completion_time)

    def failures_and_zero():
        clock = Clock()
        cache = module.TenantCache(5, clock=clock)
        def broken():
            raise LookupError("fixture failure")
        raises(LookupError, lambda: cache.get("t", "k", broken))
        require(cache.get("t", "k", lambda: "ok") == "ok", "failure cached")
        clock.value = 5
        raises(LookupError, lambda: cache.get("t", "k", broken))
        require(cache.get("t", "k", lambda: "retry") == "retry", "expired failure blocked retry")
        no_cache = module.TenantCache(0, clock=clock)
        require(no_cache.get("t", "k", lambda: 1) == 1, "zero TTL first load failed")
        require(no_cache.get("t", "k", lambda: 2) == 2, "zero TTL must always reload")
        raises(ValueError, lambda: module.TenantCache(-1, clock=clock))
    results.check("failure retry and TTL limits", failures_and_zero)


def check_report(module, results):
    def abstraction():
        raises(TypeError, module.ReportSink)
        class ExternalSink(module.ReportSink):
            def __init__(self):
                self.parts = []
            def write(self, text):
                require(isinstance(text, str), "sink receives text")
                self.parts.append(text)
        sink = ExternalSink()
        require(module.export_totals([{"category": "x", "amount_cents": 4}], sink) == 1, "wrong row count")
        require(list(csv.reader(io.StringIO("".join(sink.parts)))) ==
                [["category", "total_cents"], ["x", "4"]], "injected sink unused or wrong")
    results.check("external sink contract", abstraction)

    def csv_behavior():
        rows = [
            {"category": 'a,"b', "amount_cents": 3},
            {"category": "z", "amount_cents": -2},
            {"category": 'a,"b', "amount_cents": 7},
            {"category": "line\nbreak", "amount_cents": 0},
        ]
        before = copy.deepcopy(rows)
        sink = module.CsvBuffer()
        require(module.export_totals(rows, sink) == 3, "wrong distinct-category count")
        require(list(csv.reader(io.StringIO(sink.getvalue()))) == [
            ["category", "total_cents"], ['a,"b', "10"],
            ["line\nbreak", "0"], ["z", "-2"],
        ], "CSV sorting, totals, or quoting failed")
        require(rows == before, "input records changed")
        empty = module.CsvBuffer()
        require(module.export_totals([], empty) == 0, "empty report row count")
        require(list(csv.reader(io.StringIO(empty.getvalue()))) ==
                [["category", "total_cents"]], "empty report must retain header")
    results.check("CSV totals, escaping, emptiness and input preservation", csv_behavior)


def check_labels(module, results):
    examples = [
        ("Alpha\tBeta", "alpha-beta"),
        ("  ALPHA   BETA  ", "alpha-beta"),
        ("Ａlpha\u3000Beta", "alpha-beta"),
        ("Straße\u00a0Plan", "strasse-plan"),
        ("Cafe\u0301\nMenu", "café-menu"),
        ("already-key", "already-key"),
    ]
    def entrypoints():
        for label, expected in examples:
            require(module.normalize_key(label) == expected, f"normalizer failed for {label!r}")
            require(module.preview_key(label) == expected, f"preview failed for {label!r}")
            seen = {"keep-existing"}
            require(module.import_label(label, seen) == expected, f"import failed for {label!r}")
            require(seen == {"keep-existing", expected}, "import modified unrelated keys")
    results.check("all entrypoints and unseen normalization variants", entrypoints)

    def rejection():
        seen = {"alpha-beta", "keep-existing"}
        before = set(seen)
        raises(ValueError, lambda: module.import_label("  ALPHA\tBETA ", seen))
        require(seen == before, "duplicate import mutated seen")
        for label in ["", " \t\n", "\u3000\u00a0"]:
            raises(ValueError, lambda value=label: module.normalize_key(value))
            raises(ValueError, lambda value=label: module.preview_key(value))
            raises(ValueError, lambda value=label: module.import_label(value, seen))
        require(seen == before, "empty import mutated seen")
    results.check("duplicate and empty-label rejection", rejection)


def encoded(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def token_for(claims, secret):
    payload = encoded(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret, payload.encode("ascii"), hashlib.sha256).digest()
    return payload + "." + encoded(signature)


def check_notes(module, results):
    secret = b"fixture-only-secret"
    notes = {"n1": {"owner": "alice", "text": "hello"},
             "n2": {"owner": "bob", "text": "private"}}
    token = token_for({"sub": "alice", "exp": 120}, secret)

    def access():
        before = copy.deepcopy(notes)
        require(module.read_note(token, "n1", notes, secret, 100) == "hello", "valid access rejected")
        for note_id in ["n2", "absent"]:
            raises(module.AccessDenied, lambda key=note_id: module.read_note(token, key, notes, secret, 100))
        require(notes == before, "notes changed")
    results.check("valid access, ownership and missing-note behavior", access)

    def invalid_tokens():
        _, signature = token.split(".")
        forged = encoded(json.dumps({"sub": "bob", "exp": 999}).encode("utf-8")) + "." + signature
        bad_tokens = [
            forged,
            token_for({"sub": "alice", "exp": 100}, secret),
            token_for({"sub": "alice", "exp": 99}, secret),
            token_for({"sub": "alice", "exp": 120}, b"wrong-key"),
            "not-a-token",
            token_for({"sub": "", "exp": 120}, secret),
        ]
        for bad in bad_tokens:
            raises(module.AccessDenied, lambda value=bad: module.read_note(value, "n1", notes, secret, 100))
        raises(module.AccessDenied, lambda: module.read_note(forged, "n2", notes, secret, 100))
    results.check("signature, expiry, format and claims validation", invalid_tokens)

    def policy_boundary():
        original = module.verify_token
        calls = []
        def revoked(*args, **kwargs):
            calls.append(1)
            raise module.AccessDenied("fixture policy revoked this token")
        module.verify_token = revoked
        try:
            raises(module.AccessDenied, lambda: module.read_note(token, "n1", notes, secret, 100))
            require(bool(calls), "new entrypoint bypassed existing verification policy")
        finally:
            module.verify_token = original
    results.check("existing verifier remains authoritative", policy_boundary)


def check_jobs(module, results):
    async def active_jobs():
        events = []
        tasks = []
        ready = [asyncio.Event(), asyncio.Event()]
        class Resource:
            def __init__(self):
                self.calls = 0
            async def aclose(self):
                require(all(task.done() for task in tasks), "resource closed before tasks finished")
                require(all(f"clean-{i}" in events for i in range(2)), "resource closed before cleanup")
                self.calls += 1
                events.append("resource")
        resource = Resource()
        runner = module.JobRunner(resource)
        async def work(index):
            try:
                ready[index].set()
                await asyncio.Event().wait()
            finally:
                await asyncio.sleep(0)
                await asyncio.sleep(0)
                events.append(f"clean-{index}")
        tasks.extend(runner.start(work(i)) for i in range(2))
        require(all(isinstance(task, asyncio.Task) for task in tasks), "start must return tasks")
        await asyncio.wait_for(asyncio.gather(*(event.wait() for event in ready)), 1)
        await asyncio.wait_for(runner.close(), 1)
        require(events[-1] == "resource", "resource closure order wrong")
        require(all(task.cancelled() for task in tasks), "active work was not cancelled")
        await asyncio.wait_for(runner.close(), 1)
        require(resource.calls == 1, "resource closed more than once")
    results.check("cancel, await cleanup, then close resource once", lambda: asyncio.run(active_jobs()))

    async def completed_and_empty():
        class Resource:
            def __init__(self):
                self.calls = 0
            async def aclose(self):
                self.calls += 1
        for with_work in (False, True):
            resource = Resource()
            runner = module.JobRunner(resource)
            if with_work:
                async def done():
                    return 42
                task = runner.start(done())
                require(await task == 42, "completed task result changed")
                await asyncio.sleep(0)
            await asyncio.wait_for(runner.close(), 1)
            await asyncio.wait_for(runner.close(), 1)
            require(resource.calls == 1, "empty/completed shutdown closed resource wrong number of times")
            async def rejected():
                return "must not run"
            coroutine = rejected()
            try:
                raises(RuntimeError, lambda: runner.start(coroutine))
                raises(RuntimeError, lambda: coroutine.send(None))
            finally:
                coroutine.close()
    results.check("empty/completed shutdown and post-close admission", lambda: asyncio.run(completed_and_empty()))


def load_module(path, case_id):
    name = "_implementation_eval_" + case_id.replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "cannot load output module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=CASE_FILES)
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    results = Results()
    observations = {}
    try:
        directory = args.directory.resolve(strict=True)
        path = (directory / CASE_FILES[args.case]).resolve(strict=True)
        require(path.parent == directory, "output must remain inside evaluation directory")
        if path.suffix == ".html":
            document = Document(path.read_text(encoding="utf-8"))
            if args.case == "native-single-date":
                observations["native_date_input"] = bool(document.matching("input", name="appointment_date", type="date"))
            checker = check_native if args.case == "native-single-date" else check_range
            results.check("static HTML form and field contracts", lambda: checker(document))
        else:
            module = load_module(path, args.case)
            {
                "tenant-ttl-cache": check_cache,
                "injected-csv-interface": check_report,
                "shared-normalization": check_labels,
                "verified-note-access": check_notes,
                "async-clean-shutdown": check_jobs,
            }[args.case](module, results)
    except Exception as error:
        results.items.append({"name": "load and execute case", "passed": False,
                              "error": f"{type(error).__name__}: {error}"})
    needs_review = any(item.get("needs_review") for item in results.items)
    failed = any(item["passed"] is False for item in results.items)
    passed = bool(results.items) and all(item["passed"] for item in results.items)
    print(json.dumps({"case": args.case, "passed": passed, "checks": results.items,
                      "status": "failed" if failed else "needs_review" if needs_review else "passed",
                      "needs_review": needs_review,
                      "observations": observations,
                      "limitations": "Static HTML checks only; bounded Python behavior probes; no general quality or savings claim."},
                     ensure_ascii=False))
    return 1 if failed else 2 if needs_review else 0


if __name__ == "__main__":
    raise SystemExit(main())
