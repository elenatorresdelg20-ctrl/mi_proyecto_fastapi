from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.core.settings import ENV

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(8000), reload=(ENV != "production"))
