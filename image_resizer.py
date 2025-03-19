import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import io

def resize_image(input_path, output_path, min_size=None, target_size_mb=None):
    if min_size is None and target_size_mb is not None:
        # Calculate the scaling factor based on the target size in MB
        target_size_bytes = target_size_mb * 1024 * 1024
        img = Image.open(input_path)
        width, height = img.size
        current_bytes = width * height * 3  # Approximate size in bytes (RGB)
        
        # Calculate scaling factor (square root because we're scaling in 2 dimensions)
        scale_factor = (target_size_bytes / current_bytes) ** 0.5
        
        # Use this to determine minimum size while maintaining aspect ratio
        min_size = min(width, height) * scale_factor
    elif min_size is None:
        raise ValueError("Both min_size and target_size_mb cannot be None")

    # Ensure that min_size is a valid number
    if not isinstance(min_size, (int, float)):
        raise ValueError(f"Invalid min_size value: {min_size}")

    """Resize an image while maintaining aspect ratio. Optionally compress to a target file size."""
    image = Image.open(input_path)
    format = image.format  # Preserve original format

    # Scale image based on shortest side
    width, height = image.size
    scale_factor = min_size / min(width, height)
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # Ensure that the new width and height are at least 1 pixel
    new_width = max(1, new_width)
    new_height = max(1, new_height)

    print(f"min_size: {min_size}, target_size_mb: {target_size_mb}")
    print(f"Resizing image to {new_width}x{new_height} pixels")

    resized_image = image.resize((new_width, new_height), Image.LANCZOS)

    # Adjust compression if a file size limit is set
    if target_size_mb:
        quality = 95  # Start with high quality
        temp_output = io.BytesIO()

        while quality > 10:
            temp_output.seek(0)
            resized_image.save(temp_output, format=format, quality=quality)
            file_size = len(temp_output.getvalue()) / (1024 * 1024)  # Convert to MB

            if file_size <= target_size_mb:
                break
            quality -= 5  # Reduce quality if the file is too large

        temp_output.seek(0)
        with open(output_path, "wb") as f:
            f.write(temp_output.getvalue())
    else:
        resized_image.save(output_path, format=format)

    return resized_image


class ImageResizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Image Resizer")

        # Input & Output folder selection
        tk.Label(root, text="Input Folder:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.input_folder_entry = tk.Entry(root, width=50)
        self.input_folder_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse", command=self.select_input_folder).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(root, text="Output Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.output_folder_entry = tk.Entry(root, width=50)
        self.output_folder_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse", command=self.select_output_folder).grid(row=1, column=2, padx=5, pady=5)

        # Resizing mode selection - Modified to align buttons together on the left
        tk.Label(root, text="Resize Mode:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        # Create a frame to hold the radio buttons
        radio_frame = tk.Frame(root)
        radio_frame.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        self.resize_mode = tk.StringVar(value="pixels")
        tk.Radiobutton(radio_frame, text="Pixels", variable=self.resize_mode, value="pixels", 
                      command=self.toggle_options).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(radio_frame, text="File Size (MB)", variable=self.resize_mode, value="size", 
                      command=self.toggle_options).pack(side=tk.LEFT)

        # Pixel size input
        tk.Label(root, text="Shortest Side (px):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.pixel_size_entry = tk.Entry(root, width=10)
        self.pixel_size_entry.insert(0, "1000")
        self.pixel_size_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # File size input
        tk.Label(root, text="Target Size (MB):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.file_size_entry = tk.Entry(root, width=10)
        self.file_size_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        self.file_size_entry.config(state="disabled")  # Disabled initially

        # Process Button
        self.process_button = tk.Button(root, text="Resize Images", command=self.process_images, bg="green", fg="white")
        self.process_button.grid(row=5, column=0, columnspan=3, pady=10)

    def toggle_options(self):
        """Enable/Disable input fields based on selected resize mode."""
        if self.resize_mode.get() == "pixels":
            self.pixel_size_entry.config(state="normal")
            self.file_size_entry.config(state="disabled")
        else:
            self.pixel_size_entry.config(state="disabled")
            self.file_size_entry.config(state="normal")

    def select_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder_entry.delete(0, tk.END)
            self.input_folder_entry.insert(0, folder)

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder_entry.delete(0, tk.END)
            self.output_folder_entry.insert(0, folder)

    def process_images(self):
        input_folder = Path(self.input_folder_entry.get().strip())
        output_folder = Path(self.output_folder_entry.get().strip())

        if not input_folder.is_dir():
            messagebox.showerror("Error", "Invalid input folder")
            return
        if not output_folder.is_dir():
            output_folder.mkdir(parents=True, exist_ok=True)

        # Get resizing parameters
        resize_mode = self.resize_mode.get()
        min_size = int(self.pixel_size_entry.get()) if resize_mode == "pixels" else None
        target_size_mb = float(self.file_size_entry.get()) if resize_mode == "size" else None

        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif", ".webp"}
        image_files = [f for f in input_folder.iterdir() if f.suffix.lower() in valid_extensions]

        if not image_files:
            messagebox.showerror("Error", "No images found in the selected folder")
            return

        for image_file in image_files:
            output_file = output_folder / image_file.name
            resize_image(image_file, output_file, min_size=min_size, target_size_mb=target_size_mb)

        messagebox.showinfo("Success", "All images have been resized!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageResizerApp(root)
    root.mainloop()
