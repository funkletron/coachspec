from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coachspec.adapters import MockProviderAdapter
from coachspec.persistence import JsonSessionStorage, SessionExporter, SessionPersistenceError
from coachspec.runtime import CoachSession
from coachspec.schema import CoachSpec, load_coachspec


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_DATA_DIR = Path(__file__).resolve().parent / ".local"


class WebDemo:
    def __init__(
        self,
        root: Path = ROOT,
        sessions_dir: Path = DEFAULT_DATA_DIR / "sessions",
        exports_dir: Path = DEFAULT_DATA_DIR / "exports",
    ) -> None:
        self.root = root
        self.coaches_dir = root / "coaches"
        self.sessions_dir = sessions_dir
        self.exports_dir = exports_dir
        self.storage = JsonSessionStorage()
        self.sessions: dict[str, CoachSession] = {}

    def list_coaches(self) -> list[dict[str, object]]:
        coaches: list[dict[str, object]] = []
        for path in sorted(self.coaches_dir.glob("**/*.yaml")):
            spec = load_coachspec(path)
            coaches.append(self._coach_payload(spec, path))
        return coaches

    def start_session(self, coach_id: str) -> dict[str, object]:
        spec, path = self._load_coach_by_id(coach_id)
        session = CoachSession.from_spec(
            spec,
            provider_adapter=MockProviderAdapter(),
        )
        self.sessions[session.state.session_id] = session
        session_path = self._persist_session(session)
        return self._session_payload(session, coach_path=path, session_path=session_path)

    def get_session(self, session_id: str) -> dict[str, object]:
        session = self._get_session(session_id)
        return self._session_payload(session, session_path=self._session_path(session_id))

    def send_message(self, session_id: str, message: str) -> dict[str, object]:
        if not message.strip():
            raise DemoError(HTTPStatus.BAD_REQUEST, "Message cannot be empty.")
        session = self._get_session(session_id)
        response = session.respond_stub(message.strip())
        session_path = self._persist_session(session)
        payload = self._session_payload(session, session_path=session_path)
        payload["response"] = response
        return payload

    def export_session(self, session_id: str) -> dict[str, object]:
        session = self._get_session(session_id)
        result = SessionExporter().export(session, self.exports_dir / session_id)
        return {
            "session_id": session_id,
            "directory": str(result.directory),
            "transcript_path": str(result.transcript_path),
            "events_path": str(result.events_path),
            "metadata_path": str(result.metadata_path),
        }

    def _load_coach_by_id(self, coach_id: str) -> tuple[CoachSpec, Path]:
        for path in sorted(self.coaches_dir.glob("**/*.yaml")):
            spec = load_coachspec(path)
            if spec.coach.id == coach_id:
                return spec, path
        raise DemoError(HTTPStatus.NOT_FOUND, f"Unknown coach: {coach_id}")

    def _get_session(self, session_id: str) -> CoachSession:
        if session_id in self.sessions:
            return self.sessions[session_id]

        path = self._session_path(session_id)
        if not path.exists():
            raise DemoError(HTTPStatus.NOT_FOUND, f"Unknown session: {session_id}")
        try:
            session = self.storage.load(path)
        except SessionPersistenceError as exc:
            raise DemoError(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc)) from exc
        session.provider_adapter = MockProviderAdapter()
        self.sessions[session_id] = session
        return session

    def _persist_session(self, session: CoachSession) -> Path:
        return self.storage.save(session, self._session_path(session.state.session_id))

    def _session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def _coach_payload(self, spec: CoachSpec, path: Path) -> dict[str, object]:
        return {
            "id": spec.coach.id,
            "name": spec.coach.name,
            "summary": spec.purpose.summary,
            "description": spec.coach.description,
            "domain": spec.coach.domain,
            "memory_mode": spec.memory.mode,
            "path": str(path.relative_to(self.root)),
        }

    def _session_payload(
        self,
        session: CoachSession,
        coach_path: Path | None = None,
        session_path: Path | None = None,
    ) -> dict[str, object]:
        snapshot = session.memory.snapshot()
        return {
            "session_id": session.state.session_id,
            "coach": self._coach_payload(
                session.spec,
                coach_path or self.root / "coaches" / f"{session.state.coach_id}.yaml",
            ),
            "status": {
                "active": session.state.is_active,
                "turn_count": session.state.turn_count,
                "message_count": snapshot.message_count,
                "memory_mode": session.spec.memory.mode,
                "retention": session.spec.memory.retention,
                "session_path": str(session_path or self._session_path(session.state.session_id)),
            },
            "transcript": [
                {
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                }
                for message in snapshot.messages
            ],
        }


