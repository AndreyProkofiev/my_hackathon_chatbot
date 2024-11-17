import uvicorn 
from fastapi import FastAPI

app=FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}


# if __name__ == '__main__':
#     uvicorn.run(app,
#                 host='127.0.0.1',
#                 port=80)


if __name__ == "__main__":
    uvicorn.run(
        "bot_api:app",
        host='127.0.0.1',
        port=8000,
        reload=True
    )