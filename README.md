# Invoice Processing Application with Gemini Vision AI

A modern web application for processing and analyzing invoices using Google's Gemini Vision AI. The application supports RTL (Right-to-Left) text and is optimized for Hebrew invoices.

## Features

- Upload and process PDF, PNG, and JPG invoices
- Automatic text extraction using Gemini Vision AI
- Real-time invoice editing with automatic calculations
- RTL support for Hebrew text
- Responsive design
- Print-friendly output

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- Google Cloud API key for Gemini Vision AI

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/TypeXai/gemvis.git
   cd gemvis
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

## Usage

1. Start the development server:

   ```bash
   python app.py
   ```

2. Open your browser and navigate to:

   ```
   http://localhost:8080
   ```

3. Upload an invoice and process it with Gemini Vision AI

## Development

- The application uses Flask for the backend
- Frontend is built with Bootstrap 5
- File processing is handled asynchronously
- All calculations are verified server-side

## Project Structure

```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── layouts/         # Base templates
│   └── index.html       # Main UI template
├── static/              # Static assets
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── images/         # Image assets
├── uploads/            # Temporary upload directory
└── .env                # Environment variables
```

## API Endpoints

- `GET /`: Main application page
- `POST /upload`: Upload and process invoice
  - Accepts: multipart/form-data
  - Returns: JSON with processed invoice data

## Error Handling

The application includes comprehensive error handling for:

- File upload issues
- Processing errors
- API failures
- Validation errors

## Security

- Secure file handling
- Input validation
- Environment variable protection
- Temporary file cleanup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
