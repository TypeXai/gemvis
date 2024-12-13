import os
import uuid
import json
import logging
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("No Google API key found. Please set GOOGLE_API_KEY environment variable.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')
logger.info("Initialized Gemini model: gemini-1.5-pro")

# Flask app configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'error': 'No selected file'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'error': 'File type not allowed'}), 400

        # Create unique filename
        filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(file.filename)[1])
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        try:
            # Save and optimize image
            with Image.open(file.stream) as img:
                # Convert RGBA to RGB if necessary
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Resize if too large
                max_size = 1600
                if max(img.size) > max_size:
                    ratio = max_size / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save optimized image
                img.save(filepath, 'JPEG', quality=85, optimize=True)
            
            logger.info(f"Saved optimized file: {filepath}")
            
            try:
                # Process with Gemini
                result = process_with_gemini(filepath)
                
                # Clean up
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning(f"Failed to remove temp file: {e}")
                
                # Return success response
                return jsonify({
                    'status': 'success',
                    'invoice_data': result,
                    'message': 'Invoice processed successfully'
                })
                
            except Exception as e:
                logger.error(f"Processing error: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500
                
        except Exception as e:
            logger.error(f"Image processing error: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': f"Failed to process image: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f"Upload failed: {str(e)}"
        }), 500

def process_with_gemini(image_path):
    """Process the image with Gemini Vision AI"""
    try:
        # Load the image
        img = Image.open(image_path)
        
        # Prepare the prompt
        prompt = """
        Extract the following information from this Hebrew invoice image, paying careful attention to the column order and values:

        The invoice has these columns from right to left:
        - סה"כ (Total amount for line)
        - מחיר (Unit price)
        - כמות (Quantity)
        - תיאור (Description)

        For example, for the first line:
        המבורגר ילדים:
        - כמות (Quantity): 7.00
        - מחיר (Unit price): ₪38.00
        - סה"כ (Total): ₪266.00 (calculated as 7.00 × ₪38.00)

        Extract and format as JSON:
        {
            "company_details": {
                "name": "string",
                "address": "string",
                "tax_id": "string"
            },
            "invoice_number": "string",
            "date": "string",
            "line_items": [
                {
                    "description": "string",
                    "quantity": number (from כמות column),
                    "unit_price": number (from מחיר column),
                    "total": number (calculated as quantity × unit_price)
                }
            ],
            "totals": {
                "subtotal": number,
                "tax": number,
                "total": number
            }
        }

        IMPORTANT:
        - Use EXACT numbers from the כמות column for quantities
        - Use EXACT numbers from the מחיר column for unit prices
        - Calculate total as quantity × unit price
        - Verify each line's total matches the calculation
        - Keep all decimal places as shown in the invoice
        - Numbers should be numeric values, not strings
        """
        
        # Generate content
        response = model.generate_content(
            [prompt, img],
            generation_config={
                "temperature": 0.1,
                "top_p": 1,
                "top_k": 32,
                "max_output_tokens": 4096,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ]
        )
        
        # Extract JSON from response
        try:
            # Clean the response text
            text = response.text.strip()
            text = text.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON
            result = json.loads(text)
            
            # Validate required fields
            required_fields = {
                'company_details', 'invoice_number', 'date', 
                'line_items', 'totals'
            }
            if not all(field in result for field in required_fields):
                raise ValueError("Missing required fields in response")
            
            # Validate and fix line item calculations
            for item in result['line_items']:
                # Ensure we have the correct fields
                if not all(field in item for field in ['quantity', 'unit_price', 'description']):
                    raise ValueError(f"Missing required fields in line item: {item}")
                
                # Validate the numbers
                if not isinstance(item['quantity'], (int, float)):
                    raise ValueError(f"Invalid quantity for {item['description']}: {item['quantity']}")
                if not isinstance(item['unit_price'], (int, float)):
                    raise ValueError(f"Invalid unit price for {item['description']}: {item['unit_price']}")
                
                # Calculate the correct total
                expected_total = round(item['quantity'] * item['unit_price'], 2)
                item['total'] = expected_total
            
            # Calculate and validate totals
            subtotal = sum(item['total'] for item in result['line_items'])
            tax = round(subtotal * 0.17, 2)
            total = round(subtotal + tax, 2)
            
            result['totals'] = {
                'subtotal': subtotal,
                'tax': tax,
                'total': total
            }
            
            # Log the extracted data for verification
            logger.info(f"Extracted line items:")
            for item in result['line_items']:
                logger.info(f"Description: {item['description']}")
                logger.info(f"Quantity: {item['quantity']}")
                logger.info(f"Unit Price: {item['unit_price']}")
                logger.info(f"Total: {item['total']}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            raise ValueError("Failed to parse response as valid JSON")
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid response format: {str(e)}")
            raise ValueError(f"Invalid response format: {str(e)}")
        
    except Exception as e:
        logger.error(f"Gemini processing error: {str(e)}")
        raise Exception(f"Failed to process with Gemini: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, port=8080)