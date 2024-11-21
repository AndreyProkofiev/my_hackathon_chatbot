import uvicorn 
from fastapi import FastAPI
from fastapi import Request, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Any, Dict, AnyStr, List, Union

import os, sys
from dotenv import load_dotenv
## for test
import time
load_dotenv('ya.env')

module_p = os.environ['module_p']
sys.path.append(module_p)
from bot.llm_chain import chain


app=FastAPI()


JSONObject = Dict[AnyStr, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]


@app.get("/")
def root():
    data = {"message": "hello from api"}
    json_data = jsonable_encoder(data)
    return JSONResponse(content=json_data)



@app.post('/user_mess')
def my_api_post(user_json: JSONStructure = None):
    
    g = user_json["message"]
    answer = chain.invoke(g)
    return {"LLM_answ": answer}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )