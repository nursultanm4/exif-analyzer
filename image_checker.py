import os
import exifread
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import webbrowser

def get_decimal_from_dms(dms, ref):
    degrees = float(dms.values[0].num) / float(dms.values[0].den)
    minutes = float(dms.values[1].num) / float(dms.values[1].den)
    seconds = float(dms.values[2].num) / float(dms.values[2].den)
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def extract_gps(metadata):
    try:
        lat = metadata.get('GPS GPSLatitude')
        lat_ref = metadata.get('GPS GPSLatitudeRef')
        lon = metadata.get('GPS GPSLongitude')
        lon_ref = metadata.get('GPS GPSLongitudeRef')
        if lat and lat_ref and lon and lon_ref:
            lat_decimal = get_decimal_from_dms(lat, lat_ref.values)
            lon_decimal = get_decimal_from_dms(lon, lon_ref.values)
            return lat_decimal, lon_decimal
    except Exception:
        pass
    return None, None

def check_metadata(img_path):
    with open(img_path, 'rb') as image_file:
        metadata = exifread.process_file(image_file)

    if not metadata:
        return "No metadata, perhaps data was changed", None, None

    result = []
    important_tags = [
        'Image Make', 'Image Model', 'EXIF DateTimeOriginal',
        'GPSLatitude', 'GPSLongitude', 'Software'
    ]
    for tag in important_tags:
        if tag in metadata:
            result.append(f"{tag}: {metadata[tag]}")
        else:
            result.append(f"{tag}: No data")

    lat, lon = extract_gps(metadata)
    return "\n".join(result), lat, lon

def check_steganography(img_path):
    try:
        image = Image.open(img_path)
        pixels = image.load()

        binary_message = ""
        for y in range(image.height):
            for x in range(image.width):
                pixel = pixels[x, y]
                for color in range(3):  
                    binary_message += str(pixel[color] & 1)  

        byte_message = [binary_message[i:i+8] for i in range(0, len(binary_message), 8)]
        decoded_message = ''.join(chr(int(byte, 2)) for byte in byte_message if len(byte) == 8)

        decoded_message = decoded_message.split('ÿÿ')[0]

        readable_message = ''.join(char for char in decoded_message if char.isprintable())

        if readable_message:
            return f"Hidden information: {readable_message}"
        else:
            return "No hidden information found."

    except Exception as e:
        return f"Error during analysis: {str(e)}"

def save_the_results(metadata_result, stego_result):
    results = {
        "metadata": metadata_result,
        "steganography": stego_result
    }
    with open("metadata_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
    if file_path:
        img_path.set(file_path)
        display_image(file_path)
        gps_label.config(text="")
        maps_button.pack_forget()

def open_in_maps():
    if hasattr(open_in_maps, "coords") and open_in_maps.coords:
        lat, lon = open_in_maps.coords
        url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        webbrowser.open(url)

def analyze_image(img_path):
    if not os.path.exists(img_path):
        messagebox.showerror("Error", "File not found. Please check the path.")
        return

    progress.start()

    metadata_result, lat, lon = check_metadata(img_path)
    stego_result = check_steganography(img_path)
    save_the_results(metadata_result, stego_result)
    progress.stop()

    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, metadata_result + "\n\n" + stego_result)
    result_text.config(state=tk.DISABLED)

    if lat is not None and lon is not None:
        gps_label.config(text=f"Coordinates: {lat:.6f}, {lon:.6f}")
        open_in_maps.coords = (lat, lon)
        maps_button.pack(pady=5)
    else:
        gps_label.config(text="No GPS coordinates found")
        maps_button.pack_forget()

def display_image(img_path):
    try:
        img = Image.open(img_path)
        img.thumbnail((350, 350))
        img_tk = ImageTk.PhotoImage(img)
        image_label.config(image=img_tk)
        image_label.image = img_tk
        image_label.config(text="")
    except Exception:
        image_label.config(image="", text="Cannot display image")

def create_the_gui():
    root = tk.Tk()
    root.title("Image Metadata & Steganography Checker")
    root.geometry("800x600")

    label = tk.Label(root, text="Select an image for analysis", font=("Arial", 16))
    label.pack(pady=10)

    global progress
    progress = ttk.Progressbar(root, length=400, mode='indeterminate')
    progress.pack(pady=10)

    global img_path
    img_path = tk.StringVar()

    entry = tk.Entry(root, textvariable=img_path, width=70, font=("Arial", 12))
    entry.pack(pady=5)
    open_button = tk.Button(root, text="Open file", font=("Arial", 12), width=18, command=open_file)
    open_button.pack(pady=5)

    analyze_button = tk.Button(
        root, text="Analyze", font=("Arial", 12), width=18,
        command=lambda: analyze_image(img_path.get())
    )
    analyze_button.pack(pady=5)

    global image_label
    image_label = tk.Label(root, text="No image selected", width=50, height=16, bg="#f0f0f0", relief=tk.SUNKEN)
    image_label.pack(pady=10)

    global gps_label
    gps_label = tk.Label(root, text="", font=("Arial", 12))
    gps_label.pack(pady=2)

    global maps_button
    maps_button = tk.Button(root, text="Open in Maps", font=("Arial", 12), width=18, command=open_in_maps)
    maps_button.pack_forget()

    global result_text
    result_text = tk.Text(root, height=14, width=90, font=("Arial", 12), state=tk.DISABLED)
    result_text.pack(pady=10)

    quit_button = tk.Button(root, text="Exit", font=("Arial", 12), width=18, command=root.quit)
    quit_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_the_gui()
