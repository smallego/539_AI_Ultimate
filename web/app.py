from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.cache import record_api_metric
from web.logger import log_event, new_request_id
from web.routes import router

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

app = FastAPI(title="539 AI Ultimate V7")
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
app.include_router(router)


@app.middleware("http")
async def api_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or new_request_id()
    request.state.request_id = request_id
    start = perf_counter()
    success = False
    status_code = 500
    exception_logged = False

    try:
        response = await call_next(request)
        status_code = response.status_code
        success = status_code < 500
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        duration_ms = (perf_counter() - start) * 1000
        if request.url.path.startswith("/api"):
            record_api_metric(request.url.path, request.method, duration_ms, False, request_id)
            exception_logged = True
            log_event(
                "api.request",
                "EXCEPTION",
                request_id=request_id,
                duration_ms=round(duration_ms, 2),
                success=False,
                exception=exc,
                path=request.url.path,
                method=request.method,
            )
        raise
    finally:
        duration_ms = (perf_counter() - start) * 1000
        if request.url.path.startswith("/api") and not exception_logged:
            record_api_metric(request.url.path, request.method, duration_ms, success, request_id)
            log_event(
                "api.request",
                "SUCCESS" if success else "FAILED",
                request_id=request_id,
                duration_ms=round(duration_ms, 2),
                success=success,
                path=request.url.path,
                method=request.method,
                status_code=status_code,
            )


def main():
    import uvicorn

    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
