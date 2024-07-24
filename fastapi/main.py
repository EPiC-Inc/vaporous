from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates("templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"messages": [("error", "Not implemented yet :V")]})
