import os
import shutil  # Add this import at the top
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD  # Import tkinterdnd2
from PIL import Image, ImageTk
import io


def resize_image(input_path, output_path, min_size=None, target_size_mb=None):
    """Resize an image while maintaining aspect ratio. Optionally compress to a target file size."""
    if min_size is None and target_size_mb is not None:
        # Calculate the scaling factor based on the target size in MB
        # Fix: Convert target_size_mb directly without multiplication to address the factor of 10 issue
        target_size_bytes = target_size_mb * 1024 * 1024  # This is correct as is
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

    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Adjust compression if a file size limit is set
    if target_size_mb:
        quality = 95  # Start with high quality
        temp_output = io.BytesIO()

        while quality > 10:
            temp_output.seek(0)
            temp_output.truncate(0)  # Clear previous data
            
            # Save with appropriate format-specific parameters
            if format == 'JPEG':
                resized_image.save(temp_output, format=format, quality=quality)
            elif format == 'PNG':
                resized_image.save(temp_output, format=format, optimize=True)
            elif format == 'WEBP':
                resized_image.save(temp_output, format=format, quality=quality)
            elif format == 'HEIF' or format == 'HEIC':
                resized_image.save(temp_output, format=format, quality=quality)
            else:
                # Default save method for other formats
                resized_image.save(temp_output, format=format)
                
            file_size = len(temp_output.getvalue()) / (1024 * 1024)  # Convert to MB
            print(f"Quality: {quality}, Size: {file_size:.2f} MB, Target: {target_size_mb:.2f} MB")

            if file_size <= target_size_mb:
                break
            quality -= 5  # Reduce quality if the file is too large

        temp_output.seek(0)
        with open(output_path, "wb") as f:
            f.write(temp_output.getvalue())
    else:
        resized_image.save(output_path, format=format)

    return resized_image


class DragDropEntry(ttk.Entry):
    """Custom Entry widget that supports drag and drop."""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Enable drag and drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop)

    def drop(self, event):
        """Handle dropped files."""
        data = event.data
        
        # Remove unnecessary curly braces from file paths
        if data.startswith('{') and data.endswith('}'):
            data = data[1:-1]

        # Update the entry with the dropped path
        self.delete(0, tk.END)
        self.insert(0, data.strip())


class UndoManager:
    """Manage undo operations for batch processing."""
    def __init__(self):
        self.last_operations = []

    def add_operation(self, input_file, output_file):
        """Add an operation to the undo stack."""
        self.last_operations.append((input_file, output_file))

    def undo_last_batch(self):
        """Undo the last batch of operations."""
        if not self.last_operations:
            return False
        
        for _, output_file in self.last_operations:
            try:
                os.remove(output_file)
            except Exception as e:
                print(f"Error removing file {output_file}: {str(e)}")
        
        self.last_operations.clear()
        return True


# Ensure the main window uses TkinterDnD for drag-and-drop support
class ImageResizerApp:
    def __init__(self, root):
        self.root = root
        self.undo_manager = UndoManager()
        
        # Input & Output folder selection
        tk.Label(root, text="Input Folder:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.input_folder_entry = DragDropEntry(root, width=50)
        self.input_folder_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse", command=self.select_input_folder).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(root, text="Output Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.output_folder_entry = DragDropEntry(root, width=50)
        self.output_folder_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse", command=self.select_output_folder).grid(row=1, column=2, padx=5, pady=5)

        # Drag and drop info label
        dnd_label = tk.Label(root, text="Tip: You can drag & drop folders into the input fields", 
                             font=("Arial", 8, "italic"), fg="gray")
        dnd_label.grid(row=2, column=0, columnspan=3, padx=5, pady=(0, 5))

        # Resizing mode selection
        tk.Label(root, text="Resize Mode:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        
        # Create a frame to hold the radio buttons
        radio_frame = tk.Frame(root)
        radio_frame.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        self.resize_mode = tk.StringVar(value="pixels")
        tk.Radiobutton(radio_frame, text="Pixels", variable=self.resize_mode, value="pixels", 
                      command=self.toggle_options).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(radio_frame, text="File Size (MB)", variable=self.resize_mode, value="size", 
                      command=self.toggle_options).pack(side=tk.LEFT)

        # Pixel size input
        tk.Label(root, text="Shortest Side (px):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.pixel_size_entry = tk.Entry(root, width=10)
        self.pixel_size_entry.insert(0, "1000")
        self.pixel_size_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        # File size input
        tk.Label(root, text="Target Size (MB):").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.file_size_entry = tk.Entry(root, width=10)
        self.file_size_entry.insert(0, "1.0")  # Default value for clarity
        self.file_size_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        self.file_size_entry.config(state="disabled")  # Disabled initially

        # Format information
        supported_formats = "Supported formats: JPG, JPEG, PNG, BMP, TIFF, GIF, WEBP, HEIC, HEIF, AVIF"
        format_label = tk.Label(root, text=supported_formats, font=("Arial", 8), fg="dark blue")
        format_label.grid(row=6, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="w")

        # Progress bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Process Button
        self.process_button = tk.Button(root, text="Resize Images", command=self.process_images, bg="green", fg="white")
        self.process_button.grid(row=8, column=0, columnspan=3, pady=10)

        # Undo Button
        self.undo_button = tk.Button(root, text="Undo Last Batch", command=self.undo_last_batch, 
                                   state="disabled", bg="orange", fg="white")
        self.undo_button.grid(row=8, column=3, pady=10, padx=5)

        # Status label
        self.status_label = tk.Label(root, text="Ready", font=("Arial", 9))
        self.status_label.grid(row=9, column=0, columnspan=3, padx=5, pady=5)

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

    def get_output_filename(self, input_path, resize_mode, min_size=None, target_size_mb=None):
        """Generate output filename with appropriate suffix"""
        filename, ext = os.path.splitext(input_path)
        if resize_mode == "pixels":
            suffix = f"_w{min_size}px"
        else:
            suffix = f"_{target_size_mb}MB"
        return f"{filename}{suffix}{ext}"

    def process_images(self):
        input_path = self.input_folder_entry.get().strip()
        output_folder = self.output_folder_entry.get().strip()
        
        # Clear previous undo operations
        self.undo_manager.last_operations.clear()
        
        # Handle multiple input files
        input_files = []
        if ',' in input_path:  # Multiple files
            paths = [p.strip() for p in input_path.split(',')]
            for path in paths:
                if os.path.isfile(path):
                    input_files.append(path)
        elif os.path.isfile(input_path):  # Single file
            input_files.append(input_path)
        elif os.path.isdir(input_path):  # Directory
            valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", 
                              ".tif", ".gif", ".webp", ".heic", ".heif", ".avif"}
            for file in os.listdir(input_path):
                file_path = os.path.join(input_path, file)
                if os.path.isfile(file_path) and os.path.splitext(file)[1].lower() in valid_extensions:
                    input_files.append(file_path)
        
        if not input_files:
            messagebox.showerror("Error", "No valid input files found")
            return
            
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Get resizing parameters
        resize_mode = self.resize_mode.get()
        
        try:
            if resize_mode == "pixels":
                min_size = int(self.pixel_size_entry.get())
                target_size_mb = None
            else:
                min_size = None
                target_size_mb = float(self.file_size_entry.get())
                
                if target_size_mb <= 0:
                    messagebox.showerror("Error", "Target size must be greater than 0 MB")
                    return
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")
            return

        # Process images
        self.process_button.config(state="disabled")
        self.progress["maximum"] = len(input_files)
        self.progress["value"] = 0
        processed_count = 0
        failed_count = 0
        
        for input_file in input_files:
            try:
                self.status_label.config(text=f"Processing: {os.path.basename(input_file)}")
                self.root.update()
                
                output_file = os.path.join(output_folder, 
                    os.path.basename(self.get_output_filename(input_file, resize_mode, min_size, target_size_mb)))
                
                resize_image(input_file, output_file, min_size=min_size, target_size_mb=target_size_mb)
                self.undo_manager.add_operation(input_file, output_file)
                processed_count += 1
            except Exception as e:
                print(f"Error processing {input_file}: {str(e)}")
                failed_count += 1
            
            self.progress["value"] = processed_count + failed_count
            self.root.update()

        # Re-enable buttons
        self.process_button.config(state="normal")
        self.undo_button.config(state="normal")
        
        # Show completion message
        if failed_count > 0:
            self.status_label.config(text=f"Completed: {processed_count} processed, {failed_count} failed")
            messagebox.showinfo("Processing Complete", 
                              f"{processed_count} images were successfully resized.\n{failed_count} images failed processing.")
        else:
            self.status_label.config(text=f"Completed: {processed_count} images processed")
            messagebox.showinfo("Success", "All images have been resized!")

    def undo_last_batch(self):
        """Undo the last batch of operations"""
        if self.undo_manager.undo_last_batch():
            self.status_label.config(text="Last batch operation undone")
            self.undo_button.config(state="disabled")
            messagebox.showinfo("Undo Complete", "The last batch operation has been undone")
        else:
            messagebox.showinfo("Nothing to Undo", "No operations to undo")


if __name__ == "__main__":
    root = TkinterDnD.Tk()  # Use TkinterDnD.Tk() instead of tk.Tk()
    root.title("Batch Image Resizer")
    app = ImageResizerApp(root)
    root.mainloop()