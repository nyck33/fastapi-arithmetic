from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyHeader
from fastapi.security.api_key import APIKeyHeader
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.encoders import jsonable_encoder
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.models import APIKey
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
from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse

# making docs and all routes require api key
API_KEY = "123456789!"
API_KEY_NAME ="access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    print(f'received api key {api_key_header}')
    if api_key_header == API_KEY:
        return api_key_header
    else:
        print(f"Invalid API key: {api_key_header}") # logs invalid key
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate API Key"
        )

# Load environment variables
load_dotenv()

#SECRET_KEY = os.getenv('SECRET_KEY')
#ALGORITHM = os.getenv('ALGORITHM')
#ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Using the service role key for server-side operations

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FastAPI instance
#app = FastAPI(docs_url=None, redoc_url=None)
app = FastAPI()

def custom_openapi():
    if app.openapi_schema: 
        return app.openapi_schema 
    openapi_schema = get_openapi(
        title="Your API", 
        version="1.0.0",
        description="Recruiter API Documentaiton",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "name": "access_token",
            "in": "header"
        }
    }
    openapi_schema["security"] = [{"APIKeyHeader": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# apply custom OpenAPI schema
app.openapi = custom_openapi 

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


@app.get("/docs", dependencies=[Depends(get_api_key)])
async def get_docs():
    #return RedirectResponse(url="/docs")
    return JSONResponse(get_openapi(
        title="Custom FastAPI Docs",
        version="1.0.0",
        description="API documentation for recuriters",
        routes=app.routes
    ))

@app.post("/add", dependencies=[Depends(get_api_key)])
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

    
@app.post("/subtract", dependencies=[Depends(get_api_key)])
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


@app.post("/multiply", dependencies=[Depends(get_api_key)])
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

@app.post("/divide", dependencies=[Depends(get_api_key)])
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