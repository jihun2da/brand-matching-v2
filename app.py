from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_cors import CORS
import os
import cv2
import numpy as np
from PIL import Image
import base64
import io
from werkzeug.utils import secure_filename
import json
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['BRAND_DB_FOLDER'] = 'brand_db'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['BRAND_DB_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Brand database - in production, this would be in a real database
BRAND_DATABASE = {
    "nike": {
        "name": "Nike",
        "description": "Just Do It",
        "colors": ["#000000", "#FFFFFF"],
        "keywords": ["swoosh", "just do it", "nike", "athletic"]
    },
    "adidas": {
        "name": "Adidas",
        "description": "Impossible is Nothing",
        "colors": ["#000000", "#FFFFFF"],
        "keywords": ["three stripes", "adidas", "athletic", "trefoil"]
    },
    "apple": {
        "name": "Apple",
        "description": "Think Different",
        "colors": ["#000000", "#FFFFFF", "#007AFF"],
        "keywords": ["apple", "bitten apple", "tech", "minimalist"]
    },
    "coca-cola": {
        "name": "Coca-Cola",
        "description": "Taste the Feeling",
        "colors": ["#FF0000", "#FFFFFF"],
        "keywords": ["coca cola", "coke", "red", "classic"]
    }
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_features(image_path):
    """Extract features from image using OpenCV"""
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # Convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Extract dominant colors
        img_resized = cv2.resize(img_rgb, (50, 50))
        colors = img_resized.reshape(-1, 3)
        unique_colors = np.unique(colors, axis=0)
        
        # Get image dimensions and basic properties
        height, width = img.shape[:2]
        
        # Calculate color histogram
        hist_r = cv2.calcHist([img_rgb], [0], None, [32], [0, 256])
        hist_g = cv2.calcHist([img_rgb], [1], None, [32], [0, 256])
        hist_b = cv2.calcHist([img_rgb], [2], None, [32], [0, 256])
        
        features = {
            'dominant_colors': unique_colors[:10].tolist(),  # Top 10 colors
            'dimensions': [width, height],
            'color_histogram': {
                'r': hist_r.flatten().tolist(),
                'g': hist_g.flatten().tolist(),
                'b': hist_b.flatten().tolist()
            }
        }
        
        return features
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        return None

def match_brand(features):
    """Match image features with brand database"""
    if not features:
        return None
    
    matches = []
    
    for brand_id, brand_data in BRAND_DATABASE.items():
        confidence = 0
        
        # Simple color matching (this is a basic implementation)
        dominant_colors = features.get('dominant_colors', [])
        brand_colors = brand_data.get('colors', [])
        
        # Convert hex colors to RGB for comparison
        brand_rgb_colors = []
        for hex_color in brand_colors:
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            brand_rgb_colors.append(rgb)
        
        # Calculate color similarity
        for dom_color in dominant_colors[:3]:  # Check top 3 dominant colors
            for brand_color in brand_rgb_colors:
                # Calculate Euclidean distance
                distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(dom_color, brand_color)))
                similarity = max(0, 1 - (distance / 441))  # 441 is max distance for RGB
                confidence += similarity * 0.3
        
        # Add some randomness for demo purposes
        confidence += np.random.random() * 0.2
        
        matches.append({
            'brand_id': brand_id,
            'brand_name': brand_data['name'],
            'confidence': min(confidence, 1.0),
            'description': brand_data['description']
        })
    
    # Sort by confidence
    matches.sort(key=lambda x: x['confidence'], reverse=True)
    return matches[:5]  # Return top 5 matches

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and brand matching"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract features
        features = extract_features(filepath)
        if not features:
            return jsonify({'error': 'Failed to process image'}), 500
        
        # Match with brands
        matches = match_brand(features)
        
        # Convert image to base64 for display
        with open(filepath, 'rb') as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'filename': filename,
            'image_data': f"data:image/jpeg;base64,{img_base64}",
            'matches': matches,
            'features': features
        })
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/brands')
def get_brands():
    """Get all brands in database"""
    return jsonify(BRAND_DATABASE)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 