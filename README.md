# SmartPhotoMetadata

SmartPhotoMetadata is a Python-based tool that enhances image metadata by:
- Automatically **extracting GPS coordinates** based on filenames
- Embedding **GPS EXIF metadata** into images
- Generating **AI-powered titles** using OpenAI's GPT model

This tool is designed for photographers and archivists who want to enrich their image metadata effortlessly.

## Features
-  Extracts **location names** from filenames and converts them to GPS coordinates
-  Adds **EXIF GPS metadata** to images while preserving quality
-  Uses **OpenAI GPT** to generate artistic Japanese titles for images
-  Renames images based on AI-generated titles
-  Saves a **log CSV file** with original and new filenames
-  Simple **GUI** with folder selection and status updates

## Installation

### **1. Clone the Repository**
```sh
git clone https://github.com/ungaul/SmartPhotoMetadata.git
cd SmartPhotoMetadata
```

### **2. Install Dependencies**
Use `pipreqs` to generate and install required dependencies:
```sh
pip install -r requirements.txt
```

If you don't have `pipreqs`, install it first:
```sh
pip install pipreqs
pipreqs . --force
```

### **3. Set Up OpenAI API Key**
Create a `.env` file in the project root and add:
```sh
OPENAI_API_KEY=your_openai_api_key_here
```
Alternatively, the script will prompt you to enter the API key manually.

## Usage

### **Run the Script**
```sh
python run.py
```

### **GUI Interface**
1. Select a folder containing `.jpg` images.
2. Click **Start Processing** to:
   - Extract location-based GPS data and update EXIF metadata.
   - Generate a Japanese AI title for each image.
   - Rename images and log changes in `log.csv`.

### **Output**
- Processed images with updated **GPS metadata** and **AI-generated names**.
- A `log.csv` file listing original filenames and new AI-generated titles.

## Compiling to an Executable
To create a Windows `.exe` file:
```sh
pip install pyinstaller
pyinstaller --onefile --windowed --icon=logo.ico run.py
```
The executable will be found in the `dist/` folder.

## Dependencies
This project requires the following libraries:
```txt
openai
piexif
pillow
geopy
python-dotenv
ttkbootstrap
```

## License
This project is licensed under the MIT License.

## Contributing
Feel free to submit pull requests or open issues for enhancements or bug fixes.

---
Made with ❤️ for photographers and metadata lovers!