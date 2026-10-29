def main() -> None:
    import uvicorn

    uvicorn.run("fastapi_project.main:app", host="127.0.0.1", port=8000)
