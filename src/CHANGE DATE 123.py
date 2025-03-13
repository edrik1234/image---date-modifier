import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
import datetime
import re
import pytesseract
# Manually set the path to Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"




# === Global Variables === #
selected_area = None
image_path = ""
output_path = "updated_image.png"
log_file = "modification_log.txt"

# === Function to Load Image === #
def load_image():
    global image_path
    file_path = filedialog.askopenfilename(title="Select Image File", filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")])
    if not file_path:
        return None
    image_path = file_path
    return cv2.imread(image_path)

# === Function to Auto-Detect Date Area Using OCR === #
def detect_date_text(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    extracted_text = pytesseract.image_to_string(gray)
    
    date_pattern = re.compile(r"\d{1,2}/\d{1,2}/\d{4}.*?\d{1,2}:\d{2}")  
    matches = date_pattern.findall(extracted_text)

    if matches:
        return matches[0]  # Return the first detected date
    return None

# === Function to Select Area Manually === #
def select_area():
    global selected_area
    img = cv2.imread(image_path)
    cv2.imshow("Select Date Area (Click and Drag)", img)
    r = cv2.selectROI("Select Date Area (Click and Drag)", img, showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()
    if r[2] > 0 and r[3] > 0:
        selected_area = (r[0], r[1], r[0] + r[2], r[1] + r[3])

# === Function to Get User-Defined Date === #
def get_user_date():
    new_date = simpledialog.askstring("Enter New Date ", "Enter the new date (Format: MM/DD/YYYY HH:MM):")
    return new_date.strip() if new_date else None

# === Function to Detect Text and Background Colors === #
def detect_colors(roi):
    roi_reshaped = roi.reshape(-1, 3)
    colors, counts = np.unique(roi_reshaped, axis=0, return_counts=True)
    
    background_color = colors[np.argmax(counts)]
    text_color = colors[np.argmin(counts)]

    return tuple(map(int, text_color[::-1])), tuple(map(int, background_color[::-1]))

# === Function to Replace the Text in the Image === #
def replace_text(image, x1, y1, x2, y2, new_text):
    roi = image[y1:y2, x1:x2]
    text_color, bg_color = detect_colors(roi)

    image_pil = Image.open(image_path)
    draw = ImageDraw.Draw(image_pil)

    font_size = 5
    while True:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
        text_width, text_height = draw.textbbox((0, 0), new_text, font=font)[2:]
        if text_width >= (x2 - x1) or text_height >= (y2 - y1):
            break
        font_size += 1
    
    font_size -= 1
    font = ImageFont.truetype("arial.ttf", font_size)
    
    text_x = x1 + (x2 - x1 - text_width) // 2
    text_y = y1 + (y2 - y1 - text_height) // 2

    draw.rectangle([x1, y1, x2, y2], fill=bg_color)
    draw.text((text_x, text_y), new_text, font=font, fill=text_color)

    return image_pil

# === Function to Save and Log Changes === #
def save_and_log(image_pil, old_text, new_text):
    image_pil.save(output_path)
    with open(log_file, "a") as log:
        log.write(f"[{datetime.datetime.now()}] Changed '{old_text}' to '{new_text}' in {image_path}\n")
    messagebox.showinfo("Success", f"Updated image saved as {output_path}")

# === Main Program Flow === #
def main():
    global image_path, selected_area
    image = load_image()
    if image is None:
        return

    detected_text = detect_date_text(image)
    
    if detected_text:
        user_choice = messagebox.askyesno("Auto-Detect", f"Detected date: {detected_text}. Do you want to replace it?")
        if not user_choice:
            select_area()
    else:
        messagebox.showinfo("Manual Selection", "No date detected. Please select the area manually.")
        select_area()

    if selected_area is None:
        messagebox.showerror("Error", "No area selected. Exiting program.")
        return

    new_date = get_user_date()
    if not new_date:
        messagebox.showerror("Error", "No new date provided. Exiting program.")
        return

    x1, y1, x2, y2 = selected_area
    image_pil = replace_text(image, x1, y1, x2, y2, new_date)
    
    save_and_log(image_pil, detected_text if detected_text else "Manual Selection", new_date)
    image_pil.show()

# === Run the GUI and Main Function === #
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    main()
