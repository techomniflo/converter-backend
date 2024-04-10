from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import os
import uuid
import subprocess

app = FastAPI()

# Function to convert file using ImageMagick's convert command
def convert_file(input_file, output_file):
    try:
        subprocess.run(["convert", input_file, output_file], check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Conversion failed: {e}")

@app.post("/emf2png")
async def emf_to_png(file: UploadFile = File(...)):
    # Get the original file name without extension
    original_name = os.path.splitext(file.filename)[0]

    # Save the uploaded file temporarily
    temp_file = f"{uuid.uuid4()}.emf"
    with open(temp_file, "wb") as f:
        f.write(await file.read())

    # Convert EMF to PNG
    output_file = f"{original_name}.png"
    convert_file(temp_file, output_file)

    # Clean up the temporary files
    os.remove(temp_file)

    # Return the converted PNG file
    return FileResponse(output_file, media_type="image/png", filename=output_file)

@app.post("/xps2png")
async def xps_to_png(file: UploadFile = File(...)):
    # Get the original file name without extension
    original_name = os.path.splitext(file.filename)[0]

    # Save the uploaded file temporarily
    temp_file = f"{uuid.uuid4()}.xps"
    with open(temp_file, "wb") as f:
        f.write(await file.read())

    # Convert XPS to PNG
    output_file = f"{original_name}.png"
    convert_file(temp_file, output_file)

    # Clean up the temporary files
    os.remove(temp_file)

    # Return the converted PNG file
    return FileResponse(output_file, media_type="image/png", filename=output_file)

@app.post("/pdf2png")
async def pdf_to_png(file: UploadFile = File(...)):
    # Get the original file name without extension
    original_name = os.path.splitext(file.filename)[0]

    # Save the uploaded file temporarily
    temp_file = f"{uuid.uuid4()}.pdf"
    with open(temp_file, "wb") as f:
        f.write(await file.read())

    # Convert PDF to PNG
    output_file = f"{original_name}.png"
    convert_file(temp_file, output_file)

    # Clean up the temporary files
    os.remove(temp_file)

    # Return the converted PNG file
    return FileResponse(output_file, media_type="image/png", filename=output_file)

@app.get("/heartbeat")
async def heartbeat():
    return {"status": "up"}