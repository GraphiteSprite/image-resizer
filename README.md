# Image Resizer

A cross-platform desktop application for batch resizing images with a user-friendly interface.

## Downloads

Pre-built binaries are available in the [Releases](../../releases) section:
- Windows: `ImageResizer_Windows.zip`
- Linux: `ImageResizer.AppImage`

### Windows Installation
1. Download `ImageResizer_Windows.zip`
2. Extract the zip file
3. Double-click `Image Resizer.exe` to run

### Linux Installation
1. Download `ImageResizer.AppImage`
2. Make it executable:
```bash
chmod +x ImageResizer.AppImage
```
3. Double-click to run or use terminal:
```bash
./ImageResizer.AppImage
```

## Features

- **Two Resizing Modes**:
  - **Pixel-based**: Resize images by specifying the shortest side in pixels while maintaining aspect ratio
  - **File Size-based**: Compress images to a target file size in MB while maximizing quality

- **Batch Processing**:
  - Process multiple images at once
  - Support for entire folders
  - Multiple file selection via comma-separated paths
  - Progress tracking with status updates

- **Smart File Handling**:
  - Automatic skipping of files that are already under target size
  - Output files named with transformation details (e.g., `image_w1000px.jpg` or `image_1.5MB.jpg`)
  - Maintains original image format

- **User-Friendly Interface**:
  - Drag-and-drop support for input/output folders
  - Clear progress indication
  - Undo functionality for last batch operation
  - Visual feedback through status messages

- **Supported Formats**:
  - JPEG/JPG
  - PNG
  - BMP
  - TIFF/TIF
  - GIF
  - WEBP
  - HEIC/HEIF
  - AVIF

## Usage

1. Select input (folder or files) and output location:
   - Use Browse buttons or drag-and-drop
   - For multiple specific files, separate paths with commas

2. Choose resize mode:
   - **Pixels**: Enter desired size for shortest side (maintains aspect ratio)
   - **File Size**: Enter target size in MB (optimizes quality while meeting size constraint)

3. Click "Resize Images" to begin processing

4. Use "Undo Last Batch" to revert the most recent batch operation if needed

## Requirements

- Python 3.x
- Pillow
- customtkinter
- tkinterdnd2

## Installation

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python image_resizer.py
```
