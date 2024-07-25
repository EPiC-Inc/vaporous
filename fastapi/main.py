from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api import api_v0

app = FastAPI(openapi_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates("templates")


@app.get("/")
async def root(request: Request):
    if (session_id := request.cookies.get("session_id")):
        return str(session_id)
    return RedirectResponse(url=request.url_for("login_page"))

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"messages": [("error", "Not implemented yet :V")]})
    # response.setcookie(key="session")
    # return RedirectResponse(url=request.url_for("root"))

app.mount("/api/v0", api_v0)

# # HTTP/3 support
# import asyncio
# from hypercorn.config import Config
# from hypercorn.asyncio import serve

# config = Config()
# config.bind = ["localhost:5000"]
# config.quic_bind = ["localhost:5000"]
# asyncio.run(serve(app, config))