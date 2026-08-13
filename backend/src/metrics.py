"""Day 8 call-metrics HTTP API + dashboard.

Serves live numbers from the Day 4 SQLite file. No transcripts, names,
phones, OTPs, PINs, or account numbers leave this process.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import db

logger = logging.getLogger("agent.metrics")

DEFAULT_HOST = os.getenv("METRICS_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("METRICS_PORT", "8082"))

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Jan Sahay — Call dashboard</title>
  <style>
    :root { color-scheme: dark; }
    * { box-sizing: border-box; }
    body {
      margin: 0; font-family: ui-sans-serif, system-ui, sans-serif;
      background: #07110d; color: #e8f5ef; min-height: 100vh;
    }
    main { max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }
    h1 { font-size: 1.6rem; margin: 0 0 4px; }
    .sub { color: #8aa89a; margin: 0 0 24px; font-size: .95rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }
    .card {
      background: #0f1f18; border: 1px solid #1d3a2d; border-radius: 14px; padding: 16px 18px;
    }
    .label { color: #8aa89a; font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; }
    .num { font-size: 2rem; font-weight: 650; margin-top: 6px; }
    .ok { color: #34d399; } .bad { color: #f87171; } .muted { color: #cbd5d1; }
    .row { display: flex; flex-wrap: wrap; gap: 10px; margin: 18px 0 10px; align-items: end; }
    select, button {
      background: #12261d; color: #e8f5ef; border: 1px solid #1d3a2d;
      border-radius: 10px; padding: 8px 12px;
    }
    table { width: 100%; border-collapse: collapse; font-size: .9rem; }
    th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid #1d3a2d; }
    th { color: #8aa89a; font-weight: 500; }
    .chip { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: .75rem; }
    .chip.ok { background: #0f3d2c; } .chip.bad { background: #3d1515; }
    .note { color: #6f8b7d; font-size: .8rem; margin-top: 18px; }
    a { color: #34d399; }
  </style>
</head>
<body>
  <main>
    <h1>Jan Sahay call dashboard</h1>
    <p class="sub">Live outcomes from browser and SIP calls. No caller secrets or transcripts.</p>
    <div class="row">
      <label>Channel
        <select id="channel">
          <option value="">all</option>
          <option value="browser">browser</option>
          <option value="sip">sip</option>
        </select>
      </label>
      <label>Since
        <select id="since">
          <option value="">all time</option>
          <option value="1">last 24 hours</option>
          <option value="7">last 7 days</option>
        </select>
      </label>
      <button id="refresh" type="button">Refresh</button>
    </div>
    <div class="grid">
      <div class="card"><div class="label">Total calls</div><div class="num" id="total">0</div></div>
      <div class="card"><div class="label">Successful</div><div class="num ok" id="ok">0</div></div>
      <div class="card"><div class="label">Failed</div><div class="num bad" id="fail">0</div></div>
      <div class="card"><div class="label">Success rate</div><div class="num muted" id="rate">0%</div></div>
    </div>
    <div class="grid" style="margin-top:12px">
      <div class="card"><div class="label">Eligibility checks</div><div class="num muted" id="elig">0</div></div>
      <div class="card"><div class="label">Document lists</div><div class="num muted" id="docs">0</div></div>
      <div class="card"><div class="label">Escalations</div><div class="num muted" id="esc">0</div></div>
      <div class="card"><div class="label">Avg first reply</div><div class="num muted" id="lat">—</div></div>
    </div>
    <h2 style="margin:28px 0 8px;font-size:1.05rem">Failure types</h2>
    <p id="fails" class="sub">None yet.</p>
    <h2 style="margin:28px 0 8px;font-size:1.05rem">Recent calls</h2>
    <table>
      <thead>
        <tr><th>When</th><th>Duration</th><th>Channel</th><th>Outcome</th><th>Result</th></tr>
      </thead>
      <tbody id="rows"></tbody>
    </table>
    <p class="note">
      Success = eligibility check completed or document list delivered.
      Dashboard never shows passwords, OTPs, PINs, account numbers, or transcripts.
      <a href="/">Back to voice agent</a>
    </p>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    function sinceIso(days) {
      if (!days) return "";
      const d = new Date(Date.now() - Number(days) * 86400000);
      return d.toISOString();
    }
    function fmtDur(sec) {
      if (sec == null) return "—";
      const s = Math.max(0, Math.round(sec));
      return s < 60 ? s + "s" : Math.floor(s / 60) + "m " + (s % 60) + "s";
    }
    function fmtWhen(iso) {
      if (!iso) return "—";
      const d = new Date(iso);
      return isNaN(d) ? "—" : d.toLocaleString();
    }
    async function load() {
      const q = new URLSearchParams();
      const ch = $("channel").value;
      const since = sinceIso($("since").value);
      if (ch) q.set("channel", ch);
      if (since) q.set("since", since);
      const res = await fetch("/api/metrics?" + q.toString(), { cache: "no-store" });
      if (!res.ok) throw new Error("metrics unavailable");
      const data = await res.json();
      $("total").textContent = data.total_calls;
      $("ok").textContent = data.successful_calls;
      $("fail").textContent = data.failed_calls;
      $("rate").textContent = (data.success_rate ?? 0) + "%";
      $("elig").textContent = data.eligibility_checks;
      $("docs").textContent = data.document_lists;
      $("esc").textContent = data.escalations;
      $("lat").textContent = data.avg_first_reply_latency_ms == null
        ? "—" : data.avg_first_reply_latency_ms + " ms";
      const types = data.failure_types || {};
      const keys = Object.keys(types);
      $("fails").textContent = keys.length
        ? keys.map((k) => k + ": " + types[k]).join(" · ")
        : "None yet.";
      $("rows").innerHTML = (data.recent_calls || []).map((c) => {
        const cls = c.outcome === "success" ? "ok" : "bad";
        const result = c.outcome === "success"
          ? (c.eligibility_completed ? "eligibility" : "") +
            (c.document_list_delivered ? (c.eligibility_completed ? " + docs" : "docs") : "")
          : (c.failure_type || "failed");
        return "<tr><td>" + fmtWhen(c.ended_at) + "</td><td>" + fmtDur(c.duration_seconds) +
          "</td><td>" + (c.channel || "") + "</td><td><span class='chip " + cls + "'>" +
          (c.outcome || "") + "</span></td><td>" + result +
          (c.scheme_codes && c.scheme_codes.length ? " · " + c.scheme_codes.join(", ") : "") +
          "</td></tr>";
      }).join("") || "<tr><td colspan='5'>No closed calls yet.</td></tr>";
    }
    $("refresh").onclick = () => load().catch((err) => alert(err.message));
    $("channel").onchange = () => load().catch(() => {});
    $("since").onchange = () => load().catch(() => {});
    load().catch((err) => { $("fails").textContent = err.message; });
    setInterval(() => load().catch(() => {}), 4000);
  </script>
</body>
</html>
"""


class MetricsHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        logger.info("%s - %s", self.address_string(), fmt % args)

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/api/calls/clear":
            try:
                db.clear_call_outcomes()
                self._send(
                    200,
                    b'{"status":"success","message":"Call outcomes cleared"}',
                    "application/json; charset=utf-8",
                )
            except Exception:
                logger.exception("clear call outcomes failed")
                self._send(500, b'{"error":"clear_failed"}', "application/json")
            return

        if path == "/api/manager/approve":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
                import manager

                req_id = body.get("request_id")
                notes = body.get("notes")
                if not req_id:
                    self._send(400, b'{"error":"request_id_required"}', "application/json")
                    return
                res = manager.approve_manager_request(req_id, resolution_notes=notes)
                self._send(
                    200,
                    json.dumps(res).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            except Exception:
                logger.exception("manager approve failed")
                self._send(500, b'{"error":"approve_failed"}', "application/json")
            return

        if path == "/api/manager/reject":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
                import manager

                req_id = body.get("request_id")
                notes = body.get("notes")
                if not req_id:
                    self._send(400, b'{"error":"request_id_required"}', "application/json")
                    return
                res = manager.reject_manager_request(req_id, resolution_notes=notes)
                self._send(
                    200,
                    json.dumps(res).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            except Exception:
                logger.exception("manager reject failed")
                self._send(500, b'{"error":"reject_failed"}', "application/json")
            return

        if path == "/api/threats/ban":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
                import threat_engine

                action = body.get("action", "ban")
                fingerprint = body.get("fingerprint")
                if not fingerprint:
                    self._send(400, b'{"error":"fingerprint_required"}', "application/json")
                    return
                if action == "unban":
                    res = threat_engine.unban_session(fingerprint)
                else:
                    res = threat_engine.ban_session_manual(
                        fingerprint,
                        reason=body.get("reason", "Manual ban via dashboard"),
                        permanent=bool(body.get("permanent", False)),
                    )
                self._send(
                    200,
                    json.dumps(res).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            except Exception:
                logger.exception("ban management action failed")
                self._send(500, b'{"error":"ban_action_failed"}', "application/json")
            return

        if path not in {"/api/calls", "/api/metrics"}:
            self._send(404, b'{"error":"not_found"}', "application/json")
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            body = {}
        event = str(body.get("event") or "")
        channel = body.get("channel") if body.get("channel") in ("browser", "sip") else "browser"
        if event != "cancelled_before_connect":
            self._send(400, b'{"error":"unsupported_event"}', "application/json")
            return
        try:
            payload = db.record_cancelled_call(
                room_id=body.get("room_id"),
                channel=channel,
            )
        except Exception:
            logger.exception("cancel record failed")
            self._send(500, b'{"error":"metrics_unavailable"}', "application/json")
            return
        self._send(
            200,
            json.dumps(payload).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        channel = (query.get("channel") or [None])[0] or None
        since = (query.get("since") or [None])[0] or None
        if channel not in (None, "browser", "sip"):
            channel = None

        if path in {"/", "/dashboard"}:
            self._send(200, _DASHBOARD_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path in {"/api/manager", "/api/manager/requests"}:
            try:
                import manager

                status = (query.get("status") or [None])[0]
                rtype = (query.get("type") or [None])[0]
                payload = manager.list_manager_requests(status=status, request_type=rtype)
                self._send(
                    200,
                    json.dumps(payload).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            except Exception:
                logger.exception("manager query failed")
                self._send(
                    500,
                    json.dumps({"error": "manager_unavailable"}).encode(),
                    "application/json",
                )
            return
        if path in {"/api/security", "/api/threats"}:
            try:
                import threat_engine

                payload = threat_engine.get_security_dashboard_payload(since=since)
                self._send(
                    200,
                    json.dumps(payload).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            except Exception:
                logger.exception("security query failed")
                self._send(
                    500,
                    json.dumps({"error": "security_unavailable"}).encode(),
                    "application/json",
                )
            return
        if path == "/api/escalations":
            try:
                import escalation
                payload = escalation.list_escalations()
                self._send(
                    200,
                    json.dumps(payload).encode("utf-8"),
                    "application/json; charset=utf-8",
                )
            except Exception:
                logger.exception("escalations query failed")
                self._send(
                    500,
                    json.dumps({"error": "metrics_unavailable"}).encode(),
                    "application/json",
                )
            return
        if path in {"/api/metrics", "/api/stats", "/api/calls"}:
            try:
                payload = db.get_dashboard_payload(channel=channel, since=since)
            except Exception:
                logger.exception("metrics query failed")
                self._send(
                    500,
                    json.dumps({"error": "metrics_unavailable"}).encode(),
                    "application/json",
                )
                return
            self._send(
                200,
                json.dumps(payload).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        self._send(404, b'{"error":"not_found"}', "application/json")


def serve_metrics(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    db.init_db()
    httpd = ThreadingHTTPServer((host, port), MetricsHandler)
    logger.info("Call dashboard on http://%s:%s/dashboard", host, port)
    httpd.serve_forever()


def start_metrics_server_thread(
    host: str = DEFAULT_HOST, port: int = DEFAULT_PORT
) -> threading.Thread | None:
    """Start once per process. Bind errors are ignored (already running)."""
    try:
        httpd = ThreadingHTTPServer((host, port), MetricsHandler)
    except OSError as err:
        logger.info("Metrics server not started on %s:%s (%s)", host, port, err)
        return None
    thread = threading.Thread(target=httpd.serve_forever, name="call-metrics", daemon=True)
    thread.start()
    logger.info("Call dashboard on http://%s:%s/dashboard", host, port)
    return thread


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve_metrics()
