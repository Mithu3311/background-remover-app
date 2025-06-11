# Background Remover Web Application

This is a web-based version of the Background Remover application that allows users to remove backgrounds from images using the remove.bg API.

## Features

- Modern web interface with drag & drop functionality
- Background removal using the remove.bg API
- Side-by-side comparison of original and processed images
- Download functionality for processed images
- Responsive design that works on desktop and mobile devices

## Installation

1. Clone this repository or download the files

2. Install the required dependencies:

```bash
pip install -r web_requirements.txt
```

3. Create the necessary directories for file uploads and results:

```bash
mkdir -p uploads results
```

## Usage

1. Start the web server:

```bash
python web_app.py
```

2. Open your web browser and navigate to:

```
http://localhost:5000
```

3. Upload an image using the drag & drop interface or the file browser

4. Click "Remove Background" to process the image

5. View the result and download the processed image

## API Usage

The application also provides a simple API endpoint for background removal:

```
POST /api/remove-bg
```

Parameters:
- `file`: The image file to process

Response:
```json
{
    "success": true,
    "download_url": "http://localhost:5000/download/result_filename.png"
}
```

## Note About API Usage

This application uses the remove.bg API which has usage limits. The API key is hardcoded in the application. If you encounter any issues with the API, you might need to check your API usage or obtain a new key from remove.bg.

## Desktop Version

A desktop version of this application is also available in the same repository. To run the desktop version:

```bash
python app.py
```

## License

This project is open source and available under the MIT License.