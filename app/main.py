"""The main server monolith."""

from mimetypes import guess_file_type
from os import PathLike
from pathlib import Path
from typing import Annotated, Optional
from urllib.parse import urlparse

from fastapi import Body, Cookie, FastAPI, Form, HTTPException, Request, Security, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
from sqlalchemy import select

from . import auth, file_handler
from .api import api_v0
from .config import CONFIG
from .database import SessionMaker
from .objects import Share

jinja2_environment = Environment()
jinja2_environment.policies["json.dumps_kwargs"]["ensure_ascii"] = False

app = FastAPI(openapi_url=None)
templates = Jinja2Templates(Path(__file__).parent / "templates")

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/.well-known", StaticFiles(directory=Path(__file__).parent / ".well-known"), name=".well-known")


async def get_session(session_id: Annotated[Optional[str], Cookie()] = None) -> auth.Session | None:
    if session_id and (session := auth.check_session(session_id)):
        return session
    return None


# TODO - rename
async def directory_list(
    base: PathLike[str] | str,
    file_path: Optional[PathLike[str] | str],
    access_level: int = 0,
) -> list | None:
    if file_path is not None:
        file_path = file_handler.safe_path_regex.sub(".", str(file_path))
    files = await file_handler.list_files(base=base, subfolder=file_path, access_level=access_level)
    return files


async def get_direct_file_response(
    base: PathLike[str] | str,
    file_path: PathLike[str] | str,
):
    if file_contents := await file_handler.get_file(base=base, file_path=file_path, direct=True):
        return file_contents
    raise HTTPException(status_code=404, detail="Unable to get file")


async def get_file_response_or_embed(
    request: Request, base: PathLike[str] | str, file_path: PathLike[str] | str, direct_url: str
):
    if file_contents := await file_handler.get_file(base=base, file_path=file_path):
        if file_contents == "||video||":
            file_path_to_serve = file_handler.get_upload_directory() / file_handler.safe_join(base, file_path)
            return templates.TemplateResponse(
                request=request,
                name="embed_video.html",
                context={
                    "url": str(request.url),
                    "mime_type": guess_file_type(file_path_to_serve)[0],
                    "direct_url": direct_url,
                    "title": file_path_to_serve.name,
                },
            )
        return file_contents
    raise HTTPException(status_code=404, detail="Unable to get file")


async def get_full_file_response(
    request: Request,
    base: PathLike[str] | str,
    file_path: Optional[PathLike[str] | str],
    current_directory_url: str,
    username: Optional[str] = None,
    access_level: int = 0,
    public: bool = False,
):
    files = await directory_list(
        base=base,
        file_path=file_path,
        access_level=access_level,
    )
    if files is not None:
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
                "media_files": list(filter(lambda f: f["type"] not in ("dir", "public_directory"), files)),
                "current_directory_url": str(current_directory_url),
                "username": username,
                "access_level": access_level,
                "path_segments": path_segments,
                "in_public_folder": public,
            },
        )
    if file_path is not None:
        if file_contents := await get_file_response_or_embed(
            request=request,
            base=base,
            file_path=file_path,
            direct_url=(
                str(request.url_for("serve_public_file_direct", file_path=file_path))
                if public
                else str(request.url_for("serve_file_direct", file_path=file_path))
            ),
        ):
            return file_contents
    raise HTTPException(status_code=404, detail="Unable to get files")


async def get_share_response(
    request: Request,
    share_id: str,
    base: PathLike[str] | str,
    file_path: Optional[PathLike[str] | str],
    username: Optional[str] = None,
    access_level: int = -1,
):
    files = await directory_list(
        base=base,
        file_path=file_path,
        access_level=access_level,
    )
    if files is not None:
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
                "media_files": list(filter(lambda f: f["type"] not in ("dir", "public_directory"), files)),
                "current_directory_url": str(request.url_for("get_share", share_id=share_id)),
                "username": username,
                "access_level": access_level,
                "path_segments": path_segments,
            },
        )
    if file_path is not None:
        if file_contents := await get_file_response_or_embed(
            request=request,
            base=base,
            file_path=file_path,
            direct_url=str(request.url_for("serve_share_file_direct", share_id=share_id, file_path=file_path)),
        ):
            return file_contents
    raise HTTPException(status_code=404, detail="Unable to get files")


