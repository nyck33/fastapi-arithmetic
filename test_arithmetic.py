import requests

BASE_URL = "http://localhost:8000"

def print_response(response):
    try:
        response_json = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response_json}")
    except ValueError:
        print("Response is not valid JSON")
        print(response.text)

# Test for the catch-all operation endpoint
def test_operate(operation, operand1, operand2):
    url = f"{BASE_URL}/operate"
    data = {
        "operation": operation,
        "operand1": operand1,
        "operand2": operand2
    }
    response = requests.post(url, json=data)
    print(f"\nOperation: {operation} {operand1} and {operand2}")
    print_response(response)

# Test for specific endpoints
def test_add(operand1, operand2):
    url = f"{BASE_URL}/add"
    data = {
        "operand1": operand1,
        "operand2": operand2
    }
    response = requests.post(url, json=data)
    print(f"\nAdding: {operand1} and {operand2}")
    print_response(response)

def test_subtract(operand1, operand2):
    url = f"{BASE_URL}/subtract"
    data = {
        "operand1": operand1,
        "operand2": operand2
    }
    response = requests.post(url, json=data)
    print(f"\nSubtracting: {operand1} and {operand2}")
    print_response(response)

def test_multiply(operand1, operand2):
    url = f"{BASE_URL}/multiply"
    data = {
        "operand1": operand1,
        "operand2": operand2
    }
    response = requests.post(url, json=data)
    print(f"\nMultiplying: {operand1} and {operand2}")
    print_response(response)

def test_divide(operand1, operand2):
    url = f"{BASE_URL}/divide"
    data = {
        "operand1": operand1,
        "operand2": operand2
    }
    response = requests.post(url, json=data)
    print(f"\nDividing: {operand1} by {operand2}")
    print_response(response)


# Execute tests
if __name__ == "__main__":
    # Test specific endpoints
    test_add(10, 5)
    test_subtract(10, 5)
    test_multiply(10, 5)
    test_divide(10, 5)
    
    # Test catch-all operation endpoint
    test_operate("add", 10, 5)
    test_operate("subtract", 10, 5)
    test_operate("multiply", 10, 5)
    test_operate("divide", 10, 5)
    test_operate("divide", 10, 0)  # Test division by zero

    # Very large number (Overflow check)
    test_add(1e308, 1e308)  # Add two very large numbers
    test_multiply(1e154, 1e154)  # Multiply two large numbers to exceed float range

    # Very small number (Underflow check)
    test_subtract(1e-308, 1e-308)  # Subtract two very small numbers
    test_divide(1e-308, 1e308)  # Divide a very small number by a large number
    # Invalid input (strings instead of numbers)
    test_add("string1", "string2")  # Expect validation error
    test_multiply("abc", 123)       # Expect validation error

    test_add(-10, -5)  # Expect result to be -15
    test_subtract(-10, 5)  # Expect result to be -15
    test_multiply(-10, -5)  # Expect result to be 50
    test_divide(-10, -5)  # Expect result to be 2.0
