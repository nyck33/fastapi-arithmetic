from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
import math
from typing import List
from jose import JWTError, jwt
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from utils import authenticate_user, create_access_token
from models import Token, TokenData, OperationModel, OperandsModel
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.encoders import jsonable_encoder

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Using the service role key for server-side operations

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI instance
app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost:3000",  # React development server
    "https://your-frontend-domain.com",  # Your production frontend domain
    # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of origins that should be permitted to make requests
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# OAuth2PasswordBearer instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/operate")
def operate(operation_data: OperationModel):
    operation = operation_data.operation
    operand1 = operation_data.operand1
    operand2 = operation_data.operand2

    try:
        # Input validation checks
        if isinstance(operand1, str) or isinstance(operand2, str):
            # Log invalid operand type error
            log_operation_to_db(operation, operand1, operand2, None, "Error", error_message="Invalid operand type, expected a number")
            raise HTTPException(status_code=400, detail="Invalid operand type, expected a number")
        
        if math.isnan(operand1) or math.isnan(operand2):
            # Log NaN error
            log_operation_to_db(operation, operand1, operand2, None, "Error", error_message="Operands cannot be NaN")
            raise HTTPException(status_code=400, detail="Operands cannot be NaN")

        # Perform operation based on the type
        if operation == "add":
            result = operand1 + operand2
        elif operation == "subtract":
            result = operand1 - operand2
        elif operation == "multiply":
            result = operand1 * operand2
        elif operation == "divide":
            if operand2 == 0:
                # Log division by zero error
                log_operation_to_db(operation, operand1, operand2, None, "Error", error_message="Division by zero")
                raise HTTPException(status_code=400, detail="Division by zero")
            result = operand1 / operand2
        else:
            # Log invalid operation error
            log_operation_to_db(operation, operand1, operand2, None, "Error", error_message="Invalid operation")
            raise HTTPException(status_code=400, detail="Invalid operation")

        # Log operation to the database on success
        log_operation_to_db(operation, operand1, operand2, result, "Success", error_message=None)
        return {"result": result}

    except Exception as e:
        # Log any other exceptions that occur
        log_operation_to_db(operation, operand1, operand2, None, "Error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/add")
