from fastapi import FastAPI

api_v0 = FastAPI()

@api_v0.get("/")
async def root() -> dict:
	return {"detail": "aha!!"}