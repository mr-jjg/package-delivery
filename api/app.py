# /srv/projects/package-delivery/api/app.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pathlib import Path
from pydantic import BaseModel, Field
import asyncio, contextlib, json, os, subprocess, sys, contextlib, time, uuid

PROJECT_DIR = Path(__file__).resolve().parents[1]
TMP_DIR = PROJECT_DIR / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)
GEN_TTL_SECONDS = 30*60 # 30 minutes
GEN_SCRIPT = PROJECT_DIR / "tools" / "package_data_generator.py"

app = FastAPI(title="Package Delivery API", root_path="/wgups")

ALLOWED_CMDS = {
    "enter": "\n",
}

def cleanup_old_generated_lists() -> None:
    cutoff = time.time() - GEN_TTL_SECONDS
    for p in TMP_DIR.glob("*.csv"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
        except Exception:
            pass

class GenReq(BaseModel):
    num_pkgs: int = Field(20, ge=20, le=40)
    constraints: int = Field(20, ge=0, le=100)
    deadlines: int = Field(20, ge=0, le=100)

@app.post("/generate")
async def generate(req: GenReq):
    cleanup_old_generated_lists()

    list_id = str(uuid.uuid4())
    out_path = TMP_DIR / f"{list_id}.csv"

    cmd = [
        sys.executable,
        str(GEN_SCRIPT),
        "-o", str(out_path),
        "-n", str(req.num_pkgs),
        "-c", str(req.constraints),
        "-d", str(req.deadlines),
    ]

    subprocess.run(cmd, cwd=str(PROJECT_DIR), check=True)

    csv_text = out_path.read_text(encoding="utf-8")

    out_path = TMP_DIR / f"{list_id}.csv"
    out_path.write_text(csv_text, encoding="utf-8")

    return {
        "ok": True,
        "list_id": list_id,
        "csv": csv_text,
        "echo": req.model_dump(),
    }

@app.websocket("/ws")
async def ws_run(ws: WebSocket):
    """WebSocket: launch main.py, stream stdout to client, accept safe commands."""
    await ws.accept()

    v = ws.query_params.get("v")
    list_id = ws.query_params.get("list_id")
    package_csv = None

    if list_id:
        try:
            uuid.UUID(list_id)
            candidate = TMP_DIR / f"{list_id}.csv"
            if candidate.exists():
                package_csv = str(candidate)
        except Exception:
            package_csv = None

    cmd = [sys.executable, "-u", "main.py", "-v", v]
    if package_csv:
        cmd += ["-p", package_csv]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(PROJECT_DIR),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )

    async def pump_stdout():
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                await ws.send_text(line.decode(errors="ignore").rstrip("\n"))
        except Exception:
            pass

    pump_task = asyncio.create_task(pump_stdout())

    try:
        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)
            except Exception:
                continue
            cmd = (data.get("cmd") or "").lower()
            if cmd in ALLOWED_CMDS and proc.stdin and not proc.stdin.is_closing():
                proc.stdin.write(ALLOWED_CMDS[cmd].encode())
                await proc.stdin.drain()
    except WebSocketDisconnect:
        pass
    finally:
        pump_task.cancel()
        with contextlib.suppress(Exception):
            if proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2)
                except asyncio.TimeoutError:
                    proc.kill()
        with contextlib.suppress(Exception):
            await ws.close()