async def get_collab_response(
    request: Request,
    share_id: str,
    base: PathLike[str] | str,
    file_path: Optional[PathLike[str] | str],
    username: Optional[str] = None,
    access_level: int = -1,
):
    files = await directory_list(
        base=base,
        file_path=file_path,
        access_level=access_level,
    )
    if files is not None:
        folder_name = Path(base).name
        path_segments = [{"path": "", "name": f"{folder_name} (Shared Folder)"}]
        current_path = []
        if file_path:
            for segment in Path(file_path).parts:
                current_path.append(segment)
                path_segments.append({"path": "/".join(current_path), "name": segment})
        return templates.TemplateResponse(
            request=request,
            name="collab_view.html",
            context={
                "share_id": share_id,
                "files": files,
                "media_files": list(filter(lambda f: f["type"] not in ("dir", "public_directory"), files)),
                "current_directory_url": str(request.url_for("get_collab", share_id=share_id)),
                "username": username,
                "access_level": access_level,
                "path_segments": path_segments,
                "in_public_folder": False,
            },
        )
    if file_path is not None:
        if file_contents := await get_file_response_or_embed(
            request=request,
            base=base,
            file_path=file_path,
            direct_url=str(request.url_for("serve_share_file_direct", share_id=share_id, file_path=file_path)),
        ):
            return file_contents
    raise HTTPException(status_code=404, detail="Unable to get files")


