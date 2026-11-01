import json, re, shutil, subprocess, sys, time
from pathlib import Path
import urllib.request

APP = Path(r"D:\IL\RAG\rag-app")
PDF = APP / "data" / "rag_intro.pdf"
OUT = Path(r"hasil_eksperimen/results.json")
PY = str(APP / "venv" / "Scripts" / "python.exe")
URL = "http://127.0.0.1:8765"

QUESTIONS = [
    "Apa fungsi chunk overlap dan mengapa penting?",
    "Berapa dimensi vektor model paraphrase-multilingual-MiniLM-L12-v2 dan berapa batas maksimum token inputnya?",
]
BASE = dict(temperature=0.2, top_k=4, chunk_size=100, chunk_overlap=20)

RUNS = (
    [("exp1_temperature", dict(BASE, temperature=t), 2) for t in (0.0, 0.2, 0.8)]
    + [("exp2_top_k", dict(BASE, top_k=k), 1) for k in (1, 4, 8)]
    + [("exp3_chunk_size", dict(BASE, chunk_size=s), 1) for s in (50, 100, 120)]
    + [("exp4_chunk_overlap", dict(BASE, chunk_overlap=o), 1) for o in (0, 20, 40)]
)


def set_config(cfg):
    p = APP / "config.py"
    s = p.read_text()
    s = re.sub(r"^TOP_K = \d+", f"TOP_K = {cfg['top_k']}", s, flags=re.M)
    s = re.sub(r"^CHUNK_SIZE = \d+", f"CHUNK_SIZE = {cfg['chunk_size']}", s, flags=re.M)
    s = re.sub(r"^CHUNK_OVERLAP = \d+", f"CHUNK_OVERLAP = {cfg['chunk_overlap']}", s, flags=re.M)
    p.write_text(s)
    p = APP / "llm.py"
    s = p.read_text()
    s = re.sub(r"temperature=[\d.]+", f"temperature={cfg['temperature']}", s)
    p.write_text(s)


def post_json(path, payload):
    req = urllib.request.Request(URL + path, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))


def ingest():
    b = "----b"
    data = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{PDF.name}\"\r\n"
            f"Content-Type: application/pdf\r\n\r\n").encode() + PDF.read_bytes() + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(URL + "/ingest", data, {"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(req, timeout=300))


def run(name, cfg, repeats):
    shutil.rmtree(APP / "qdrant_data", ignore_errors=True)
    set_config(cfg)
    log = open(APP.parent / "server.log", "a")
    proc = subprocess.Popen([PY, "-m", "uvicorn", "main:app", "--port", "8765"], cwd=APP, stdout=log, stderr=log)
    try:
        for _ in range(180):
            try:
                urllib.request.urlopen(URL + "/health", timeout=2)
                break
            except Exception:
                time.sleep(2)
        else:
            raise RuntimeError("server did not start")
        ing = ingest()
        answers = []
        for q in QUESTIONS:
            for r in range(repeats):
                answers.append(dict(question=q, run=r + 1, **post_json("/ask", {"question": q})))
        return dict(experiment=name, config=cfg, ingest=ing, answers=answers)
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        log.close()
        time.sleep(2)


results = []
for name, cfg, rep in RUNS:
    print("RUN", name, cfg, flush=True)
    results.append(run(name, cfg, rep))
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
set_config(BASE)
shutil.rmtree(APP / "qdrant_data", ignore_errors=True)
print("DONE", flush=True)
