from typing import Any
from starlette.exceptions import HTTPException as StarletteHTTPException

class ExceptionBase(StarletteHTTPException):
    def __init__(self,status_code: int,message:str):
        self.status_code = status_code
        self.message     = message