"""The main server monolith."""

from pathlib import Path
from tomllib import load as toml_load
from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api import api_v0
from objects import Base


with open(Path(__file__).parent / "config.toml", "rb") as config_file:
    CONFIG = SimpleNamespace(**toml_load(config_file))

app = FastAPI(openapi_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates("templates")

# ANCHOR - SQLAlchemy engine
engine = create_engine(CONFIG.database_uri, connect_args={"check_same_thread": False})
SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


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


app.mount("/api/v0", api_v0)

if __name__ == "__main__":
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    hypercorn_config = Config()
    hypercorn_config.bind = [f"{CONFIG.host}:{CONFIG.port}"]
    # hypercorn_config.quic_bind = [f"{CONFIG.host}:{CONFIG.port}"]
    asyncio.run(serve(app, hypercorn_config))  # type: ignore
