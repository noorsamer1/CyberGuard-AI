"""Tests validating range_target.py log emission."""

from __future__ import annotations

import json
import os
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

import range_target


class RangeTargetLogTests(unittest.TestCase):
    """Fire range requests and validate emitted log fields."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._prev_secret = os.environ.get("RANGE_SHARED_SECRET")
        os.environ["RANGE_SHARED_SECRET"] = "test-secret"
        range_target.SECRET = "test-secret"
        range_target._reset_state()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), range_target.RangeHandler)
        cls.port = cls.server.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        if cls._prev_secret is None:
            os.environ.pop("RANGE_SHARED_SECRET", None)
        else:
            os.environ["RANGE_SHARED_SECRET"] = cls._prev_secret

    def setUp(self) -> None:
        range_target._reset_state()

    def _post_json(self, path: str, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)

    def _drain_logs(self) -> list[dict]:
        req = urllib.request.Request(
            f"{self.base}/_range/logs",
            headers={"X-Range-Secret": "test-secret"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("logs", [])

    def test_exec_benign_does_not_tag_attack(self) -> None:
        self._post_json("/exec", {"input": "report.csv"})
        logs = self._drain_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["event_type"], "web")
        self.assertNotIn("attack", logs[0].get("metadata", {}))

    def test_exec_malicious_tags_command_injection(self) -> None:
        self._post_json("/exec", {"input": "report.csv; whoami"})
        logs = self._drain_logs()
        self.assertEqual(logs[0]["event_type"], "web_attack")
        self.assertEqual(logs[0]["metadata"].get("attack"), "command_injection")

    def test_dns_benign_does_not_tag_attack(self) -> None:
        self._post_json("/dns/query", {"query": "healthcheck.local"})
        logs = self._drain_logs()
        self.assertEqual(logs[0]["severity"], "low")
        self.assertNotIn("attack", logs[0].get("metadata", {}))

    def test_dns_suspicious_tags_tunneling(self) -> None:
        query = "c2VjcmV0LXNlZ21lbnQtMDE=.corp.lab.local"
        self._post_json("/dns/query", {"query": query})
        logs = self._drain_logs()
        self.assertEqual(logs[0]["metadata"].get("attack"), "dns_tunneling")
        self.assertIn("Suspicious DNS", logs[0]["message"])
