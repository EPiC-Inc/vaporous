from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates("templates")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": Request, "name": "test"})
