import struct
import os
import glob

def extract_emf_records(emfspool_file):
    with open(emfspool_file, 'rb') as file:
        data = file.read()

    offset = 0
    while offset < len(data):
        if offset + 8 > len(data):
            break
        record_id = struct.unpack('<I', data[offset:offset+4])[0]
        record_size = struct.unpack('<I', data[offset+4:offset+8])[0]

        if record_id == 0x0000000C:  # EMRI_METAFILE_DATA
            emf_data = data[offset+8:offset+record_size+8]
            yield emf_data

        offset += record_size
        if record_size % 4 != 0:
            offset += 4 - (record_size % 4)

def save_emf_records(emfspool_file, output_folder):
    base_name = os.path.basename(emfspool_file).split('.')[0]
    os.makedirs(output_folder, exist_ok=True)
    count=0
    for i, emf_data in enumerate(extract_emf_records(emfspool_file)):
        output_file = os.path.join(output_folder, f"{base_name}_{i}.emf")
        with open(output_file, 'wb') as file:
            file.write(emf_data)
        count+=1
        print(f"Saved EMF record {i} to {output_file}")
    return count