from fastapi import FastAPI, File, UploadFile,HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import subprocess
import logging
from pathlib import Path

from spl_to_emf import save_emf_records
app = FastAPI()

input_folder,results_folder = "input","results"
os.makedirs(results_folder, exist_ok=True)
os.makedirs(input_folder,exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to convert file using escpos-tools
def convert_escpos_file(input_file, output_dir):
    try:
        subprocess.run(["docker", "run", "--rm", "-v", f"{os.path.dirname(input_file)}:/data", "escpos-tools",
                        "escimages.php", "--file", f"/data/{os.path.basename(input_file)}",
                        "--png", "--output-dir", f"/data/{output_dir}"], check=True)
        logger.info(f"Conversion successful: {input_file} to {output_dir}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Conversion failed: {e}")
        raise Exception(f"Conversion failed: {e}")

# Function to convert file using ImageMagick's convert command
def convert_file(input_file, output_file):
    try:
        subprocess.run(["convert","-density","300", input_file, "-append",output_file], check=True)
        logger.info(f"Conversion successful: {input_file} to {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Conversion failed: {e}")
        raise Exception(f"Conversion failed: {e}")
def run_command(command):
    try:
        subprocess.run(command, check=True)
        logger.info(f"commnad successful: {str(command)}")
    except subprocess.CalledProcessError as e:
        logger.error(f"command failed: {e}")
        raise Exception(f"command failed: {e}")

def remove_file_from_list(files):
    for file_path in files:
        try:
            # Attempt to remove the file
            os.remove(file_path)
            logger.info(f"File '{file_path}' removed successfully.")
        except OSError as e:
            # If an error occurs (e.g., file not found), print the error message
            logger.error(f"Error: {file_path} : {e.strerror}")



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

@app.post("/spl2png")
async def spl_to_png(file: UploadFile = File(...)):
    manage_folder_size()  # Ensure folder size is managed before processing new file
    original_name = os.path.splitext(file.filename)[0]
    temp_uuid=uuid.uuid4()
    temp_file = f"{temp_uuid}.emf"
    with open(temp_file, "wb") as f:
        f.write(await file.read())
        logger.info(f"Temporarily saved file: {temp_file}")
    output_file = os.path.join(results_folder, f"{temp_uuid}.png")
    emf_files_count=save_emf_records(temp_file,input_folder)
    input_emf_file=[os.path.join(input_folder,temp_file[:-4] + "_" + str(i)+".emf")for i in range(emf_files_count)]
    command=["wine","ImageMagick-7.1.1-31-portable-Q16-HDRI-x86/convert.exe","-density","300"] + input_emf_file +  ["-append",output_file]
    run_command(command=command)
    remove_file_from_list(input_emf_file+[temp_file])
    logger.info(f"Deleted temporary file: {temp_file}")
    return FileResponse(output_file, media_type="image/png", filename=os.path.basename(f"{original_name}.png"))

@app.post("/pdf2png")
async def pdf_to_png(file: UploadFile = File(...)):
    manage_folder_size()  # Ensure folder size is managed before processing new file
    original_name = os.path.splitext(file.filename)[0]
    temp_file = f"{uuid.uuid4()}.pdf"
    with open(temp_file, "wb") as f:
        f.write(await file.read())
        logger.info(f"Temporarily saved file: {temp_file}")
    output_file = os.path.join(results_folder, f"{original_name}.png")
    convert_file(temp_file, output_file)
    os.remove(temp_file)
    logger.info(f"Deleted temporary file: {temp_file}")
    return FileResponse(output_file, media_type="image/png", filename=os.path.basename(output_file))

@app.post("/xps2png")
async def xps_to_png(file: UploadFile = File(...)):
    # Manage folder size
    manage_folder_size()

    # Generate temporary UUID for file
    temp_uuid = uuid.uuid4()

    # Save uploaded XPS file temporarily
    temp_file = os.path.join(input_folder, f"{temp_uuid}.xps")
    with open(temp_file, "wb") as f:
        f.write(await file.read())
    logger.info(f"Temporarily saved file: {temp_file}")

    # Convert XPS to PNG
    output_file = os.path.join(results_folder, str(temp_uuid))
    xpstopng_command = ["xpstopng", temp_file, output_file]
    run_command(command=xpstopng_command)

    # Vertically append all PNG files into one
    all_input_files = os.path.join(results_folder, f"{temp_uuid}-*.png")
    output_file += ".png"
    convert_command = ["convert", "-density", "300", all_input_files, "-append", output_file]
    run_command(command=convert_command)

    # Clean up temporary XPS file
    os.remove(temp_file)
    logger.info(f"Deleted temporary file: {temp_file}")

    # Return PNG file
    original_name = os.path.splitext(file.filename)[0]
    return FileResponse(output_file, media_type="image/png", filename=os.path.basename(original_name))


@app.post("/pdf2txt")
@app.post("/xps2txt")
async def extract_text_from_xps_pdf(file: UploadFile = File(...)):

    # Check file extension
    allowed_extensions = {"pdf", "xps"}
    file_extension = file.filename.split(".")[-1]
    if file_extension.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF and XPS are supported.")
    
    # Manage folder size
    manage_folder_size()

    # Generate temporary UUID for file
    temp_uuid = uuid.uuid4()

    # Save uploaded file temporarily
    temp_file = os.path.join(input_folder, f"{temp_uuid}.{file_extension}")
    with open(temp_file, "wb") as f:
        f.write(await file.read())
    logger.info(f"Temporarily saved file: {temp_file}")

    # Convert XPS to PNG
    output_file_path = os.path.join(results_folder, f"{temp_uuid}.txt")
    command = ["mutool", "draw", "-F", "txt", temp_file]
    try:
        with open(output_file_path, 'w') as output_file:
            subprocess.call(command, stdout=output_file)
    except subprocess.CalledProcessError as e:
        logger.error(f"command failed: {e}")
        raise Exception(f"command failed: {e}")
    
    original_name = os.path.splitext(file.filename)[0]
    return FileResponse(output_file_path, media_type="text/plain", filename=os.path.basename(original_name))

# Function to append images vertically
def append_images_vertically(image_files, output_file):
    try:
        subprocess.run(["convert", "-append"] + image_files + [output_file], check=True)
        logger.info(f"Images appended vertically: {image_files} to {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Image append failed: {e}")
        raise Exception(f"Image append failed: {e}")

@app.post("/escpos2png")
async def escpos_to_png(file: UploadFile = File(...)):
    manage_folder_size()  # Ensure folder size is managed before processing new file
    original_name = os.path.splitext(file.filename)[0]
    temp_file = f"{uuid.uuid4()}.bin"
    with open(temp_file, "wb") as f:
        f.write(await file.read())
    logger.info(f"Temporarily saved file: {temp_file}")

    output_dir = os.path.join(results_folder, original_name)
    os.makedirs(output_dir, exist_ok=True)
    convert_escpos_file(temp_file, output_dir)
    os.remove(temp_file)
    logger.info(f"Deleted temporary file: {temp_file}")

    output_files = sorted(Path(output_dir).glob("*.png"))
    if len(output_files) > 1:
        output_file = os.path.join(results_folder, f"{original_name}.png")
        append_images_vertically([str(f) for f in output_files], output_file)
    else:
        output_file = output_files[0]

    return FileResponse(output_file, media_type="image/png", filename=os.path.basename(output_file))

@app.get("/heartbeat")
async def heartbeat():
    logger.info("Heartbeat checked. Service is up.")
    return {"status": "up"}