def add(operands: OperandsModel):
    try:
        # Input validation checks
        if isinstance(operands.operand1, str) or isinstance(operands.operand2, str):
            # Log invalid operand type error
            log_operation_to_db("add", operands.operand1, operands.operand2, None, "Error", error_message="Invalid operand type, expected a number")
            raise HTTPException(status_code=400, detail="Invalid operand type, expected a number")
        
        if math.isnan(operands.operand1) or math.isnan(operands.operand2):
            # Log NaN error
            log_operation_to_db("add", operands.operand1, operands.operand2, None, "Error", error_message="Operands cannot be NaN")
            raise HTTPException(status_code=400, detail="Operands cannot be NaN")
        
        # Perform addition
        result = operands.operand1 + operands.operand2

        if math.isinf(result):
            # Log overflow error
            log_operation_to_db("add", operands.operand1, operands.operand2, None, "Error", error_message="Overflow error")
            raise HTTPException(status_code=400, detail="Overflow error")
        
        if result == 0 and (operands.operand1 != 0 and operands.operand2 != 0):
            # Log underflow error
            log_operation_to_db("add", operands.operand1, operands.operand2, None, "Error", error_message="Underflow error")
            raise HTTPException(status_code=400, detail="Underflow error")
        
        # Log operation to the database on success
        log_operation_to_db("add", operands.operand1, operands.operand2, result, "Success", error_message=None)
        return {"result": result}

    except Exception as e:
        # Log any other exceptions that occur
        log_operation_to_db("add", operands.operand1, operands.operand2, None, "Error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    
@app.post("/subtract")
def subtract(operands: OperandsModel):
    try:
        # Input validation checks
        if isinstance(operands.operand1, str) or isinstance(operands.operand2, str):
            # Log the invalid type error to the database
            log_operation_to_db("subtract", operands.operand1, operands.operand2, None, "Error", error_message="Invalid operand type, expected a number")
            raise HTTPException(status_code=400, detail="Invalid operand type, expected a number")
        
        if math.isnan(operands.operand1) or math.isnan(operands.operand2):
            # Log the NaN error to the database
            log_operation_to_db("subtract", operands.operand1, operands.operand2, None, "Error", error_message="Operands cannot be NaN")
            raise HTTPException(status_code=400, detail="Operands cannot be NaN")

        # Perform the subtraction
        result = operands.operand1 - operands.operand2

        if math.isinf(result):
            # Log overflow error
            log_operation_to_db("subtract", operands.operand1, operands.operand2, None, "Error", error_message="Overflow error")
            raise HTTPException(status_code=400, detail="Overflow error")
        
        if result == 0 and (operands.operand1 != 0 and operands.operand2 != 0):
            # Log underflow error
            log_operation_to_db("subtract", operands.operand1, operands.operand2, None, "Error", error_message="Underflow error")
            raise HTTPException(status_code=400, detail="Underflow error")
        
        # Log operation to the database on success
        log_operation_to_db("subtract", operands.operand1, operands.operand2, result, "Success", error_message=None)
        return {"result": result}
    
    except Exception as e:
        # Log any other exceptions that occur
        log_operation_to_db("subtract", operands.operand1, operands.operand2, None, "Error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/multiply")
def multiply(operands: OperandsModel):
    try:
        # Input validation checks
        if isinstance(operands.operand1, str) or isinstance(operands.operand2, str):
            # Log the invalid type error to the database
            log_operation_to_db("multiply", operands.operand1, operands.operand2, None, "Error", error_message="Invalid operand type, expected a number")
            raise HTTPException(status_code=400, detail="Invalid operand type, expected a number")
        
        if math.isnan(operands.operand1) or math.isnan(operands.operand2):
            # Log the NaN error to the database
            log_operation_to_db("multiply", operands.operand1, operands.operand2, None, "Error", error_message="Operands cannot be NaN")
            raise HTTPException(status_code=400, detail="Operands cannot be NaN")
        
        # Perform the multiplication
        result = operands.operand1 * operands.operand2

        if math.isinf(result):
            # Log overflow error
            log_operation_to_db("multiply", operands.operand1, operands.operand2, None, "Error", error_message="Overflow error")
            raise HTTPException(status_code=400, detail="Overflow error")
        
        if result == 0 and (operands.operand1 != 0 and operands.operand2 != 0):
            # Log underflow error
            log_operation_to_db("multiply", operands.operand1, operands.operand2, None, "Error", error_message="Underflow error")
            raise HTTPException(status_code=400, detail="Underflow error")

        # Log successful operation
        log_operation_to_db("multiply", operands.operand1, operands.operand2, result, "Success", error_message=None)
        return {"result": result}

    except Exception as e:
        # Log any other exceptions that occur
        log_operation_to_db("multiply", operands.operand1, operands.operand2, None, "Error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/divide")
def divide(operands: OperandsModel):
    try:
        # Input validation checks
        if isinstance(operands.operand1, str) or isinstance(operands.operand2, str):
            # Log the invalid type error to the database
            log_operation_to_db("divide", operands.operand1, operands.operand2, None, "Error", error_message="Invalid operand type, expected a number")
            raise HTTPException(status_code=400, detail="Invalid operand type, expected a number")
        
        if math.isnan(operands.operand1) or math.isnan(operands.operand2):
            # Log the NaN error to the database
            log_operation_to_db("divide", operands.operand1, operands.operand2, None, "Error", error_message="Operands cannot be NaN")
            raise HTTPException(status_code=400, detail="Operands cannot be NaN")

        if operands.operand2 == 0:
            # Log division by zero error
            log_operation_to_db("divide", operands.operand1, operands.operand2, None, "Error", error_message="Division by zero")
            raise HTTPException(status_code=400, detail="Division by zero")

        # Perform the division
        result = operands.operand1 / operands.operand2

        if math.isinf(result):
            # Log overflow error
            log_operation_to_db("divide", operands.operand1, operands.operand2, None, "Error", error_message="Overflow error")
            raise HTTPException(status_code=400, detail="Overflow error")
    
        if result == 0 and (operands.operand1 != 0 and operands.operand2 != 0):
            # Log underflow error
            log_operation_to_db("divide", operands.operand1, operands.operand2, None, "Error", error_message="Underflow error")
            raise HTTPException(status_code=400, detail="Underflow error")
        
        # Log operation to the database on success
        log_operation_to_db("divide", operands.operand1, operands.operand2, result, "Success", error_message=None)

        return {"result": result}
    
    except Exception as e:
        # Log any other exceptions that occur
        log_operation_to_db("divide", operands.operand1, operands.operand2, None, "Error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))


def log_operation_to_db(operation_type: str, operand1: float, operand2: float, result: float, status: str, error_message: str = None):
    if error_message is not None:
        print(f"Error: {error_message}")
    try:
        # Insert operation log with error details if status is "Error"
        supabase.table('operation_logs').insert({
            "operation_type": operation_type,
            "operand1": operand1,
            "operand2": operand2,
            "result": result,
            "status": status,
            "error_message": error_message
        }).execute()
    except Exception as e:
        print(f"Failed to log to database: {str(e)}")

# Custom handler for RequestValidationError
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the validation error to the database
    error_message = str(exc)
    # You can customize this part to extract relevant details for the log
    log_operation_to_db("validation_error", None, None, None, "Error", error_message=error_message)
    
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors()})
    )