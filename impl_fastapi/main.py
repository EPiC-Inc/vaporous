"""The main server monolith."""

from os import PathLike
from pathlib import Path
from typing import Annotated, Optional
from urllib.parse import urlparse

from fastapi import Body, Cookie, FastAPI, Form, HTTPException, Request, Security, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

import auth
import file_handler
from api import api_v0
from config import CONFIG
from database import SessionMaker
from objects import Share, User

app = FastAPI(openapi_url=None)
templates = Jinja2Templates(Path(__file__).parent / "templates")

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/.well-known", StaticFiles(directory=Path(__file__).parent / ".well-known"), name=".well-known")


async def get_session(session_id: Annotated[Optional[str], Cookie()] = None) -> auth.Session | None:
    if session_id and (session := auth.check_session(session_id)):
        return session
    return None


async def get_file_response(
    request: Request,
    base: PathLike[str] | str,
    file_path: Optional[PathLike[str] | str],
    current_directory_url: str,
    username: Optional[str] = None,
    access_level: int = 0,
    public: bool = False,
):
    if file_path is not None:
        file_path = file_handler.safe_path_regex.sub(".", str(file_path))
    files = await file_handler.list_files(base=base, subfolder=file_path, access_level=access_level)
    if files is None and file_path is not None:  # NOTE - I smell a possible bug here?
        if file_contents := await file_handler.get_file(base=base, file_path=file_path):
            return file_contents
        raise HTTPException(status_code=404, detail="Unable to get files")
    path_segments = [{"path": "", "name": "Public Files"}] if public else []
    current_path = []
    if file_path:
        for segment in Path(file_path).parts:
            current_path.append(segment)
            path_segments.append({"path": "/".join(current_path), "name": segment})
    return templates.TemplateResponse(
        request=request,
        name="file_view.html",
        context={
            "files": files,
            "current_directory_url": current_directory_url,
            "username": username,
            "access_level": access_level,
            "path_segments": path_segments,
            "in_public_folder": public,
        },
    )


async def get_share_response(
    request: Request,
    share_id: str,
    base: PathLike[str] | str,
    file_path: Optional[PathLike[str] | str],
    username: Optional[str] = None,
    access_level: int = -1,
):
    file_path = file_handler.safe_path_regex.sub(".", str(file_path))
    files = await file_handler.list_files(base=base, subfolder=file_path, access_level=-1)
    if files is None and file_path is not None:  # NOTE - I smell a possible bug here?
        if file_contents := await file_handler.get_file(base=base, file_path=file_path):
            return file_contents
        raise HTTPException(status_code=404, detail="Unable to get files")
    if files:
        for file_ in files:
            file_["path"] = "/".join(Path(file_["path"]).parts[1:])
    folder_name = Path(base).name
    path_segments = [{"path": "", "name": f"{folder_name} (Shared Folder)"}]
    current_path = []
    if file_path:
        for segment in Path(file_path).parts:
            current_path.append(segment)
            path_segments.append({"path": "/".join(current_path), "name": segment})
    return templates.TemplateResponse(
        request=request,
        name="share_view.html",
        context={
            "files": files,
            "current_directory_url": request.url_for("get_share", share_id=share_id),
            "username": username,
            "access_level": access_level,
            "path_segments": path_segments,
        },
    )


@app.exception_handler(404)
async def not_found(request: Request, exception: HTTPException):
    return templates.TemplateResponse(request=request, name="404.html")


@app.get("/")
async def root(request: Request, session: Annotated[Optional[auth.Session], Security(get_session)]):
    if session is None:
        return RedirectResponse(url=request.url_for("login_page"))
    return RedirectResponse(url=request.url_for("get_files"))


@app.get("/settings")
async def settings(request: Request, session: Annotated[Optional[auth.Session], Security(get_session)]):
    if session is None:
        return RedirectResponse(url=request.url_for("login_page").include_query_params(next=request.url.path))
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "username": session.username,
            "access_level": session.access_level,
        },
    )


@app.get("/control_panel")
async def control_panel(request: Request, session: Annotated[Optional[auth.Session], Security(get_session)]):
    if session is None:
        return RedirectResponse(url=request.url_for("login_page").include_query_params(next=request.url.path))
    if session.access_level < 2:
        raise HTTPException(status_code=403, detail="Access level insufficient.")
    return templates.TemplateResponse(
        request=request,
        name="control_panel.html",
        context={
            "username": session.username,
            "access_level": session.access_level,
        },
    )


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
        request=request,
        base=session.user_id,
        file_path=file_path,
        current_directory_url=str(request.url_for("get_files")),
        username=session.username,
        access_level=session.access_level,
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
    else:
        if session.access_level < CONFIG.get("public_access_level", -1):
            raise HTTPException(status_code=403, detail="User level insufficient.")
    return await get_file_response(
        request=request,
        base=str(CONFIG.get("public_directory")),
        file_path=file_path,
        current_directory_url=str(request.url_for("get_public_files")),
        username=session.username if session else None,
        access_level=session.access_level if session else -1,
        public=True,
    )


