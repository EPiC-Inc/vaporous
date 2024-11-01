import asyncio

from hypercorn.config import Config
from hypercorn.asyncio import serve

from app import app, CONFIG

hypercorn_config = Config()
hypercorn_config.bind = [f"{CONFIG.get("host")}:{CONFIG.get("port")}"]
# hypercorn_config.quic_bind = [f"{CONFIG.get("host")}:{CONFIG.get("port") + 1}"]
asyncio.run(serve(app, hypercorn_config))  # type: ignore
