"""
database.py - SQLite Database Management for PlantCare AI
Handles persistent storage of plant analyses, symptoms, care notes, and statistics.
"""

import sqlite3
import json
import os
from datetime import datetime

DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'data', 'plantcare.db'))


def get_db_connection():
    """Create and return a thread-safe connection to the SQLite database with dict-like row access."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables and indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_name TEXT NOT NULL,
            plant_age TEXT,
            location TEXT,
            soil_type TEXT,
            watering_frequency TEXT,
            user_symptoms TEXT,
            image_filename TEXT NOT NULL,
            thumbnail_filename TEXT,
            health_status TEXT NOT NULL,  -- Healthy, Potentially Affected, Diseased, Unclear
            disease_name TEXT,
            severity TEXT,                -- Low, Moderate, High, None
            confidence_score REAL,
            visible_symptoms TEXT,        -- JSON array
            growth_observations TEXT,     -- JSON array
            likely_causes TEXT,           -- JSON array or text
            immediate_steps TEXT,         -- JSON array
            treatment_recommendations TEXT, -- JSON array
            preventive_measures TEXT,     -- JSON array
            personalized_care TEXT,       -- JSON object
            notes TEXT,
            engine_used TEXT NOT NULL,
            is_clarity_issue INTEGER DEFAULT 0,
            clarity_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create helpful indexes for performance and querying
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_plant_name ON analyses(plant_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_health_status ON analyses(health_status)')

    conn.commit()
    conn.close()

    # Seed sample records if database is empty
    seed_sample_data_if_empty()


def _json_dumps_safe(val):
    if val is None:
        return '[]'
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    return str(val)


def _json_loads_safe(val, default=None):
    if not val:
        return default if default is not None else []
    try:
        return json.loads(val)
    except Exception:
        return default if default is not None else []


def save_analysis(data):
    """Save an analysis record into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO analyses (
            plant_name, plant_age, location, soil_type, watering_frequency,
            user_symptoms, image_filename, thumbnail_filename,
            health_status, disease_name, severity, confidence_score,
            visible_symptoms, growth_observations, likely_causes,
            immediate_steps, treatment_recommendations, preventive_measures,
            personalized_care, notes, engine_used, is_clarity_issue, clarity_notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('plant_name', 'Unknown Plant'),
        data.get('plant_age', ''),
        data.get('location', ''),
        data.get('soil_type', ''),
        data.get('watering_frequency', ''),
        data.get('user_symptoms', ''),
        data.get('image_filename', ''),
        data.get('thumbnail_filename', ''),
        data.get('health_status', 'Unclear'),
        data.get('disease_name', 'Undetermined'),
        data.get('severity', 'None'),
        data.get('confidence_score'),
        _json_dumps_safe(data.get('visible_symptoms', [])),
        _json_dumps_safe(data.get('growth_observations', [])),
        _json_dumps_safe(data.get('likely_causes', [])),
        _json_dumps_safe(data.get('immediate_steps', [])),
        _json_dumps_safe(data.get('treatment_recommendations', [])),
        _json_dumps_safe(data.get('preventive_measures', [])),
        _json_dumps_safe(data.get('personalized_care', {})),
        data.get('notes', ''),
        data.get('engine_used', 'PlantCare AI Engine'),
        1 if data.get('is_clarity_issue') else 0,
        data.get('clarity_notes', ''),
        data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    ))

    analysis_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return analysis_id


def get_analysis_by_id(analysis_id):
    """Retrieve and unpack a single analysis record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    item = dict(row)
    item['visible_symptoms'] = _json_loads_safe(item.get('visible_symptoms'), [])
    item['growth_observations'] = _json_loads_safe(item.get('growth_observations'), [])
    item['likely_causes'] = _json_loads_safe(item.get('likely_causes'), [])
    item['immediate_steps'] = _json_loads_safe(item.get('immediate_steps'), [])
    item['treatment_recommendations'] = _json_loads_safe(item.get('treatment_recommendations'), [])
    item['preventive_measures'] = _json_loads_safe(item.get('preventive_measures'), [])
    item['personalized_care'] = _json_loads_safe(item.get('personalized_care'), {})
    return item


def get_all_analyses(health_filter=None, search=None, plant_filter=None):
    """Retrieve all analyses with optional filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM analyses WHERE 1=1'
    params = []

    if health_filter and health_filter != 'all':
        query += ' AND health_status = ?'
        params.append(health_filter)

    if plant_filter and plant_filter != 'all':
        query += ' AND LOWER(plant_name) = LOWER(?)'
        params.append(plant_filter)

    if search:
        query += ' AND (plant_name LIKE ? OR disease_name LIKE ? OR notes LIKE ? OR user_symptoms LIKE ?)'
        like_search = f'%{search}%'
        params.extend([like_search, like_search, like_search, like_search])

    query += ' ORDER BY created_at DESC'

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        item = dict(row)
        item['visible_symptoms'] = _json_loads_safe(item.get('visible_symptoms'), [])
        item['growth_observations'] = _json_loads_safe(item.get('growth_observations'), [])
        item['treatment_recommendations'] = _json_loads_safe(item.get('treatment_recommendations'), [])
        item['personalized_care'] = _json_loads_safe(item.get('personalized_care'), {})
        results.append(item)

    return results


