import uvicorn 
from fastapi import FastAPI
from fastapi import Request, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Any, Dict, AnyStr, List, Union

import os, sys
from dotenv import load_dotenv

load_dotenv('ya.env')

from bot.llm_chain import chain
from bot.classifier import mk_classyfi

def processor(q:str):
    classyfi_answ = mk_classyfi(q)
    if classyfi_answ == "консультация":
        answer = chain.invoke(q)
        return {"LLM_answ": answer,
                "class":classyfi_answ}
    else:
        return {"LLM_answ": "",
                "class":classyfi_answ}



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
    answer = processor(q)
    return answer

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )