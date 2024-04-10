from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import os
import uuid
import subprocess
import logging
from pathlib import Path

app = FastAPI()

results_folder = "results"
os.makedirs(results_folder, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to convert file using ImageMagick's convert command
def convert_file(input_file, output_file):
    try:
        subprocess.run(["convert", input_file, output_file], check=True)
        logger.info(f"Conversion successful: {input_file} to {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Conversion failed: {e}")
        raise Exception(f"Conversion failed: {e}")

# Function to check and manage the results folder size
def manage_folder_size():
    folder = Path(results_folder)
    # Get folder size
    folder_size = sum(f.stat().st_size for f in folder.glob('**/*') if f.is_file())
    max_size_bytes = 5 * 1024**3  # 5GB
    target_size_bytes = 4 * 1024**3  # Target size is 4GB

    if folder_size > max_size_bytes:
        logger.info(f"Folder size exceeds 5GB. Current size: {folder_size}. Purging old files...")
        files = sorted(folder.glob('*'), key=os.path.getmtime)
        while folder_size > target_size_bytes and files:
            oldest_file = files.pop(0)
            folder_size -= oldest_file.stat().st_size
            oldest_file.unlink()
            logger.info(f"Deleted {oldest_file} to reduce folder size.")
        logger.info("Folder size managed successfully.")

@app.post("/emf2png")
async def emf_to_png(file: UploadFile = File(...)):
    manage_folder_size()  # Ensure folder size is managed before processing new file
    original_name = os.path.splitext(file.filename)[0]
    temp_file = f"{uuid.uuid4()}.emf"
    with open(temp_file, "wb") as f:
        f.write(await file.read())
        logger.info(f"Temporarily saved file: {temp_file}")
    output_file = os.path.join(results_folder, f"{original_name}.png")
    convert_file(temp_file, output_file)
    os.remove(temp_file)
    logger.info(f"Deleted temporary file: {temp_file}")
    return FileResponse(output_file, media_type="image/png", filename=os.path.basename(output_file))

# Implement similar manage_folder_size() call in other endpoint functions

@app.get("/heartbeat")
async def heartbeat():
    logger.info("Heartbeat checked. Service is up.")
    return {"status": "up"}