def update_notes(analysis_id, new_notes):
    """Update notes for a specific analysis record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE analyses SET notes = ? WHERE id = ?', (new_notes, analysis_id))
    conn.commit()
    conn.close()
    return True


def delete_analysis(analysis_id):
    """Delete an analysis record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT image_filename, thumbnail_filename FROM analyses WHERE id = ?', (analysis_id,))
    row = cursor.fetchone()

    cursor.execute('DELETE FROM analyses WHERE id = ?', (analysis_id,))
    conn.commit()
    conn.close()
    return row


def get_distinct_plants():
    """Get list of distinct plant names stored in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT plant_name FROM analyses WHERE plant_name IS NOT NULL AND plant_name != "" ORDER BY plant_name ASC')
    rows = cursor.fetchall()
    conn.close()
    return [row['plant_name'] for row in rows]


def get_dashboard_stats():
    """Calculate and return real dynamic statistics for the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total analyses
    cursor.execute('SELECT COUNT(*) as count FROM analyses')
    total_analyses = cursor.fetchone()['count']

    # Total unique plants
    cursor.execute('SELECT COUNT(DISTINCT plant_name) as count FROM analyses')
    total_plants = cursor.fetchone()['count']

    # Health status breakdown
    cursor.execute('SELECT health_status, COUNT(*) as count FROM analyses GROUP BY health_status')
    status_rows = cursor.fetchall()
    status_counts = {'Healthy': 0, 'Potentially Affected': 0, 'Diseased': 0, 'Unclear': 0}
    for r in status_rows:
        if r['health_status'] in status_counts:
            status_counts[r['health_status']] = r['count']
        else:
            status_counts['Potentially Affected'] += r['count']

    # Severity breakdown
    cursor.execute('SELECT severity, COUNT(*) as count FROM analyses WHERE severity IS NOT NULL GROUP BY severity')
    sev_rows = cursor.fetchall()
    severity_counts = {'Low': 0, 'Moderate': 0, 'High': 0, 'None': 0}
    for r in sev_rows:
        sev = r['severity']
        if sev in severity_counts:
            severity_counts[sev] = r['count']

    # Top plant types monitored
    cursor.execute('''
        SELECT plant_name, COUNT(*) as count 
        FROM analyses 
        WHERE plant_name IS NOT NULL AND plant_name != ""
        GROUP BY plant_name 
        ORDER BY count DESC 
        LIMIT 6
    ''')
    top_plants = [{'name': r['plant_name'], 'count': r['count']} for r in cursor.fetchall()]

    # Recent activity (latest 5)
    cursor.execute('SELECT id, plant_name, health_status, disease_name, severity, image_filename, thumbnail_filename, created_at FROM analyses ORDER BY created_at DESC LIMIT 5')
    recent_activity = [dict(r) for r in cursor.fetchall()]

    # Timeline counts for trend chart (last 7 recorded days)
    cursor.execute('''
        SELECT DATE(created_at) as log_date, COUNT(*) as count 
        FROM analyses 
        GROUP BY DATE(created_at) 
        ORDER BY log_date ASC 
        LIMIT 10
    ''')
    trend_rows = cursor.fetchall()
    timeline = [{'date': r['log_date'], 'count': r['count']} for r in trend_rows]

    conn.close()

    healthy_count = status_counts['Healthy']
    affected_count = status_counts['Potentially Affected'] + status_counts['Diseased']

    return {
        'total_analyses': total_analyses,
        'total_plants': total_plants,
        'healthy_count': healthy_count,
        'affected_count': affected_count,
        'status_counts': status_counts,
        'severity_counts': severity_counts,
        'top_plants': top_plants,
        'recent_activity': recent_activity,
        'timeline': timeline
    }