class DemoError(Exception):
    def __init__(self, status: HTTPStatus, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def make_handler(demo: WebDemo) -> type[BaseHTTPRequestHandler]:
    class DemoHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/":
                    self._send_html(INDEX_HTML)
                elif parsed.path == "/api/coaches":
                    self._send_json({"coaches": demo.list_coaches()})
                elif parsed.path == "/api/session":
                    session_id = parse_qs(parsed.query).get("id", [""])[0]
                    self._send_json(demo.get_session(session_id))
                else:
                    self._send_error(HTTPStatus.NOT_FOUND, "Not found.")
            except DemoError as exc:
                self._send_error(exc.status, exc.message)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                data = self._read_json()
                if parsed.path == "/api/sessions":
                    self._send_json(demo.start_session(str(data.get("coach_id", ""))))
                elif parsed.path == "/api/messages":
                    self._send_json(
                        demo.send_message(
                            str(data.get("session_id", "")),
                            str(data.get("message", "")),
                        )
                    )
                elif parsed.path == "/api/export":
                    self._send_json(demo.export_session(str(data.get("session_id", ""))))
                else:
                    self._send_error(HTTPStatus.NOT_FOUND, "Not found.")
            except DemoError as exc:
                self._send_error(exc.status, exc.message)
            except json.JSONDecodeError:
                self._send_error(HTTPStatus.BAD_REQUEST, "Request body must be JSON.")

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_json(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise DemoError(HTTPStatus.BAD_REQUEST, "Request body must be a JSON object.")
            return data

        def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_error(self, status: HTTPStatus, message: str) -> None:
            self._send_json({"error": message}, status=status)

    return DemoHandler


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CoachSpec Web Demo</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    body { margin: 0; background: #f7f8fb; color: #17202a; }
    main { max-width: 1120px; margin: 0 auto; padding: 28px; display: grid; gap: 18px; }
    header { display: flex; justify-content: space-between; gap: 18px; align-items: end; }
    h1, h2, p { margin: 0; }
    h1 { font-size: 28px; }
    h2 { font-size: 16px; }
    button, select, input { font: inherit; }
    button { border: 0; background: #214e8a; color: white; border-radius: 6px; padding: 10px 14px; cursor: pointer; }
    button.secondary { background: #425466; }
    button:disabled { background: #9aa8b6; cursor: not-allowed; }
    select, input { border: 1px solid #cad2dc; border-radius: 6px; padding: 10px; background: white; min-width: 0; }
    section { background: white; border: 1px solid #dde3eb; border-radius: 8px; padding: 16px; }
    .grid { display: grid; grid-template-columns: 340px 1fr; gap: 18px; align-items: start; }
    .stack { display: grid; gap: 12px; }
    .muted { color: #5d6b7a; }
    .coach-summary { min-height: 96px; line-height: 1.45; }
    .status { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; font-size: 14px; }
    .status div { background: #f3f6f9; border-radius: 6px; padding: 8px; overflow-wrap: anywhere; }
    .transcript { height: 420px; overflow: auto; border: 1px solid #e3e8ef; border-radius: 8px; padding: 12px; background: #fbfcfe; display: flex; flex-direction: column; gap: 10px; }
    .message { max-width: 82%; padding: 10px 12px; border-radius: 8px; line-height: 1.4; white-space: pre-wrap; overflow-wrap: anywhere; }
    .user { align-self: flex-end; background: #dcecff; }
    .assistant { align-self: flex-start; background: #edf2f7; }
    form { display: grid; grid-template-columns: 1fr auto; gap: 10px; }
    .export-path { font-size: 13px; overflow-wrap: anywhere; }
    @media (max-width: 820px) {
      main { padding: 16px; }
      header, .grid { display: grid; grid-template-columns: 1fr; }
      .status { grid-template-columns: 1fr; }
      .transcript { height: 340px; }
      .message { max-width: 94%; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div class="stack">
        <h1>CoachSpec Web Demo</h1>
        <p class="muted">A local host application using CoachSpec runtime sessions and the mock provider.</p>
      </div>
      <button id="export" class="secondary" disabled>Export Transcript</button>
    </header>
    <div class="grid">
      <section class="stack">
        <h2>Available Coaches</h2>
        <select id="coaches"></select>
        <button id="start">Start Session</button>
        <div class="coach-summary" id="summary"></div>
      </section>
      <section class="stack">
        <h2 id="coachName">No coach selected</h2>
        <div class="status" id="status"></div>
        <div class="transcript" id="transcript"></div>
        <form id="chat">
          <input id="message" autocomplete="off" placeholder="Send a message" disabled>
          <button id="send" disabled>Send</button>
        </form>
        <p class="export-path muted" id="exportPath"></p>
      </section>
    </div>
  </main>
  <script>
    const coachesEl = document.querySelector("#coaches");
    const summaryEl = document.querySelector("#summary");
    const startEl = document.querySelector("#start");
    const chatEl = document.querySelector("#chat");
    const messageEl = document.querySelector("#message");
    const sendEl = document.querySelector("#send");
    const exportEl = document.querySelector("#export");
    const exportPathEl = document.querySelector("#exportPath");
    const coachNameEl = document.querySelector("#coachName");
    const statusEl = document.querySelector("#status");
    const transcriptEl = document.querySelector("#transcript");
    let coaches = [];
    let session = null;

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Request failed");
      return payload;
    }

    function renderCoachSummary() {
      const coach = coaches.find(item => item.id === coachesEl.value);
      summaryEl.innerHTML = coach
        ? `<strong>${coach.name}</strong><p class="muted">${coach.summary}</p>`
        : "";
    }

    function renderSession(payload) {
      session = payload;
      coachNameEl.textContent = payload.coach.name;
      messageEl.disabled = false;
      sendEl.disabled = false;
      exportEl.disabled = false;
      statusEl.innerHTML = `
        <div>Session: ${payload.session_id}</div>
        <div>Turns: ${payload.status.turn_count}</div>
        <div>Messages: ${payload.status.message_count}</div>
        <div>Memory: ${payload.status.memory_mode}</div>
        <div>Retention: ${payload.status.retention || "not specified"}</div>
        <div>Saved: ${payload.status.session_path}</div>
      `;
      transcriptEl.innerHTML = "";
      for (const message of payload.transcript) {
        const item = document.createElement("div");
        item.className = `message ${message.role}`;
        item.textContent = `${message.role}: ${message.content}`;
        transcriptEl.appendChild(item);
      }
      transcriptEl.scrollTop = transcriptEl.scrollHeight;
    }

    async function loadCoaches() {
      const payload = await api("/api/coaches");
      coaches = payload.coaches;
      coachesEl.innerHTML = coaches.map(coach => `<option value="${coach.id}">${coach.name}</option>`).join("");
      coachesEl.value = coaches.find(coach => coach.id === "bible-deep-dive")?.id || coaches[0]?.id || "";
      renderCoachSummary();
    }

    coachesEl.addEventListener("change", renderCoachSummary);
    startEl.addEventListener("click", async () => {
      exportPathEl.textContent = "";
      renderSession(await api("/api/sessions", {
        method: "POST",
        body: JSON.stringify({ coach_id: coachesEl.value })
      }));
    });
    chatEl.addEventListener("submit", async event => {
      event.preventDefault();
      if (!session || !messageEl.value.trim()) return;
      const message = messageEl.value;
      messageEl.value = "";
      renderSession(await api("/api/messages", {
        method: "POST",
        body: JSON.stringify({ session_id: session.session_id, message })
      }));
    });
    exportEl.addEventListener("click", async () => {
      if (!session) return;
      const payload = await api("/api/export", {
        method: "POST",
        body: JSON.stringify({ session_id: session.session_id })
      });
      exportPathEl.textContent = `Exported transcript: ${payload.transcript_path}`;
    });
    loadCoaches();
  </script>
</body>
</html>
"""


def run_server(host: str, port: int, open_browser: bool) -> None:
    demo = WebDemo()
    server = ThreadingHTTPServer((host, port), make_handler(demo))
    url = f"http://{host}:{server.server_port}"
    print(f"CoachSpec web demo running at {url}")
    print("Using local mock provider; press Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local CoachSpec web demo.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    run_server(args.host, args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
