import uvicorn 
from fastapi import FastAPI
from fastapi import Request, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Any, Dict, AnyStr, List, Union
## for test
import time

app=FastAPI()



@app.get("/")
def root():
    data = {"message": "hello from api"}
    json_data = jsonable_encoder(data)
    return JSONResponse(content=json_data)


@app.post('/user_mess')
def user_mess(data = Body()):
    # json_data = jsonable_encoder(data)
    # user_say = JSONResponse(content=json_data)
  
    return {"d":data, "t":str(type(data))}


    # return ({"user_say":user_say,
    #          "data_type": str(type(user_say))})

JSONObject = Dict[AnyStr, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]


@app.post('/user_mess2')
def my_api_post(user_json: JSONStructure = None):
    sleep_time = user_json["sleep_time"]
    time.sleep(sleep_time)
    user_say = user_json["message"]
    return {"user_say": user_say, "api_sleep":sleep_time}

if __name__ == "__main__":
    uvicorn.run(
        "bot_api:app",
        host='127.0.0.1',
        port=8000,
        reload=True
    )