from fastmcp import FastMCP

mcp = FastMCP("simpleremoteserver")

@mcp.tool
def hello(name: str):
    """A simple hello world function."""
    return f"Hello, {name}!"

@mcp.tool
def add(a: int, b: int):
    """A simple addition function."""
    return a + b

@mcp.tool
def subtract(a: int, b: int):
    """A simple subtraction function."""
    return a - b

@mcp.tool
def multiply(a: int, b: int):
    """A simple multiplication function."""
    return a * b

@mcp.tool
def divide(a: int, b: int):
    """A simple division function."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

@mcp.resource('info://simpleremoteserver')
def server_info():
    """Returns information about the server."""
    return {
        "name": "Simple Remote Server",
        "version": "1.0.0",
        "description": "A simple remote server for calculator operations.",
        "author": "Arun Pandey Laudari",
    }
    
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8080)
  



if __name__ == "__main__":
    mcp.run()