async def get_collab_share_info(session: Optional[auth.Session], share_id: str) -> dict:
    try:
        share_id_bytes = bytes.fromhex(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid share ID.")

    with SessionMaker() as engine:
        share: Share | None = engine.execute(select(Share).filter_by(share_id=share_id_bytes)).scalar_one_or_none()
        if not share:
            raise HTTPException(status_code=404, detail="Share ID not found.")
        if not share.collaborative:
            raise HTTPException(status_code=405, detail="Not a collaborative share.")
        allow_list = share.user_whitelist
        if allow_list:
            allow_list.split("$")
            if not (session and session.user_id in allow_list):
                raise HTTPException(status_code=403, detail="User ID not on allow list.")
        share_path = Path(share.path)
        return {
            "base": share_path,
            "anonymous_access": share.anonymous_access,
            "allow_list": allow_list or None,
        }


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
            "has_password": auth.check_user_has_password(session.username),
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
    if str(file_path) == ".":
        file_path = None
    return await get_full_file_response(
        request=request,
        base=session.user_id,
        file_path=file_path,
        current_directory_url=str(request.url_for("get_files")),
        username=session.username,
        access_level=session.access_level,
    )


@app.get("/d/{file_path:path}")
async def serve_file_direct(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    file_path: str,
):
    if session is None:
        return RedirectResponse(url=request.url_for("login_page").include_query_params(next=request.url.path))
    return await get_direct_file_response(base=session.user_id, file_path=file_path)


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
        if CONFIG.get("public_access_requires_login", True):
            return RedirectResponse(url=request.url_for("login_page").include_query_params(next=request.url.path))
    else:
        if session.access_level < CONFIG.get("public_access_level", -1):
            raise HTTPException(status_code=403, detail="User level insufficient.")
    return await get_full_file_response(
        request=request,
        base=str(CONFIG.get("public_directory")),
        file_path=file_path,
        current_directory_url=str(request.url_for("get_public_files")),
        username=session.username if session else None,
        access_level=session.access_level if session else -1,
        public=True,
    )


@app.get("/d_public/{file_path:path}")
async def serve_public_file_direct(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    file_path: PathLike[str] | str,
):
    if not CONFIG.get("public_directory"):
        raise HTTPException(status_code=404, detail="Public directory not enabled.")
    if session is None:
        if CONFIG.get("public_access_requires_login", True):
            return RedirectResponse(url=request.url_for("login_page").include_query_params(next=request.url.path))
    else:
        if session.access_level < CONFIG.get("public_access_level", -1):
            raise HTTPException(status_code=403, detail="User level insufficient.")
    return await get_direct_file_response(base=str(CONFIG.get("public_directory")), file_path=file_path)


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
        if share.collaborative:
            return RedirectResponse(url=request.url_for("get_collab", share_id=share_id, file_path=file_path))
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


@app.get("/d_s/{share_id}/{file_path:path}")
async def serve_share_file_direct(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    share_id: str,
    file_path: PathLike[str] | str,
):
    file_path = file_handler.safe_path_regex.sub(".", str(file_path))
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
    return await get_direct_file_response(base=share_path, file_path=file_path)


@app.get("/collab/{share_id}")
@app.get("/collab/{share_id}/{file_path:path}")
async def get_collab(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    share_id: str,
    file_path: Optional[str] = None,
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
        if not share.collaborative:
            return RedirectResponse(url=request.url_for("get_share", share_id=share_id, file_path=file_path))
        share_path = Path(share.path)
        # owner_id = share_path.parts[0]
        # share_path = share_path.relative_to(owner_id)
        # share_subpath = share_path / file_path
        return await get_collab_response(
            request=request,
            share_id=share_id,
            base=share_path,
            file_path=file_path,
            username=session.username if session else None,
            access_level=session.access_level if session else -1,
        )


@app.post("/new_share")
async def add_share(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    file_path: Annotated[str, Form()],
    anonymous_access: Annotated[bool, Form()] = False,
    collaborative: Annotated[bool, Form()] = False,
):
    if session is None:
        raise HTTPException(status_code=401, detail="neener neener neener")
    base = session.user_id
    success, share_id = await file_handler.create_share(
        user_id=session.user_id,
        file_path=file_path,
        anonymous_access=anonymous_access,
        collaborative=collaborative,
        expires=None,
    )
    return (success, str(request.url_for("get_share", share_id=share_id)).replace(" ", "%20"))


@app.get("/list_shares")
async def list_shares(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    filter: Optional[str] = None,
):
    if session is None:
        raise HTTPException(status_code=401, detail="Anonymous users cannot get shares!")
    shares = await file_handler.list_shares(session.user_id, filter)
    for share in shares:
        share["url"] = str(request.url_for("get_share", share_id=share["id"])).replace(" ", "%20")
    return shares


@app.post("/remove_share")
async def remove_share(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    share_id: Annotated[str, Body()],
):
    if session is None:
        raise HTTPException(status_code=401, detail="Anonymous users cannot get shares!")
    return await file_handler.delete_share(share_id, session.user_id)


@app.post("/new_folder")
async def new_folder(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    file_path: Annotated[str, Body()],
    folder_name: Annotated[str, Body()],
    to_public: Annotated[bool, Body()],
):
    if session is None:
        raise HTTPException(status_code=401, detail="Anonymous users cannot create folders!")
    return await file_handler.new_folder(
        base=CONFIG.get("public_directory") if to_public and CONFIG.get("public_directory") else session.user_id,
        file_path=file_path,
        folder_name=folder_name,
    )


@app.post("/rename")
async def rename(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    file_path: Annotated[str, Body()],
    new_name: Annotated[str, Body()],
    to_public: Annotated[bool, Body()],
):
    if session is None:
        raise HTTPException(status_code=401, detail="Anonymous users cannot rename!")
    return await file_handler.rename(
        base=CONFIG.get("public_directory") if to_public and CONFIG.get("public_directory") else session.user_id,
        file_path=file_path,
        new_name=new_name,
    )


@app.post("/move")
async def move(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    file_path: Annotated[str, Body()],
    to: Annotated[str, Body()],
    to_public: Annotated[bool, Body()],
):
    if session is None:
        raise HTTPException(status_code=401, detail="Anonymous users cannot move!")
    to_base = None
    if not to:
        to_base = session.user_id
    elif to == "||public||":
        to = ""
        to_base = CONFIG.get("public_directory") or session.user_id
    base = CONFIG.get("public_directory") if to_public and CONFIG.get("public_directory") else session.user_id
    return await file_handler.move(
        base=base,
        to_base=to_base or base,
        file_path=file_path,
        to=to,
    )


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
    from_public: Annotated[bool, Body()],
    file_path: Annotated[str, Body()],
):
    # from_public, file_path = body
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


@app.post("/add_password")
async def add_password(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    new_password: Annotated[str, Form()],
    confirm_new_password: Annotated[str, Form()],
):
    if session is None:
        raise HTTPException(status_code=401, detail="Cannot add password without being logged in first!")
    if not new_password:
        return (False, "Cannot add a blank password!")
    if new_password != confirm_new_password:
        return (False, "New passwords must match!")
    if not auth.check_user_has_password(session.username):
        return auth.change_password(session.username, new_password=new_password)
    return (False, "Cannot add a password to an account that already has one!")


@app.post("/remove_password")
async def remove_password(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
):
    if session is None:
        raise HTTPException(status_code=401, detail="Cannot remove password without being logged in first!")
    return auth.remove_password(session.username)


@app.post("/change_username")
async def change_username(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    new_username: Annotated[str, Form()],
):
    if session is None:
        raise HTTPException(status_code=401, detail="Cannot change username without being logged in first!")
    return auth.change_username(old_username=session.username, new_username=new_username)


@app.get("/login")
async def login_page(request: Request, next: Optional[str] = None, messages: Optional[list] = None):
    if messages is None:
        messages = []
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "messages": messages,
            "next": next,
            "banner": CONFIG.get("banner"),
            "can_enroll": bool(CONFIG.get("self_enrollment", False)),
        },
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
        response = RedirectResponse(
            url=next or request.url_for("root"), status_code=status.HTTP_303_SEE_OTHER
        )  # type:ignore
        response.set_cookie(
            key="session_id",
            value=auth.new_session(username, invalidate_previous_sessions=CONFIG.get("multiple_sessions_signout")),
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


@app.get("/signup")
async def enroll_page(request: Request, next: Optional[str] = None, messages: Optional[list] = None):
    if messages is None:
        messages = []
    if not CONFIG.get("self_enrollment"):
        return RedirectResponse(url=request.url_for("login_page").include_query_params(next=next or ""))
    return templates.TemplateResponse(
        request=request,
        name="enroll.html",
        context={
            "messages": messages,
            "next": next,
            "banner": CONFIG.get("banner"),
            "passcode": CONFIG.get("self_enrollment_passcode"),
        },
    )


@app.post("/signup")
async def enroll(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Security()],
    confirm_password: Annotated[str, Form()],
    next: Optional[str] = None,
    passcode: Annotated[Optional[str], Form()] = None,
):
    if not CONFIG.get("self_enrollment"):
        return RedirectResponse(url=request.url_for("login_page").include_query_params(next=next or ""))
    username = form.username
    password = form.password
    if password != confirm_password:
        return await enroll_page(request=request, next=next, messages=[("error", "Passwords must match!")])
    stored_passcode = CONFIG.get("self_enrollment_passcode")
    if stored_passcode and passcode != stored_passcode:
        return await enroll_page(request=request, next=next, messages=[("error", "Passcode is incorrect!")])
    success, message = auth.add_user(username=username, password=password)
    if success:
        response = RedirectResponse(
            url=next or request.url_for("root"), status_code=status.HTTP_303_SEE_OTHER
        )  # type:ignore
        response.set_cookie(
            key="session_id",
            value=auth.new_session(username),
            # secure=True,
            max_age=int(auth.SESSION_EXPIRY.total_seconds()),
        )
        return response
    return await enroll_page(request=request, next=next, messages=[("error", message)])


