import json
import time
import uuid
from collections import deque
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

EMAIL = "22f3000320@ds.study.iitm.ac.in"   # <-- CHANGE THIS to your own email

app = FastAPI()
START_TIME = time.time()

# Allow anyone's browser/grader to call us
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# The "tally clicker"
REQUESTS = Counter("http_requests_total", "Total HTTP requests")

# The "notebook": remembers only the last 1000 entries
LOGS = deque(maxlen=1000)


# This runs for EVERY request, before and after your endpoint
@app.middleware("http")
async def track_requests(request: Request, call_next):
    REQUESTS.inc()                       # click the tally counter
    request_id = str(uuid.uuid4())       # unique ID for this request
    response = await call_next(request)  # run the actual endpoint

    entry = {
        "level": "INFO",
        "ts": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "request_id": request_id,
        "method": request.method,
        "status": response.status_code,
    }
    LOGS.append(entry)                   # write in the notebook
    print(json.dumps(entry), flush=True) # also print as JSON log line
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/work")
def work(n: int = 1):
    total = 0
    for i in range(n * 1000):   # pretend to do "n units" of work
        total += i
    return {"email": EMAIL, "done": n}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "uptime_s": float(time.time() - START_TIME)}


@app.get("/logs/tail")
def logs_tail(limit: int = 10):
    if limit <= 0:
        return []
    return list(LOGS)[-limit:]