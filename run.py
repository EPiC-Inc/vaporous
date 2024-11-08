import uvicorn

from app import CONFIG

if __name__ == "__main__":
    uvicorn.run("app:app", host=CONFIG.get("host", "127.0.0.1"), port=CONFIG.get("port", "8080"), forwarded_allow_ips=CONFIG.get("reverse_proxy_ips"))