def seed_sample_data_if_empty():
    """Populate database with realistic initial college demo records if it has no entries."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM analyses')
    count = cursor.fetchone()['count']

    if count == 0:
        sample_records = [
            {
                'plant_name': 'Tomato (Solanum lycopersicum)',
                'plant_age': 'Vegetative (6 weeks)',
                'location': 'Outdoor Kitchen Garden',
                'soil_type': 'Loamy soil with compost',
                'watering_frequency': 'Every 2 days (overhead sprinkling)',
                'user_symptoms': 'Brown concentric spots on lower leaves with yellow halo',
                'image_filename': 'sample_tomato_blight.jpg',
                'thumbnail_filename': 'sample_tomato_blight.jpg',
                'health_status': 'Diseased',
                'disease_name': 'Early Blight (Alternaria solani)',
                'severity': 'Moderate',
                'confidence_score': 0.94,
                'visible_symptoms': [
                    'Target-like concentric ring brown lesions on leaf surface',
                    'Chlorotic (yellowing) halo surrounding necrotic lesions',
                    'Lower mature leaves showing primary damage'
                ],
                'growth_observations': [
                    'Upper foliage remains green and turgid',
                    'Stem shows no visible dark cankers at this stage',
                    'Vegetative growth is active but threatened by spore spread'
                ],
                'likely_causes': [
                    'Alternaria solani fungal spores splashed from soil onto lower foliage',
                    'Prolonged leaf wetness from overhead watering',
                    'Warm, humid microclimate around lower canopy'
                ],
                'immediate_steps': [
                    'Immediately prune and carefully dispose of infected lower leaves (do NOT compost)',
                    'Disinfect pruning shears with 70% isopropyl alcohol between cuts',
                    'Switch watering to base-level drip or soaker hose to keep foliage dry'
                ],
                'treatment_recommendations': [
                    'Apply organic bio-fungicide containing Bacillus subtilis or copper octanoate spray as per label directions',
                    'Apply a 2-3 inch layer of clean straw mulch around plant base to prevent soil splashback',
                    'Ensure 24-inch spacing between tomato plants for optimal airflow'
                ],
                'preventive_measures': [
                    'Practice 3-year crop rotation (avoid planting nightshades like potatoes or peppers in the same bed)',
                    'Water early in the morning so incidental leaf moisture evaporates quickly',
                    'Choose certified disease-resistant tomato varieties for subsequent plantings'
                ],
                'personalized_care': {
                    'watering': 'Provide 1 to 1.5 inches of water per week at ground level only; avoid overhead sprinklers.',
                    'sunlight': 'Requires 6 to 8 hours of direct full sunlight daily.',
                    'soil_drainage': 'Prefers fertile, well-draining loamy soil with pH 6.2 - 6.8.',
                    'nutrients': 'Apply balanced organic fertilizer (5-10-10) with calcium to prevent blossom end rot.',
                    'temperature_humidity': 'Ideal temperature 21°C - 29°C (70°F - 85°F). Avoid leaf wetness during humid nights.',
                    'next_session': 'Inspect weekly for spot enlargement or migration to upper stems.'
                },
                'notes': 'Lower 3 leaf branches pruned on Day 1. Mulch applied. Monitoring progress over the next 7 days.',
                'engine_used': 'PlantCare AI Expert Knowledge & Vision Engine',
                'is_clarity_issue': 0,
                'clarity_notes': 'Photograph is sharp with distinct target lesions.',
                'created_at': '2026-10-10 10:15:00'
            },
            {
                'plant_name': 'Sweet Basil (Ocimum basilicum)',
                'plant_age': 'Vegetative (4 weeks)',
                'location': 'Indoor Balcony Planter',
                'soil_type': 'Organic potting mix with perlite',
                'watering_frequency': 'When top 1 inch feels dry (approx every 3 days)',
                'user_symptoms': 'None, checking routine vigor and growth',
                'image_filename': 'sample_healthy_leaf.jpg',
                'thumbnail_filename': 'sample_healthy_leaf.jpg',
                'health_status': 'Healthy',
                'disease_name': 'None (Healthy Plant)',
                'severity': 'None',
                'confidence_score': 0.98,
                'visible_symptoms': [
                    'Pristine, vibrant emerald green leaf surface',
                    'Uniform vein pattern without interveinal chlorosis or spotting',
                    'Full cellular turgor without wilting or edge curling'
                ],
                'growth_observations': [
                    'Vigorous leaf expansion with smooth leaf cuticle',
                    'Healthy node development and branching points',
                    'High chlorophyll density indicated by deep green coloration'
                ],
                'likely_causes': [
                    'Optimal photoperiod and balanced watering schedule',
                    'Proper soil aeration preventing root suffocation'
                ],
                'immediate_steps': [
                    'Pinch the top central stem just above a pair of leaves to encourage bushier lateral growth',
                    'Maintain current consistent watering regimen'
                ],
                'treatment_recommendations': [
                    'No disease treatments or fungicides needed',
                    'Periodic diluted fish emulsion or seaweed extract every 3-4 weeks supports lush foliage'
                ],
                'preventive_measures': [
                    'Ensure container drainage holes remain unblocked',
                    'Keep leaf surfaces dry when watering to prevent downy mildew'
                ],
                'personalized_care': {
                    'watering': 'Water when top 1 inch of soil is dry. Basil prefers consistently moist but never soggy soil.',
                    'sunlight': 'Thrives in 6-8 hours of warm bright sunlight or south-facing windowsill.',
                    'soil_drainage': 'Rich, moist, well-aerated potting soil with neutral pH (6.0 - 7.0).',
                    'nutrients': 'Light monthly feeding with balanced organic nitrogen liquid fertilizer.',
                    'temperature_humidity': 'Warm climate plant; protect from drafts below 15°C (59°F).',
                    'next_session': 'Check in 10-14 days to monitor branching after pinching.'
                },
                'notes': 'Baseline healthy scan. Pinched top tips to promote dense branching for kitchen harvesting.',
                'engine_used': 'PlantCare AI Expert Knowledge & Vision Engine',
                'is_clarity_issue': 0,
                'clarity_notes': 'Optimal lighting and crisp focal definition.',
                'created_at': '2026-10-12 14:30:00'
            }
        ]

        for record in sample_records:
            save_analysis(record)

    conn.close()
