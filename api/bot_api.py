import uvicorn 
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

app=FastAPI()

# @app.get("/")
# def root():
#     return {"message": "Hello World"}

@app.get("/")
def root():
    data = {"message": "Hello METANIT.COM"}
    json_data = jsonable_encoder(data)
    return JSONResponse(content=json_data)

@app.post('/user_mess')
def user_mess():
    pass


if __name__ == "__main__":
    uvicorn.run(
        "bot_api:app",
        host='127.0.0.1',
        port=8000,
        reload=True
    )