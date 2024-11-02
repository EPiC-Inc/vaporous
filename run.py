import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config
from hypercorn.middleware import ProxyFixMiddleware

from app import app, CONFIG

app = ProxyFixMiddleware(app, mode="modern", trusted_hops=1)

hypercorn_config = Config()
hypercorn_config.bind = [f"{CONFIG.get("host")}:{CONFIG.get("port")}"]
# hypercorn_config.quic_bind = [f"{CONFIG.get("host")}:{CONFIG.get("port") + 1}"]
asyncio.run(serve(app, hypercorn_config))  # type: ignore
