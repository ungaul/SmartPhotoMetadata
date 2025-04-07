import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFile
import piexif
import ttkbootstrap as ttk
from dotenv import load_dotenv
import webbrowser

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

# Load .env for folder path
env_path = ".env"
load_dotenv(env_path)

root = ttk.Window(themename="darkly")
root.title("Manual GPS Editor")
root.geometry("600x600+0+0")

folder_path = tk.StringVar(value=os.getenv("IMAGE_PATH", ""))
image_list = []
current_index = 0

# Widgets
image_label = None
lat_var = tk.StringVar()
lon_var = tk.StringVar()
status_label = None


def select_folder():
    global image_list, current_index
    folder_selected = filedialog.askdirectory()
    folder_path.set(folder_selected)
    image_list = [f for f in os.listdir(folder_selected) if f.lower().endswith(".jpg")]
    current_index = 0
    if image_list:
        load_image()
    else:
        messagebox.showinfo("Info", "No JPG images found in this folder.")


def load_gps_data(image_path):
    try:
        img = Image.open(image_path)
        exif_dict = piexif.load(img.info.get("exif", b""))
        gps = exif_dict.get("GPS", {})
        def conv(tag):
            return gps.get(tag, None)

        if conv(piexif.GPSIFD.GPSLatitude) and conv(piexif.GPSIFD.GPSLongitude):
            lat_ref = gps[piexif.GPSIFD.GPSLatitudeRef].decode()
            lon_ref = gps[piexif.GPSIFD.GPSLongitudeRef].decode()

            lat = dms_to_deg(gps[piexif.GPSIFD.GPSLatitude])
            lon = dms_to_deg(gps[piexif.GPSIFD.GPSLongitude])
            if lat_ref == 'S': lat = -lat
            if lon_ref == 'W': lon = -lon
            return lat, lon
    except:
        pass
    return None, None


def dms_to_deg(dms):
    d, m, s = dms
    return d[0]/d[1] + m[0]/m[1]/60 + s[0]/s[1]/3600


def deg_to_dms(deg):
    d = int(deg)
    m_float = abs((deg - d) * 60)
    m = int(m_float)
    s = round((m_float - m) * 60, 6)
    return ((d,1), (m,1), (int(s*1000000),1000000))


def open_map_in_browser():
    try:
        lat = float(lat_var.get())
        lon = float(lon_var.get())
        url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=15/{lat}/{lon}"
        webbrowser.open(url)
    except ValueError:
        messagebox.showerror("Invalid Input", "Latitude and Longitude must be valid numbers.")


def save_and_next():
    global current_index
    if not image_list:
        return
    file = image_list[current_index]
    image_path = os.path.join(folder_path.get(), file)

    try:
        lat = float(lat_var.get())
        lon = float(lon_var.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Latitude and Longitude must be valid numbers.")
        return

    img = Image.open(image_path)
    exif_dict = piexif.load(img.info.get("exif", b"")) if "exif" in img.info else {"GPS": {}}

    exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = deg_to_dms(abs(lat))
    exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = deg_to_dms(abs(lon))
    exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
    exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if lon >= 0 else 'W'

    exif_bytes = piexif.dump(exif_dict)
    img.save(image_path, "jpeg", exif=exif_bytes)

    if current_index + 1 < len(image_list):
        current_index += 1
        load_image()
    else:
        messagebox.showinfo("Done", "You have reached the end of the folder.")


def load_image():
    if not image_list:
        return
    file = image_list[current_index]
    image_path = os.path.join(folder_path.get(), file)
    img = Image.open(image_path)
    img.thumbnail((400, 400))
    img_tk = ImageTk.PhotoImage(img)

    image_label.config(image=img_tk)
    image_label.image = img_tk

    lat, lon = load_gps_data(image_path)
    lat_var.set(str(lat) if lat else "")
    lon_var.set(str(lon) if lon else "")
    status_label.config(text=f"{file} ({current_index+1}/{len(image_list)})")


# UI Layout
ttk.Label(root, text="Select a folder with JPG images:", bootstyle="info").pack(pady=10)
ttk.Entry(root, textvariable=folder_path, width=60).pack(pady=5)
ttk.Button(root, text="Browse", command=select_folder, bootstyle="primary").pack(pady=5)

image_label = ttk.Label(root)
image_label.pack(pady=10)

coord_frame = ttk.Frame(root)
coord_frame.pack(pady=5)
ttk.Label(coord_frame, text="Latitude:").grid(row=0, column=0, padx=0)
ttk.Entry(coord_frame, textvariable=lat_var, width=20).grid(row=0, column=1, padx=20)
ttk.Label(coord_frame, text="Longitude:").grid(row=0, column=2, padx=0)
ttk.Entry(coord_frame, textvariable=lon_var, width=20).grid(row=0, column=3, padx=20)

button_frame = ttk.Frame(root)
button_frame.pack(pady=5)
ttk.Button(button_frame, text="Skip / Save", command=save_and_next, bootstyle="success").grid(row=0, column=0, padx=10)
ttk.Button(button_frame, text="Open Maps", command=open_map_in_browser, bootstyle="info").grid(row=0, column=1, padx=10)

status_label = ttk.Label(root, text="")
status_label.pack(pady=5)

root.mainloop()