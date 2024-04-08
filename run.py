from fastapi import FastAPI

# Create an instance of FastAPI
app = FastAPI()
# Define a route with GET method
@app.get("/")
async def read_root():
    return {"message": "Hello, World"}