# SECTION - Collab operations
@app.post("/collab/{share_id}/new_folder")
async def collab_new_folder(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    share_id: str,
    file_path: Annotated[str, Body()],
    folder_name: Annotated[str, Body()],
):
    share_info = await get_collab_share_info(session, share_id)
    return await file_handler.new_folder(
        base=share_info["base"],
        file_path=file_path,
        folder_name=folder_name,
    )


@app.post("/collab/{share_id}/rename")
async def collab_rename(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    share_id: str,
    file_path: Annotated[str, Body()],
    new_name: Annotated[str, Body()],
):
    share_info = await get_collab_share_info(session, share_id)
    return await file_handler.rename(
        base=share_info["base"],
        file_path=file_path,
        new_name=new_name,
    )


@app.post("/collab/{share_id}/move")
async def collab_move(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    share_id: str,
    file_path: Annotated[str, Body()],
    to: Annotated[str, Body()],
):
    share_info = await get_collab_share_info(session, share_id)
    return await file_handler.move(
        base=share_info["base"],
        to_base=share_info["base"],
        file_path=file_path,
        to=to,
    )


@app.post("/collab/{share_id}/upload")
async def collab_upload(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    share_id: str,
    file_path: Annotated[str, Form()],
    compression_level: Annotated[int, Form()],
    files: list[UploadFile],
):
    share_info = await get_collab_share_info(session, share_id)
    return await file_handler.upload_files(
        base=share_info["base"],
        file_path=file_path,
        files=files,
        compression=compression_level,
    )


@app.post("/collab/{share_id}/delete")
async def collab_delete(
    request: Request,
    session: Annotated[Optional[auth.Session], Security(get_session)],
    share_id: str,
    from_public: Annotated[bool, Body()],
    file_path: Annotated[str, Body()],
):
    share_info = await get_collab_share_info(session, share_id)
    return await file_handler.delete_file(share_info["base"], file_path)


#!SECTION


# TODO - finish this
@app.get("/logout")
async def logout(request: Request, session: Annotated[Optional[auth.Session], Security(get_session)]):
    response = RedirectResponse(url=request.url_for("root"))
    if session:
        auth.invalidate_session(session.session_id)
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
