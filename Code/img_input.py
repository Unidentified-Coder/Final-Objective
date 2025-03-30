import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import shutil
import os

# initialize variables before being used inside function
label = None
status_label = None
img_display = None

# Function to take in an image as input
def img_input():
    
    # Allow different image file types to be accepted
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
    
    #  
    if file_path:
        global label
        global status_label
        global img_display
        
        if label is not None:
            label.config(image=img_display)
            image = Image.open(file_path)
            image.thumbnail((600, 600)) 
        if img_display is not None:
            img_display = ImageTk.PhotoImage(image)
            label.image = img_display  
        
        # Save the file to a shared directory
        img_path = "image-Folder/shared_image.png"  
        os.makedirs("image-Folder", exist_ok=True)  
        shutil.copy(file_path, img_path)
        if status_label is not None:
            status_label.config(text=f"Image saved as {img_path}", fg="black")

# Tkinter GUI setup
    root = tk.Tk()
    root.title("Image Uploader")

    btn = tk.Button(root, text="Upload Image", command=img_input)
    btn.pack()

    label = tk.Label(root)
    label.pack()

    status_label = tk.Label(root, text="No image uploaded", fg="red")
    status_label.pack()

    root.mainloop()
