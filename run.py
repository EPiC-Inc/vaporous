import uvicorn

from app import CONFIG

if __name__ == "__main__":
    uvicorn.run("app:app", host=CONFIG.get("host"), port=CONFIG.get("port"), forwarded_allow_ips=CONFIG.get("reverse_proxy_ips"))
