"""The main server monolith."""

from os import PathLike
from pathlib import Path
from typing import Annotated, Optional
from urllib.parse import urlparse

from fastapi import Body, Cookie, HTTPException, FastAPI, Request, Security, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import auth
import file_handler
from api import api_v0
from config import CONFIG

# from database import SessionMaker

app = FastAPI(openapi_url=None)
templates = Jinja2Templates(Path(__file__).parent / "templates")

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/.well-known", StaticFiles(directory=Path(__file__).parent / ".well-known"), name=".well-known")


async def get_session(session_id: Annotated[Optional[str], Cookie()] = None) -> auth.Session | None:
    if session_id and (session := auth.check_session(session_id)):
        return session
    return None


async def get_file_response(request: Request, base: PathLike[str] | str, file_path: Optional[PathLike[str] | str], current_directory_url: str):
    files = file_handler.list_files(base=base, subfolder=file_path)
    if files is None:
        if file_contents := file_handler.get_file(base=base, file_path=file_path):
            return file_contents
        raise HTTPException(status_code=404, detail="Unable to get files")
    return templates.TemplateResponse(
        request=request, name="file_view.html", context={"files": files, "current_directory_url": current_directory_url}
    )


@app.exception_handler(404)
async def not_found(request: Request, exception: HTTPException):
    return templates.TemplateResponse(request=request, name="404.html")


@app.get("/")
async def root(request: Request, session: Annotated[Optional[auth.Session], Security(get_session)]):
    if session is None:
        return RedirectResponse(url=request.url_for("login_page"))
    return RedirectResponse(url=request.url_for("get_files"))


@app.get("/f")
@app.get("/f/{file_path:path}")
async def get_files(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    file_path: Optional[PathLike[str]] = None,
):
    if session is None:
        return RedirectResponse(url=request.url_for("login_page").include_query_params(next=request.url.path))
    return await get_file_response(
        request=request, base=session.user_id, file_path=file_path, current_directory_url=request.url_for("get_files")
    )


@app.get("/public")
@app.get("/public/{file_path:path}")
async def get_public_files(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    file_path: Optional[PathLike[str]] = None,
):
    if not CONFIG.get("public_directory"):
        raise HTTPException(status_code=404, detail="Public directory not enabled.")
    if session is None:
        if CONFIG.get("public_access_requires_login"):
            return RedirectResponse(url=request.url_for("login_page").include_query_params(next=request.url.path))
    return await get_file_response(
        request=request,
        base=str(CONFIG.get("public_directory")),
        file_path=file_path,
        current_directory_url=request.url_for("get_public_files"),
    )


@app.post("/compose")
async def compose_file_view(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    file_path: Annotated[PathLike[str], Body()],
    public: Annotated[bool, Body()],
):
    if session is None:
        return RedirectResponse(url=request.url_for("login_page").include_query_params(next=request.url.path))
    if public:
        base = CONFIG.get("public_directory")
    else:
        base = session.user_id
    files = file_handler.list_files(base=str(base), subfolder=file_path)
    if files is None:
        raise HTTPException(status_code=404, detail="Unable to get files")
    return templates.TemplateResponse(
        request=request,
        name="compose_file_list.html",
        context={
            "files": files,
            "current_directory_url": file_path,
            "public_directory_url": request.url_for("get_public_files"),
        },
    )


@app.get("/login")
async def login_page(request: Request, next: Optional[str] = None, messages: Optional[list] = None):
    if messages is None:
        messages = []
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"messages": messages, "next": next, "banner": CONFIG.get("banner")},
    )


@app.post("/login")
async def login(request: Request, form: Annotated[OAuth2PasswordRequestForm, Security()], next: Optional[str] = None):
    username = form.username
    password = form.password
    success = auth.login_with_password(username, password)
    if success:
        # Get rid of any unexpected redirects
        if next:
            next = urlparse(next).path
        # The above branch breaks everything if next was maliciously set, so let's properly unbreak it
        if not next:
            next = request.url_for("root")
        response = RedirectResponse(url=next, status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="session_id",
            value=auth.new_session(username),
            secure=True,
            max_age=int(auth.SESSION_EXPIRY.total_seconds()),
        )
        return response
    return await login_page(request=request, next=next, messages=[("error", "Username or password is incorrect")])


@app.post("/login/passkey")
async def login_passkey(request: Request, next: Optional[str] = None):
    # response = RedirectResponse(url=request.url_for("root"), status_code=status.HTTP_303_SEE_OTHER)
    # response.set_cookie(
    #     key="session_id",
    #     value=auth.new_session(username),
    #     secure=True,
    #     max_age=int(auth.SESSION_EXPIRY.total_seconds()),
    # )
    # return response
    return await login_page(request=request, next=next, messages=[("error", "Not yet implemented!")])


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

    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    hypercorn_config = Config()
    hypercorn_config.bind = [f"{CONFIG.get("host")}:{CONFIG.get("port")}"]
    # hypercorn_config.quic_bind = [f"{CONFIG.host}:{CONFIG.port}"]
    asyncio.run(serve(app, hypercorn_config))  # type: ignore
