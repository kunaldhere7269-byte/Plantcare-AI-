"""
services/image_processor.py - Image Validation, Resizing, Thumbnailing & CV Feature Extraction
Handles secure uploads, image integrity checks, thumbnail generation, and OpenCV/PIL color/texture analytics.
"""

import os
import uuid
from datetime import datetime
from PIL import Image
import cv2
import numpy as np
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_DIMENSION = 1600
THUMBNAIL_SIZE = (400, 400)


def allowed_file(filename):
    """Check if uploaded file has an approved image extension."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def process_and_save_image(file_storage, upload_folder):
    """
    Validate, sanitize, resize, and save an uploaded plant photo.
    Generates both an optimized main image and a high-performance thumbnail.
    
    Returns:
        dict: {
            'success': bool,
            'image_filename': str,
            'thumbnail_filename': str,
            'image_path': str,
            'thumbnail_path': str,
            'width': int,
            'height': int,
            'file_size_kb': float,
            'error': str (if failed)
        }
    """
    if not file_storage or not file_storage.filename:
        return {'success': False, 'error': 'No file was provided.'}

    if not allowed_file(file_storage.filename):
        return {
            'success': False, 
            'error': f'Unsupported file type. Please upload a JPG, JPEG, PNG, or WEBP image.'
        }

    # Generate unique, non-colliding safe filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    ext = 'jpg'  # normalize output storage to clean JPG
    image_filename = f'plant_{timestamp}_{unique_id}.{ext}'
    thumb_filename = f'thumb_{timestamp}_{unique_id}.{ext}'

    os.makedirs(upload_folder, exist_ok=True)
    thumb_folder = os.path.join(upload_folder, 'thumbnails')
    os.makedirs(thumb_folder, exist_ok=True)

    image_path = os.path.join(upload_folder, image_filename)
    thumb_path = os.path.join(thumb_folder, thumb_filename)

    try:
        # Open and verify image integrity with Pillow
        image = Image.open(file_storage.stream)
        image.verify()  # verify that it is actually an image

        # Reopen after verify (verify closes or invalidates the stream pointer)
        file_storage.stream.seek(0)
        image = Image.open(file_storage.stream)

        # Convert to RGB (handles RGBA, PNG transparency, palette, CMYK)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Paste on clean white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        orig_w, orig_h = image.size

        # Resize if image exceeds maximum dimensions while preserving aspect ratio
        if orig_w > MAX_DIMENSION or orig_h > MAX_DIMENSION:
            image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

        # Save optimized main image
        image.save(image_path, 'JPEG', quality=88, optimize=True)

        # Generate cropped square thumbnail for fast card/table rendering
        thumb_image = image.copy()
        thumb_image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        thumb_image.save(thumb_path, 'JPEG', quality=85, optimize=True)

        file_size_kb = round(os.path.getsize(image_path) / 1024, 1)

        return {
            'success': True,
            'image_filename': image_filename,
            'thumbnail_filename': thumb_filename,
            'image_path': image_path,
            'thumbnail_path': thumb_path,
            'width': image.width,
            'height': image.height,
            'file_size_kb': file_size_kb,
            'error': None
        }

    except Exception as e:
        # Clean up any partial files if an error occurred
        if os.path.exists(image_path):
            os.remove(image_path)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
        return {'success': False, 'error': f'Failed to process image: {str(e)}'}


def extract_visual_features(image_path):
    """
    Extract computer vision features (greenness, necrosis ratio, sharpness, brightness)
    using OpenCV to substantiate visual health observations.
    """
    metrics = {
        'is_blurry': False,
        'blur_score': 0.0,
        'average_brightness': 128.0,
        'green_ratio': 0.0,
        'yellow_brown_ratio': 0.0,
        'is_plant_candidate': True,
        'visual_description': []
    }

    if not os.path.exists(image_path):
        return metrics

    try:
        # Load image via OpenCV
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            return metrics

        # Resize for consistent rapid analysis
        img_bgr = cv2.resize(img_bgr, (600, 600))
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Image Sharpness / Blur Detection (Laplacian Variance)
        laplacian_var = cv2.Laplacian(img_gray, cv2.CV_64F).var()
        metrics['blur_score'] = round(float(laplacian_var), 1)
        if laplacian_var < 70:
            metrics['is_blurry'] = True
            metrics['visual_description'].append('Image has moderate optical blur or soft focus.')

        # 2. Brightness Check
        avg_brightness = float(np.mean(img_gray))
        metrics['average_brightness'] = round(avg_brightness, 1)
        if avg_brightness < 45:
            metrics['visual_description'].append('Photograph is dimly lit; details in shadow might be obscured.')
        elif avg_brightness > 220:
            metrics['visual_description'].append('Photograph is overexposed; leaf highlights are washed out.')

        # 3. Green Foliage Coverage (HSV: Hue 35 to 85)
        lower_green = np.array([30, 40, 40])
        upper_green = np.array([85, 255, 255])
        mask_green = cv2.inRange(img_hsv, lower_green, upper_green)
        green_ratio = float(np.sum(mask_green > 0)) / (600 * 600)
        metrics['green_ratio'] = round(green_ratio, 3)

        # 4. Yellow / Chlorotic Foliage Coverage (HSV: Hue 18 to 35)
        lower_yellow = np.array([18, 50, 50])
        upper_yellow = np.array([32, 255, 255])
        mask_yellow = cv2.inRange(img_hsv, lower_yellow, upper_yellow)
        yellow_ratio = float(np.sum(mask_yellow > 0)) / (600 * 600)

        # 5. Brown / Necrotic Lesion Foliage Coverage (HSV: Hue 8 to 20, lower saturation/val)
        lower_brown = np.array([5, 40, 20])
        upper_brown = np.array([20, 200, 160])
        mask_brown = cv2.inRange(img_hsv, lower_brown, upper_brown)
        brown_ratio = float(np.sum(mask_brown > 0)) / (600 * 600)

        total_necrotic_ratio = round(yellow_ratio + brown_ratio, 3)
        metrics['yellow_brown_ratio'] = total_necrotic_ratio

        # Determine plant likelihood
        if green_ratio < 0.08 and total_necrotic_ratio < 0.04:
            metrics['is_plant_candidate'] = False
            metrics['visual_description'].append('Low botanical chlorophyll signature detected; image may not contain plant leaves.')
        else:
            metrics['is_plant_candidate'] = True

        return metrics

    except Exception as e:
        metrics['visual_description'].append(f'CV analysis note: {str(e)}')
        return metrics
