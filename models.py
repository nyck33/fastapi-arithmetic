from pydantic import BaseModel
from typing import Optional, List, Dict

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class OperationModel(BaseModel):
    operation: str
    operand1: float
    operand2: float

class OperandsModel(BaseModel):
    operand1: float
    operand2: float