@app.get("/s/{share_id}")
@app.get("/s/{share_id}/{file_path:path}")
async def get_share(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    share_id: str,
    file_path: Optional[PathLike[str] | str] = None,
):
    if file_path:
        file_path = file_handler.safe_path_regex.sub(".", str(file_path))
    else:
        file_path = "."
    try:
        share_id_bytes = bytes.fromhex(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid share ID.")

    with SessionMaker() as engine:
        share: Share | None = engine.execute(select(Share).filter_by(share_id=share_id_bytes)).scalar_one_or_none()
        if not share:
            raise HTTPException(status_code=404, detail="Share ID not found.")
        if allow_list := share.user_whitelist:
            if not (session and session.user_id in allow_list.split("$")):
                raise HTTPException(status_code=403, detail="Not on share list.")
        elif not (share.anonymous_access or session):
            raise HTTPException(status_code=401, detail="Share not publicly accessible.")
        share_path = Path(share.path)
        # owner_id = share_path.parts[0]
        # share_path = share_path.relative_to(owner_id)
        # share_subpath = share_path / file_path
        return await get_share_response(
            request=request,
            share_id=share_id,
            base=share_path,
            file_path=file_path,
            username=session.username if session else None,
            access_level=session.access_level if session else -1,
        )


@app.get("/list_shares")
async def list_shares(request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)]
):
    if session is None:
        raise HTTPException(status_code=401, detail="Anonymous users cannot get shares!")
    owned_shares: list[dict] = []
    with SessionMaker() as engine:
        shares: list[Share] = engine.execute(select(Share).filter_by(owner=bytes.fromhex(session.user_id))).scalars()
        for share in shares:
            allow_list = []
            if share.user_whitelist:
                for user_id in share.user_whitelist.split("$"):
                    if (user := engine.execute(select(User).filter_by(user_id=bytes.fromhex(user_id))).scalar_one_or_none()):
                        allow_list.append(user.username)
            owned_shares.append({
                "id": share.share_id.hex(),
                "shared_file": share.path,
                "anonymous_access": share.anonymous_access,
                "allowed_users": allow_list
            })
    return owned_shares


# FIXME
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
    files = await file_handler.list_files(base=str(base), subfolder=file_path)
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


@app.post("/upload")
async def upload(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    file_path: Annotated[str, Form()],
    to_public: Annotated[bool, Form()],
    compression_level: Annotated[int, Form()],
    files: list[UploadFile],
):
    if session is None:
        raise HTTPException(status_code=401, detail="You may not upload anonymously!")
    return await file_handler.upload_files(
        base=CONFIG.get("public_directory") if to_public and CONFIG.get("public_directory") else session.user_id,
        file_path=file_path,
        files=files,
        compression=compression_level,
    )


@app.post("/delete")
async def delete(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    body: Annotated[list, Body()]
):
    from_public, file_path = body
    print(body)
    if session is None:
        raise HTTPException(status_code=401, detail="You CAN NOT delete anonymously!")
    base = CONFIG.get("public_directory") if from_public and CONFIG.get("public_directory") else session.user_id
    return await file_handler.delete_file(base, file_path)


@app.post("/change_password")
async def change_password(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    old_password: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    confirm_new_password: Annotated[str, Form()],
):
    if session is None:
        raise HTTPException(status_code=401, detail="Cannot change password without being logged in first!")
    if new_password != confirm_new_password:
        return (False, "New passwords must match!")
    return auth.change_password(session.username, new_password=new_password, old_password=old_password)


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
        # The above branch breaks everything if next was maliciously set, so let's properly un-break it
        if not next:
            next = request.url_for("root")  # type:ignore
        response = RedirectResponse(url=next, status_code=status.HTTP_303_SEE_OTHER)  # type:ignore
        response.set_cookie(
            key="session_id",
            value=auth.new_session(username),
            # secure=True,
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


# TODO - finish this
@app.get("/logout")
async def logout(request: Request, session: Annotated[Optional[auth.Session], Security(get_session)]):
    response = RedirectResponse(url=request.url_for("root"))
    if session:
        # auth.invalidate_session(session)
        response.delete_cookie(key="session_id")
    return response


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
