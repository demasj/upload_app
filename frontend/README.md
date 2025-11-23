# Streamlit Frontend for Large File Upload

This is a Streamlit-based frontend interface for the Large File Upload API.

## Features

- Direct browser upload (no memory usage)
- File upload with progress tracking and speed display
- Chunked upload support for large files
- Modular architecture with separate CSS, JS, and HTML files

## Project Structure

```
frontend/
├── static/
│   ├── styles.css      # CSS styles
│   ├── script.js       # JavaScript functionality
│   └── template.html   # HTML template
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Running the App

1. Ensure the backend API is running on `http://localhost:8000`
2. Install dependencies from the root directory: `pip install -r requirements.txt`
3. Run the app: `streamlit run app.py`

Note: The app is configured to allow uploads up to 1GB. If you need to change the upload limit, modify `.streamlit/config.toml`.

The app will be available at `http://localhost:8501` by default.