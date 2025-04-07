import os
import sys
import base64
import csv
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from geopy.geocoders import Nominatim
from PIL import Image, ImageFile
import openai
import piexif
import ttkbootstrap as ttk
import re
from dotenv import load_dotenv

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

load_dotenv()
OPENAI_API_KEY = None
if os.path.exists(".env"):
    from dotenv import dotenv_values
    env_vars = dotenv_values(".env")
    OPENAI_API_KEY = env_vars.get("OPENAI_API_KEY")

root = ttk.Window(themename="darkly")
root.title("SmartPhotoMetadata")
root.geometry("500x260+0+0")

def ask_api_key():
    api_dialog = ttk.Toplevel(root)
    api_dialog.title("API Key Required")
    api_dialog.geometry("400x180")
    api_dialog.resizable(False, False)

    ttk.Label(api_dialog, text="Enter your OpenAI API Key:", bootstyle="info").pack(pady=10)

    api_key_var = tk.StringVar()
    api_entry = ttk.Entry(api_dialog, textvariable=api_key_var, show="*", width=40, bootstyle="dark")
    api_entry.pack(pady=5)
    api_entry.focus()

    def submit_key():
        global OPENAI_API_KEY
        OPENAI_API_KEY = api_key_var.get().strip()
        if OPENAI_API_KEY:
            with open(".env", "a") as env_file:
                env_file.write(f"\nOPENAI_API_KEY={OPENAI_API_KEY}\n")
            api_dialog.destroy()
        else:
            messagebox.showerror("Error", "API key is required to proceed.")

    ttk.Button(api_dialog, text="Submit", command=submit_key, bootstyle="success").pack(pady=15)

    api_dialog.transient(root)
    api_dialog.grab_set()
    root.wait_window(api_dialog)

if not OPENAI_API_KEY:
    ask_api_key()

openai.api_key = OPENAI_API_KEY

def update_status(message):
    status_label.config(text=message)
    root.update_idletasks()

def get_gps_coordinates(location_name):
    geolocator = Nominatim(user_agent="geo_exif_editor")
    location = geolocator.geocode(location_name)
    if location:
        return location.latitude, location.longitude
    return None, None

def clean_title(title):
    return re.sub(r'[「」]', '', title).strip()

def to_deg(value):
    d = int(value)
    m = int((value - d) * 60)
    s = round((value - d - m / 60) * 3600, 2)
    return ((d, 1), (m, 1), (int(s * 100), 100))

def set_gps_exif(image_path, lat, lon):
    update_status(f"Checking GPS data for {os.path.basename(image_path)}...")
    with Image.open(image_path) as img:
        exif_dict = piexif.load(img.info.get("exif", b"")) if "exif" in img.info else {"GPS": {}}

        if piexif.GPSIFD.GPSLatitude in exif_dict['GPS'] and piexif.GPSIFD.GPSLongitude in exif_dict['GPS']:
            update_status(f"GPS data already present in {os.path.basename(image_path)}, skipping GPS update.")
            return

        update_status(f"Adding GPS data to {os.path.basename(image_path)}...")
        if lat is not None and lon is not None:
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = to_deg(abs(lat))
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = to_deg(abs(lon))
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if lon >= 0 else 'W'

        exif_bytes = piexif.dump(exif_dict)
        img.save(image_path, "JPEG", exif=exif_bytes, quality=100)

def encode_image(image_path):
    with Image.open(image_path) as img:
        img.thumbnail((512, 512))
        temp_path = image_path + "_temp.jpg"
        img.save(temp_path, "JPEG", quality=85)
        with open(temp_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        os.remove(temp_path)
    return encoded

def get_gpt_title(image_path):
    update_status(f"Generating title for {os.path.basename(image_path)}...")
    client = openai.OpenAI()
    encoded_image = encode_image(image_path)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI specialized in generating creative photography titles in Japanese. Respond with only the title in Japanese, no additional text."},
            {"role": "user", "content": "この写真のための創造的で芸術的なタイトルを提供してください。"},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}", "detail": "low"}}
            ]}
        ],
    )
    return clean_title(response.choices[0].message.content.strip())

def extract_location_from_filename(filename):
    return re.sub(r'\d+', '', os.path.splitext(filename)[0]).strip()

def process_images():
    update_status("Processing images...")
    csv_path = os.path.join(folder_path.get(), "log.csv")

    processed_titles = set()
    if os.path.exists(csv_path):
        try:
            with open(csv_path, mode="r", newline="", encoding="utf-8-sig") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                header = next(csv_reader, None)
                for row in csv_reader:
                    if len(row) >= 2:
                        processed_titles.add(row[1].strip())
        except Exception as e:
            update_status(f"Error reading CSV: {e}")

    file_mode = "a" if os.path.exists(csv_path) else "w"
    with open(csv_path, mode=file_mode, newline="", encoding="utf-8-sig") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        if file_mode == "w":
            csv_writer.writerow(["Original Filename", "New Title"])

        for file in os.listdir(folder_path.get()):
            if file.lower().endswith(".jpg"):
                base_name = os.path.splitext(file)[0]
                if base_name in processed_titles:
                    update_status(f"Skipping already processed file: {file}")
                    continue

                image_path = os.path.join(folder_path.get(), file)

                location = extract_location_from_filename(file)
                if location:
                    lat, lon = get_gps_coordinates(location)
                    if lat and lon:
                        set_gps_exif(image_path, lat, lon)

                title = get_gpt_title(image_path)
                if title:
                    safe_title = re.sub(r'[\\/:*?"<>|]', '', title)
                    new_filename = os.path.join(folder_path.get(), safe_title.replace(" ", "_") + ".jpg")
                    if os.path.exists(new_filename):
                        base, ext = os.path.splitext(new_filename)
                        counter = 1
                        while os.path.exists(f"{base}_{counter}{ext}"):
                            counter += 1
                        new_filename = f"{base}_{counter}{ext}"
                    original_base_name = os.path.splitext(file)[0]
                    new_base_name = os.path.splitext(os.path.basename(new_filename))[0]
                    for sibling_file in os.listdir(folder_path.get()):
                        sibling_base, sibling_ext = os.path.splitext(sibling_file)
                        if sibling_base == original_base_name:
                            old_path = os.path.join(folder_path.get(), sibling_file)
                            new_path = os.path.join(folder_path.get(), new_base_name + sibling_ext)
                            counter = 1
                            while os.path.exists(new_path):
                                new_path = os.path.join(folder_path.get(), f"{new_base_name}_{counter}{sibling_ext}")
                                counter += 1

                            os.rename(old_path, new_path)

                    csv_writer.writerow([file, safe_title])
                    update_status(f"Processed: {file} → {safe_title}")
    update_status("Processing complete! Done.")

def start_processing_thread():
    processing_thread = threading.Thread(target=process_images)
    processing_thread.start()

ttk.Label(root, text="Select a folder with JPG images:", bootstyle="info").pack(pady=10)
folder_path = tk.StringVar(value=os.getenv("IMAGE_PATH", ""))

def select_folder():
    folder_selected = filedialog.askdirectory()
    folder_path.set(folder_selected)

ttk.Entry(root, textvariable=folder_path, width=50).pack(pady=5)
ttk.Button(root, text="Browse", command=select_folder, bootstyle="primary").pack(pady=5)
ttk.Button(root, text="Start Processing", command=start_processing_thread, bootstyle="success").pack(pady=20)

status_label = ttk.Label(root, text="", bootstyle="secondary")
status_label.pack(pady=5)

root.mainloop()
