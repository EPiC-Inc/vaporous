"""The main server monolith."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import auth
from api import api_v0
from database import engine
from config import CONFIG

app = FastAPI(openapi_url=None)
templates = Jinja2Templates(Path(__file__).parent / "templates")

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/.well-known", StaticFiles(directory=Path(__file__).parent / ".well-known"), name=".well-known")


@app.get("/")
async def root(request: Request):
    if session_id := request.cookies.get("session_id"):
        return str(session_id)
    return RedirectResponse(url=request.url_for("login_page"))


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.post("/login")
async def login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"messages": [("error", "Not implemented yet :V")]},
    )
    # response.setcookie(key="session", value="test", secure=True)
    # return RedirectResponse(url=request.url_for("root"))


@app.post("/login/passkey")
async def login_passkey(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"messages": [("error", "Not implemented yet :V")]},
    )
    # response.setcookie(key="session", value="test", secure=True)
    # return RedirectResponse(url=request.url_for("root"))


@app.get("/login/passkey/challenge")
async def passkey_challenge():
    return Response(content=auth.passkey_challenge())


@app.get("/robots.txt")
async def robots_txt():
    return FileResponse(Path(__file__).parent / "static/robots.txt")


@app.get("/favicon.ico")
async def favicon():
    return


@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    return templates.TemplateResponse(request=request, name="privacy-policy.html")


@app.get("/vulnerability-disclosure-policy", response_class=HTMLResponse)
async def security_policy(request: Request):
    return templates.TemplateResponse(request=request, name="security-policy.html")


app.mount("/api/v0", api_v0)

if __name__ == "__main__":
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    hypercorn_config = Config()
    hypercorn_config.bind = [f"{CONFIG.host}:{CONFIG.port}"]
    # hypercorn_config.quic_bind = [f"{CONFIG.host}:{CONFIG.port}"]
    asyncio.run(serve(app, hypercorn_config))  # type: ignore
