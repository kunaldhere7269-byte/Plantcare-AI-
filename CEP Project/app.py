"""
app.py - Main Flask Application for PlantCare AI
AI-Assisted Plant Growth Monitoring & Disease Detection System
Built for College Community Engagement Project (CEP).
"""

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database import (
    init_db, save_analysis, get_analysis_by_id, get_all_analyses,
    update_notes, delete_analysis, get_dashboard_stats, get_distinct_plants
)
from services.image_processor import process_and_save_image
from services.ai_analyzer import analyze_plant_image

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'plantcare-ai-cep-secret-2026')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), os.getenv('UPLOAD_FOLDER', 'uploads'))
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))  # 10 MB

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'), exist_ok=True)

# Initialize database on module load
init_db()


@app.context_processor
def inject_global_data():
    """Inject global context into all templates, such as API status banner."""
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    return {
        'has_gemini_key': bool(api_key and len(api_key) > 5),
        'app_name': 'PlantCare AI',
        'current_year': 2026
    }


# -------------------------------------------------------------
# Static Upload Serving
# -------------------------------------------------------------
@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded plant image."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/uploads/thumbnails/<filename>')
def serve_thumbnail(filename):
    """Serve thumbnail image."""
    thumb_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails')
    return send_from_directory(thumb_dir, filename)


# -------------------------------------------------------------
# Page Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    """Home landing page."""
    stats = get_dashboard_stats()
    return render_template('index.html', stats=stats)


@app.route('/analyze')
def analyze():
    """Plant photo upload & diagnosis interactive page."""
    distinct_plants = get_distinct_plants()
    return render_template('analyze.html', distinct_plants=distinct_plants)


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """
    Handle plant image upload and trigger AI diagnosis.
    Saves analysis record into SQLite and returns full results JSON.
    """
    # 1. Check for file in request or sample image request
    file = request.files.get('plant_image')
    sample_name = request.form.get('sample_image')

    image_filename = None
    thumb_filename = None
    image_path = None

    if sample_name:
        # Pre-configured sample image demo
        sample_map = {
            'tomato_blight': ('sample_tomato_blight.jpg', 'Tomato (Solanum lycopersicum)', 'Brown spots with concentric rings and yellow halo'),
            'healthy_basil': ('sample_healthy_leaf.jpg', 'Sweet Basil (Ocimum basilicum)', 'None, normal healthy check')
        }
        if sample_name in sample_map:
            s_file, default_plant, default_symptoms = sample_map[sample_name]
            image_filename = s_file
            thumb_filename = s_file
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], s_file)

    if not image_path:
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'Please select a plant image to upload.'}), 400

        # Process and save the uploaded image safely
        proc_result = process_and_save_image(file, app.config['UPLOAD_FOLDER'])
        if not proc_result['success']:
            return jsonify({'success': False, 'error': proc_result['error']}), 400

        image_filename = proc_result['image_filename']
        thumb_filename = proc_result['thumbnail_filename']
        image_path = proc_result['image_path']

    # 2. Gather user context
    plant_name = request.form.get('plant_name', '').strip() or 'Unknown Plant'
    plant_age = request.form.get('plant_age', '').strip()
    location = request.form.get('location', '').strip()
    soil_type = request.form.get('soil_type', '').strip()
    watering_frequency = request.form.get('watering_frequency', '').strip()
    user_symptoms = request.form.get('user_symptoms', '').strip()

    metadata = {
        'plant_name': plant_name,
        'plant_age': plant_age,
        'location': location,
        'soil_type': soil_type,
        'watering_frequency': watering_frequency,
        'user_symptoms': user_symptoms
    }

    # 3. Execute AI diagnosis
    analysis_data = analyze_plant_image(image_path, metadata)

    # If the user didn't specify plant name or left it general, use identified name if available
    final_plant_name = plant_name
    if plant_name in ('', 'Unknown Plant', 'Other') and analysis_data.get('plant_name'):
        final_plant_name = analysis_data['plant_name']

    # 4. Prepare database record
    db_payload = {
        'plant_name': final_plant_name,
        'plant_age': plant_age,
        'location': location,
        'soil_type': soil_type,
        'watering_frequency': watering_frequency,
        'user_symptoms': user_symptoms,
        'image_filename': image_filename,
        'thumbnail_filename': thumb_filename,
        'health_status': analysis_data.get('health_status', 'Unclear'),
        'disease_name': analysis_data.get('disease_name', 'Undetermined'),
        'severity': analysis_data.get('severity', 'None'),
        'confidence_score': analysis_data.get('confidence_score'),
        'visible_symptoms': analysis_data.get('visible_symptoms', []),
        'growth_observations': analysis_data.get('growth_observations', []),
        'likely_causes': analysis_data.get('likely_causes', []),
        'immediate_steps': analysis_data.get('immediate_steps', []),
        'treatment_recommendations': analysis_data.get('treatment_recommendations', []),
        'preventive_measures': analysis_data.get('preventive_measures', []),
        'personalized_care': analysis_data.get('personalized_care', {}),
        'notes': f"Initial scan conducted on {location or 'Garden'}.",
        'engine_used': analysis_data.get('engine_used', 'PlantCare AI Engine'),
        'is_clarity_issue': analysis_data.get('is_clarity_issue', False),
        'clarity_notes': analysis_data.get('clarity_notes', '')
    }

    # 5. Persist to SQLite
    record_id = save_analysis(db_payload)

    # 6. Response with full structured data and link to detail page
    return jsonify({
        'success': True,
        'id': record_id,
        'redirect_url': url_for('view_analysis', analysis_id=record_id),
        'data': {
            'id': record_id,
            'plant_name': final_plant_name,
            'health_status': analysis_data.get('health_status'),
            'disease_name': analysis_data.get('disease_name'),
            'severity': analysis_data.get('severity'),
            'confidence_score': analysis_data.get('confidence_score'),
            'visible_symptoms': analysis_data.get('visible_symptoms', []),
            'growth_observations': analysis_data.get('growth_observations', []),
            'likely_causes': analysis_data.get('likely_causes', []),
            'immediate_steps': analysis_data.get('immediate_steps', []),
            'treatment_recommendations': analysis_data.get('treatment_recommendations', []),
            'preventive_measures': analysis_data.get('preventive_measures', []),
            'personalized_care': analysis_data.get('personalized_care', {}),
            'engine_used': analysis_data.get('engine_used'),
            'is_live_ai': analysis_data.get('is_live_ai', False),
            'is_clarity_issue': analysis_data.get('is_clarity_issue', False),
            'clarity_notes': analysis_data.get('clarity_notes', ''),
            'fallback_reason': analysis_data.get('fallback_reason'),
            'image_url': url_for('serve_upload', filename=image_filename),
            'thumbnail_url': url_for('serve_thumbnail', filename=thumb_filename)
        }
    })


@app.route('/history')
def history():
    """Monitoring history view with search, filter, and comparison modal."""
    health_filter = request.args.get('status', 'all')
    plant_filter = request.args.get('plant', 'all')
    search_query = request.args.get('q', '').strip()

    records = get_all_analyses(health_filter=health_filter, search=search_query, plant_filter=plant_filter)
    distinct_plants = get_distinct_plants()

    return render_template(
        'history.html',
        records=records,
        distinct_plants=distinct_plants,
        current_status=health_filter,
        current_plant=plant_filter,
        search_query=search_query
    )


@app.route('/history/<int:analysis_id>')
def view_analysis(analysis_id):
    """View full detailed report for a specific plant monitoring session."""
    record = get_analysis_by_id(analysis_id)
    if not record:
        flash('Analysis record not found.', 'danger')
        return redirect(url_for('history'))

    # Retrieve other records of the same plant for timeline tracking
    other_records = [
        r for r in get_all_analyses(plant_filter=record['plant_name'])
        if r['id'] != record['id']
    ]

    return render_template('detail.html', record=record, related_records=other_records)


@app.route('/history/<int:analysis_id>/notes', methods=['POST'])
def save_notes(analysis_id):
    """Update notes for a specific plant monitoring record."""
    notes = request.form.get('notes', '').strip()
    update_notes(analysis_id, notes)
    flash('Monitoring notes successfully updated.', 'success')
    return redirect(url_for('view_analysis', analysis_id=analysis_id))


@app.route('/history/<int:analysis_id>/delete', methods=['POST'])
def delete_record(analysis_id):
    """Delete an analysis record."""
    deleted_row = delete_analysis(analysis_id)
    if deleted_row:
        # Optionally clean up files if not a demo sample
        img = deleted_row['image_filename']
        if img and not img.startswith('sample_'):
            try:
                p1 = os.path.join(app.config['UPLOAD_FOLDER'], img)
                if os.path.exists(p1):
                    os.remove(p1)
                thumb = deleted_row['thumbnail_filename']
                if thumb:
                    p2 = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', thumb)
                    if os.path.exists(p2):
                        os.remove(p2)
            except Exception:
                pass

    flash('Plant analysis record deleted.', 'info')
    return redirect(url_for('history'))


@app.route('/compare')
def compare():
    """Side-by-side comparison of two plant monitoring scans."""
    id1 = request.args.get('id1', type=int)
    id2 = request.args.get('id2', type=int)

    all_records = get_all_analyses()

    record1 = get_analysis_by_id(id1) if id1 else None
    record2 = get_analysis_by_id(id2) if id2 else None

    # If parameters not passed, pre-select first 2 records if available
    if not record1 and len(all_records) >= 1:
        record1 = get_analysis_by_id(all_records[0]['id'])
    if not record2 and len(all_records) >= 2:
        record2 = get_analysis_by_id(all_records[1]['id'])

    return render_template('compare.html', record1=record1, record2=record2, all_records=all_records)


@app.route('/dashboard')
def dashboard():
    """Interactive dashboard with real metrics, Chart.js visualizations, and care tips."""
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)


@app.route('/guide')
def guide():
    """Educational guide: 'How to Take a Good Plant Photo'."""
    return render_template('guide.html')


@app.route('/faq')
def faq():
    """Frequently Asked Questions."""
    return render_template('faq.html')


@app.route('/about')
def about():
    """Project background, architecture, and College Community Engagement Project (CEP) documentation."""
    return render_template('about.html')


# -------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------
@app.errorhandler(413)
def file_too_large(e):
    if request.is_json:
        return jsonify({'success': False, 'error': 'Image file is too large. Maximum size allowed is 10 MB.'}), 413
    flash('File too large. Please upload an image under 10 MB.', 'danger')
    return redirect(url_for('analyze'))


@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', content='<div class="container py-5 text-center"><h2>404 - Page Not Found</h2><p>The requested page could not be located.</p><a href="/" class="btn btn-primary mt-3">Return to Home</a></div>'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', content='<div class="container py-5 text-center"><h2>500 - Server Error</h2><p>An unexpected error occurred while processing your request.</p><a href="/" class="btn btn-primary mt-3">Return to Home</a></div>'), 500


if __name__ == '__main__':
    # Local development server
    port = int(os.getenv('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True)
