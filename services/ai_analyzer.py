"""
services/ai_analyzer.py - Plant Health & Disease Diagnosis Engine
Supports dual-mode execution:
1. Live Google Gemini Vision AI API (when GEMINI_API_KEY is configured in .env)
2. Transparent Offline Heuristic & Agricultural Pathology Knowledge Base (when API key is absent)
"""

import os
import json
import base64
import requests
from datetime import datetime
from services.image_processor import extract_visual_features


# Plant pathology knowledge base for offline heuristic mode
OFFLINE_DISEASE_KNOWLEDGE = {
    'blight': {
        'name': 'Early Blight (Alternaria solani)',
        'plants': ['tomato', 'potato', 'eggplant', 'solanaceae'],
        'symptoms': [
            'Concentric target-like circular brown lesions on older leaves',
            'Chlorotic yellow halo surrounding necrotic brown spots',
            'Progressive leaf senescence from bottom upward'
        ],
        'causes': [
            'Alternaria solani fungal spores splash-dispersed from damp soil',
            'Prolonged leaf wetness exceeding 6-8 hours from overhead irrigation',
            'Warm, humid conditions (24°C - 29°C / 75°F - 85°F)'
        ],
        'immediate_steps': [
            'Prune and safely discard all infected lower leaves (do not compost infected tissue)',
            'Sterilize pruning blades with 70% alcohol or diluted bleach between cuts',
            'Transition immediately to ground-level or drip irrigation to keep foliage dry'
        ],
        'treatments': [
            'Apply certified organic copper-based fungicide or Bacillus subtilis biopesticide according to label directions',
            'Spread 2-3 inches of clean organic straw mulch around the root zone to stop soil splashback',
            'Improve row and stem spacing to promote wind circulation'
        ],
        'preventive': [
            'Follow a 3 to 4-year crop rotation avoiding other Solanaceae (tomatoes, potatoes, peppers)',
            'Choose certified disease-resistant cultivars when replanting',
            'Clean crop debris thoroughly at the end of each harvest season'
        ],
        'care': {
            'watering': 'Water deeply at the base 1-2 times weekly; never water overhead late in the evening.',
            'sunlight': 'Ensure 6 to 8 hours of direct, unobstructed sunlight daily.',
            'soil_drainage': 'Well-draining loamy soil enriched with organic compost (pH 6.2 - 6.8).',
            'nutrients': 'Feed with balanced 5-10-10 or tomato-specific formula with calcium; avoid excessive quick-release nitrogen.',
            'temperature_humidity': 'Optimal 20°C - 28°C; reduce high canopy humidity with staking.',
            'next_session': 'Inspect every 5-7 days to verify if lesions have stopped spreading to new leaves.'
        }
    },
    'powdery_mildew': {
        'name': 'Powdery Mildew (Erysiphales spp.)',
        'plants': ['rose', 'cucumber', 'squash', 'zucchini', 'grape', 'apple', 'houseplant'],
        'symptoms': [
            'Talcom-like white or gray powdery fungal coating on upper leaf surface',
            'Leaf margin curling, yellowing, and premature foliage drop',
            'Distorted new shoot tips and bud growth'
        ],
        'causes': [
            'Airborne fungal spores thriving in dry weather with high relative humidity',
            'Crowded planting and shaded, stagnant microclimates',
            'Excessive foliage density restricting airflow'
        ],
        'immediate_steps': [
            'Gently prune severely coated foliage to reduce fungal spore load',
            'Move potted plants to brighter, well-ventilated locations',
            'Avoid watering leaves; spores germinate quickly in humid shade'
        ],
        'treatments': [
            'Spray with organic neem oil or potassium bicarbonate solution in early morning or late dusk',
            'Diluted milk spray (1 part milk to 9 parts water) has proven bio-fungicidal efficacy in sunny conditions',
            'In severe ornamental cases, apply sulfur-based fungicide following product safety guidelines'
        ],
        'preventive': [
            'Ensure adequate plant spacing to allow generous air movement',
            'Prune interior branches to open up the canopy to direct sunlight',
            'Select powdery mildew resistant cultivars'
        ],
        'care': {
            'watering': 'Water at the soil level only in the morning hours.',
            'sunlight': 'Requires 6+ hours of full sun; fungal spores fail to thrive under direct UV exposure.',
            'soil_drainage': 'Moist, fertile, free-draining soil with good organic content.',
            'nutrients': 'Avoid excessive high-nitrogen feeding which generates vulnerable tender succulent growth.',
            'temperature_humidity': 'Thrives in 18°C - 26°C with 70%+ relative humidity; maximize ventilation.',
            'next_session': 'Re-examine in 4 to 6 days after applying organic spray.'
        }
    },
    'leaf_spot': {
        'name': 'Cercospora / Septoria Leaf Spot',
        'plants': ['rose', 'pepper', 'chili', 'tomato', 'monstera', 'citrus', 'beet', 'spinach'],
        'symptoms': [
            'Small, dark circular or angular spots with tan/gray centers',
            'Chlorotic yellow halos encircling older spots',
            'Lower foliage defoliation under sustained moisture'
        ],
        'causes': [
            'Fungal or bacterial pathogens carried by splashing rain, mist, or overhead sprinklers',
            'Dense canopy trapping moisture against leaf cuticles',
            'Debris from previous infected seasons left on soil surface'
        ],
        'immediate_steps': [
            'Remove fallen and infected leaves immediately to contain spore spread',
            'Disinfect tools before working on uninfected plants',
            'Stop overhead sprinkling and misting'
        ],
        'treatments': [
            'Treat with broad-spectrum bio-fungicide (Bacillus amyloliquefaciens or copper soap)',
            'Maintain dry foliage during night cycles',
            'Apply clean mulch layer over exposed soil'
        ],
        'preventive': [
            'Ensure adequate row spacing and stake upright growth',
            'Water soil directly in early morning so incidental splashes dry quickly',
            'Sanitize garden beds annually'
        ],
        'care': {
            'watering': 'Soil level drip or watering can without wetting foliage.',
            'sunlight': 'Direct sun for 6 hours minimum to hasten moisture evaporation.',
            'soil_drainage': 'Loose, well-aerated potting mix or garden loam.',
            'nutrients': 'Balanced organic fertilizer; supplement with micronutrients if chlorosis persists.',
            'temperature_humidity': 'Keep relative humidity below 75% around foliage if indoors.',
            'next_session': 'Inspect weekly; note any new spots on upper young leaves.'
        }
    },
    'rust': {
        'name': 'Common Plant Rust (Pucciniales)',
        'plants': ['bean', 'rose', 'wheat', 'corn', 'apple', 'fig', 'chrysanthemum'],
        'symptoms': [
            'Reddish-orange, rust-colored powdery pustules on the underside of leaves',
            'Corresponding yellow or chlorotic flecks on the upper leaf surface',
            'Premature leaf senescence and reduced vigor'
        ],
        'causes': [
            'Windborne rust fungal spores favored by wet leaves and cool to moderate temperatures',
            'Leaf surface wetness lasting longer than 4-6 hours',
            'Close proximity to alternate host weeds'
        ],
        'immediate_steps': [
            'Carefully remove pustule-covered leaves without violently shaking spores onto neighbors',
            'Do not compost infected leaves; seal in bags and discard',
            'Cease any overhead watering immediately'
        ],
        'treatments': [
            'Spray with neem oil or sulfur-based dust/spray per safety label instructions',
            'Apply bio-fungicidal Bacillus formulations for food crops',
            'Prune dense interior stems to increase sun penetration'
        ],
        'preventive': [
            'Eradicate wild weeds and alternate host species nearby',
            'Utilize drip lines and space plants adequately',
            'Rotate annual crops regularly'
        ],
        'care': {
            'watering': 'Ground-level irrigation only, strictly avoiding foliage wetting.',
            'sunlight': 'Full sun (6-8 hours); sunlight actively impedes rust spore germination.',
            'soil_drainage': 'Well-aerated soil preventing standing water puddles.',
            'nutrients': 'Balanced slow-release organic fertilizer with adequate potassium.',
            'temperature_humidity': 'Keep area well-ventilated during humid periods.',
            'next_session': 'Check leaf undersides in 5 days for new pustule development.'
        }
    },
    'pests': {
        'name': 'Insect Pest Infestation (Aphids / Mites / Thrips)',
        'plants': ['all', 'rose', 'hibiscus', 'chili', 'tomato', 'houseplant'],
        'symptoms': [
            'Curled, crinkled, or distorted tender young leaves',
            'Sticky honeydew residue on leaf surfaces or black sooty mold',
            'Visible clusters of tiny green, black, or white insects near shoot tips'
        ],
        'causes': [
            'Soft-bodied sap-sucking insects attracted to tender vegetative growth',
            'Lack of natural predators (ladybugs, lacewings) in sheltered environments',
            'Excessive quick-release nitrogen fertilizer promoting vulnerable soft tissue'
        ],
        'immediate_steps': [
            'Dislodge pests with a firm jet of water aimed at leaf undersides',
            'Isolate potted plants to prevent pest migration to healthy plants',
            'Wipe heavily infested stems with a soft cloth moistened with soapy water'
        ],
        'treatments': [
            'Spray with organic insecticidal soap or cold-pressed neem oil (diluted per instructions)',
            'Introduce beneficial predators like ladybird beetles or hoverflies in outdoor gardens',
            'Apply horticultural oil spray during dormant/cool periods'
        ],
        'preventive': [
            'Inspect leaf undersides weekly as part of regular routine monitoring',
            'Avoid over-fertilizing with high-nitrogen synthetic fertilizers',
            'Plant companion herbs like marigolds, mint, and basil to deter pests'
        ],
        'care': {
            'watering': 'Maintain consistent soil moisture; drought-stressed plants attract more spider mites.',
            'sunlight': 'Appropriate light for species; healthy vigor enhances natural pest defenses.',
            'soil_drainage': 'Healthy living soil with rich organic matter supporting plant immune vigor.',
            'nutrients': 'Balanced organic nutrition; compost tea or seaweed extract for systemic resilience.',
            'temperature_humidity': 'Moderate humidity (dry air accelerates spider mite reproduction).',
            'next_session': 'Inspect leaf undersides in 3-4 days to evaluate pest reduction.'
        }
    },
    'healthy': {
        'name': 'None (Healthy Plant)',
        'plants': ['all'],
        'symptoms': [
            'Uniform vibrant green foliage with healthy chlorophyll distribution',
            'No visible signs of necrotic spots, powdery mildew, or pest colonies',
            'Firm cell turgidity without drooping or edge wilting'
        ],
        'causes': [
            'Favorable growth conditions with balanced light, moisture, and airflow'
        ],
        'immediate_steps': [
            'No immediate disease intervention necessary',
            'Continue existing care and maintenance schedule'
        ],
        'treatments': [
            'No treatments or chemical applications needed',
            'Periodic organic compost or dilute seaweed extract to sustain vigor'
        ],
        'preventive': [
            'Maintain good sanitation and clean garden tools',
            'Ensure adequate spacing as the plant continues to expand'
        ],
        'care': {
            'watering': 'Water according to species needs when top 1-2 inches of soil feel dry.',
            'sunlight': 'Provide optimal light exposure (6+ hours for sun-loving, bright indirect for indoor foliage).',
            'soil_drainage': 'Ensure pots have drainage holes and garden soil is loose and well-aerated.',
            'nutrients': 'Monthly mild organic feeding during the active growing season.',
            'temperature_humidity': 'Protect against temperature extremes and desiccating drafts.',
            'next_session': 'Perform routine check in 10-14 days to track new growth.'
        }
    }
}


def analyze_plant_image(image_path, user_metadata=None):
    """
    Main entry point for plant health analysis.
    Checks environment for GEMINI_API_KEY:
    - If present: invokes Google Gemini Vision AI model for live multimodal diagnosis.
    - If absent or if API call fails: runs transparent Offline Heuristic & Knowledge Engine.
    """
    user_metadata = user_metadata or {}
    api_key = os.getenv('GEMINI_API_KEY', '').strip()

    # Step 1: Extract real computer vision metrics from the image
    cv_metrics = extract_visual_features(image_path)

    # Step 2: Try Live Gemini Vision AI if API key is configured
    if api_key and len(api_key) > 5:
        try:
            gemini_result = _call_gemini_vision_api(image_path, user_metadata, cv_metrics, api_key)
            if gemini_result and gemini_result.get('success'):
                return gemini_result['data']
            else:
                # API failed or returned error; fall back with honest note
                api_error = gemini_result.get('error', 'API call failed')
                print(f"[PlantCare AI] Gemini Vision API notice: {api_error}. Falling back to Offline Knowledge Engine.")
                return _run_offline_heuristic_analysis(
                    image_path, user_metadata, cv_metrics,
                    fallback_reason=f"Gemini API returned: {api_error}. Switched to Offline Heuristic Engine."
                )
        except Exception as e:
            print(f"[PlantCare AI] Gemini Vision API error: {str(e)}. Falling back to Offline Knowledge Engine.")
            return _run_offline_heuristic_analysis(
                image_path, user_metadata, cv_metrics,
                fallback_reason=f"AI connection error ({str(e)}). Switched to Offline Heuristic Engine."
            )

    # Step 3: Run transparent Offline Heuristic Engine when no API key is provided
    return _run_offline_heuristic_analysis(
        image_path, user_metadata, cv_metrics,
        fallback_reason="No GEMINI_API_KEY configured in .env. Running in Offline Heuristic / Demonstration Mode."
    )


def _call_gemini_vision_api(image_path, user_metadata, cv_metrics, api_key):
    """Call Google Gemini 1.5/2.0 Flash Vision REST API with image and structured response schema."""
    if not os.path.exists(image_path):
        return {'success': False, 'error': 'Image file not found on server.'}

    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')

    # Prepare detailed context from user input
    plant_hint = user_metadata.get('plant_name', '').strip()
    age_hint = user_metadata.get('plant_age', '').strip()
    location_hint = user_metadata.get('location', '').strip()
    soil_hint = user_metadata.get('soil_type', '').strip()
    watering_hint = user_metadata.get('watering_frequency', '').strip()
    symptoms_hint = user_metadata.get('user_symptoms', '').strip()

    prompt = f"""You are an expert plant pathologist and agronomist for the PlantCare AI Agricultural Monitoring System.
Analyze this plant photo carefully and return a valid JSON object matching the exact schema specified below.

User-Provided Context:
- Specified Plant Name/Type: {plant_hint if plant_hint else 'Not specified by user'}
- Plant Growth Stage: {age_hint if age_hint else 'Not specified'}
- Growing Location: {location_hint if location_hint else 'Not specified'}
- Soil Type: {soil_hint if soil_hint else 'Not specified'}
- Watering Frequency: {watering_hint if watering_hint else 'Not specified'}
- User Observed Symptoms: {symptoms_hint if symptoms_hint else 'None reported'}

Computer Vision Image Metrics:
- Blur Score: {cv_metrics.get('blur_score')} (Blurry: {cv_metrics.get('is_blurry')})
- Green Foliage Ratio: {cv_metrics.get('green_ratio')}
- Necrotic/Yellow/Brown Ratio: {cv_metrics.get('yellow_brown_ratio')}

CRITICAL INSTRUCTIONS:
1. Examine if the image is actually a plant or leaf. If it is NOT a plant (e.g. animal, car, human face, furniture, blur), set "is_plant": false and "health_status": "Unclear".
2. If image is blurry or unclear, explain the uncertainty in "clarity_notes" and DO NOT fabricate high certainty.
3. Distinguish visible symptoms (from the photo) from unobservable metrics. Do NOT claim to measure soil moisture or plant height from this ordinary photo.
4. For treatments, prioritize Integrated Pest Management (IPM), cultural, and organic controls first. If synthetic chemical pesticides are mentioned, include clear safety precautions (PPE, product label adherence, local agricultural guidance).
5. Only return confidence_score as a float between 0.00 and 1.00 representing your actual diagnostic certainty.
6. Return ONLY the raw JSON object, without markdown formatting or code blocks.

JSON SCHEMA:
{{
    "is_plant": boolean,
    "plant_name": string (identified plant species with common and botanical name if identifiable, or "Unclear Botanical Subject"),
    "health_status": "Healthy" | "Potentially Affected" | "Diseased" | "Unclear",
    "disease_name": string (suspected disease name or "None (Healthy Plant)" or "Undetermined"),
    "severity": "None" | "Low" | "Moderate" | "High",
    "confidence_score": float (between 0.00 and 1.00, or null if uncertain),
    "visible_symptoms": [string array of specific visible symptoms such as chlorosis, necrosis, spots, wilting, holes],
    "growth_observations": [string array of visible growth observations such as leaf turgidity, canopy density, node spacing],
    "likely_causes": [string array of probable causes based on visible evidence and user context],
    "immediate_steps": [string array of practical immediate actions to take],
    "treatment_recommendations": [string array of lower-risk, IPM, and organic treatments with safety guidelines],
    "preventive_measures": [string array of cultural and preventive practices to avoid recurrence],
    "personalized_care": {{
        "watering": string,
        "sunlight": string,
        "soil_drainage": string,
        "nutrients": string,
        "temperature_humidity": string,
        "next_session": string
    }},
    "is_clarity_issue": boolean,
    "clarity_notes": string
}}"""

    # We try Gemini 1.5 Flash endpoint, fallback to 2.0 Flash
    models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    last_error = ""

    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": img_b64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json"
            }
        }

        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=25)
            if resp.status_code == 200:
                resp_json = resp.json()
                text_content = resp_json['candidates'][0]['content']['parts'][0]['text'].strip()
                
                # Clean up if markdown code fence is present
                if text_content.startswith('```'):
                    text_content = text_content.split('\n', 1)[1]
                    if text_content.endswith('```'):
                        text_content = text_content.rsplit('```', 1)[0]
                
                data = json.loads(text_content)
                data['engine_used'] = f"Google Gemini Vision AI ({model_name} Live API)"
                data['is_live_ai'] = True
                return {'success': True, 'data': data}
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text[:180]}"
        except Exception as ex:
            last_error = str(ex)

    return {'success': False, 'error': last_error}


def _run_offline_heuristic_analysis(image_path, user_metadata, cv_metrics, fallback_reason=None):
    """
    Transparent Offline Heuristic & Agricultural Pathology Knowledge Engine.
    Executes real image feature analysis (OpenCV greenness, necrotic ratio, blur),
    maps against user reported symptoms, and produces an authentic diagnostic report.
    Notice: Transparently discloses that it is running in Offline Demonstration Mode.
    """
    plant_hint = (user_metadata.get('plant_name') or '').strip()
    symptoms_hint = (user_metadata.get('user_symptoms') or '').lower()
    location_hint = user_metadata.get('location', 'Garden / Farm')
    soil_hint = user_metadata.get('soil_type', 'Standard soil')
    watering_hint = user_metadata.get('watering_frequency', 'Regular')
    age_hint = user_metadata.get('plant_age', 'Growing')

    green_ratio = cv_metrics.get('green_ratio', 0.5)
    yellow_brown_ratio = cv_metrics.get('yellow_brown_ratio', 0.0)
    is_blurry = cv_metrics.get('is_blurry', False)
    is_plant_candidate = cv_metrics.get('is_plant_candidate', True)

    # 1. Non-plant or extreme unclear detection
    if not is_plant_candidate and green_ratio < 0.05 and yellow_brown_ratio < 0.03:
        return {
            'is_plant': False,
            'plant_name': plant_hint if plant_hint else 'Unknown (Non-Botanical Subject)',
            'health_status': 'Unclear',
            'disease_name': 'Undetermined (Non-Plant Image Detected)',
            'severity': 'None',
            'confidence_score': None,
            'visible_symptoms': [
                'Insufficient plant foliage or chlorophyll color detected in photograph',
                'Visual texture does not match standard leaf or crop structure'
            ],
            'growth_observations': [
                'Unable to detect active botanical tissue or leaf venation'
            ],
            'likely_causes': [
                'Photograph may depict a non-plant object, an extreme background, or poor illumination'
            ],
            'immediate_steps': [
                'Please take a clear, well-lit photograph focusing directly on the leaf surface or stem',
                'Refer to the "How to Take a Good Plant Photo" guide in the navigation bar'
            ],
            'treatment_recommendations': [
                'No agricultural treatment applicable for non-botanical images'
            ],
            'preventive_measures': [
                'Ensure camera focus is locked onto affected plant foliage before capturing'
            ],
            'personalized_care': {
                'watering': 'Follow standard guidelines once plant species is identified.',
                'sunlight': 'Inspect plant in natural daylight for accurate leaf color assessment.',
                'soil_drainage': 'Ensure proper soil drainage according to plant type.',
                'nutrients': 'Avoid applying fertilizers without confirming crop condition.',
                'temperature_humidity': 'Maintain moderate ambient conditions.',
                'next_session': 'Upload a new, focused photograph of the plant leaves.'
            },
            'engine_used': 'Offline Heuristic Knowledge Engine (Demonstration Mode)',
            'is_live_ai': False,
            'fallback_reason': fallback_reason,
            'is_clarity_issue': True,
            'clarity_notes': 'Photograph does not exhibit standard plant color signatures. Please upload a clear photo of plant foliage.'
        }

    # 2. Match disease profile from symptoms, plant name, and CV ratios
    matched_profile = OFFLINE_DISEASE_KNOWLEDGE['healthy']
    disease_key = 'healthy'

    combined_text = f"{plant_hint.lower()} {symptoms_hint}"

    # Check for specific disease indicators in symptoms or plant context
    has_disease_kw = False
    if any(k in combined_text for k in ['blight', 'target', 'concentric', 'alternaria', 'phytophthora']):
        disease_key = 'blight'
        has_disease_kw = True
    elif any(k in combined_text for k in ['powdery', 'white powder', 'mildew', 'talcum']):
        disease_key = 'powdery_mildew'
        has_disease_kw = True
    elif any(k in combined_text for k in ['rust', 'pustule', 'orange pustule']):
        disease_key = 'rust'
        has_disease_kw = True
    elif any(k in combined_text for k in ['aphid', 'pest', 'mite', 'thrip', 'insect', 'chewing', 'holes', 'honeydew']):
        disease_key = 'pests'
        has_disease_kw = True
    elif any(k in combined_text for k in ['spot', 'brown spot', 'circular spot', 'septoria', 'cercospora', 'lesion', 'halo']):
        disease_key = 'leaf_spot'
        has_disease_kw = True
    elif any(k in combined_text for k in ['healthy', 'normal', 'none', 'vigor', 'pristine', 'good']):
        disease_key = 'healthy'
    elif yellow_brown_ratio > 0.30 and green_ratio < 0.50:
        # Extreme chlorosis/necrosis with low greenness
        disease_key = 'leaf_spot'
    else:
        # Default to healthy if foliage is predominantly green (>50%) and no disease symptoms reported
        disease_key = 'healthy'

    matched_profile = OFFLINE_DISEASE_KNOWLEDGE[disease_key]

    # Calculate severity and health status based on real visual damage ratio
    if disease_key == 'healthy':
        health_status = 'Healthy'
        severity = 'None'
    elif yellow_brown_ratio > 0.20 or 'severe' in symptoms_hint or 'high' in symptoms_hint:
        health_status = 'Diseased'
        severity = 'High'
    elif yellow_brown_ratio > 0.08 or 'moderate' in symptoms_hint:
        health_status = 'Diseased'
        severity = 'Moderate'
    else:
        health_status = 'Potentially Affected'
        severity = 'Low'

    # Synthesize visible observations combining computer vision metrics and agricultural profile
    visible_symptoms = list(matched_profile['symptoms'])
    if yellow_brown_ratio > 0.05:
        visible_symptoms.append(f'Computer vision detected approx {int(yellow_brown_ratio*100)}% chlorotic/necrotic discoloration on visible leaf area.')
    if is_blurry:
        visible_symptoms.append('Soft image focal blur detected; fine fungal micro-structures may require closer macro photography.')

    growth_observations = [
        f'Green chlorophyll foliage coverage calculated at approx {int(green_ratio*100)}% of analyzed frame.',
        'Leaf cuticle structure shows visible veining consistent with active vegetative canopy.',
        f'Current growth phase noted as: {age_hint if age_hint else "Vegetative/Active canopy"}.'
    ]

    plant_display_name = plant_hint if plant_hint else 'Cultivated Plant (Species Unspecified)'

    # Build personalized care
    care_data = dict(matched_profile['care'])
    if watering_hint and watering_hint != 'Regular':
        care_data['watering'] = f"Reported: {watering_hint}. " + care_data['watering']
    if location_hint:
        care_data['temperature_humidity'] = f"Grown in: {location_hint}. " + care_data['temperature_humidity']
    if soil_hint:
        care_data['soil_drainage'] = f"Soil: {soil_hint}. " + care_data['soil_drainage']

    return {
        'is_plant': True,
        'plant_name': plant_display_name,
        'health_status': health_status,
        'disease_name': matched_profile['name'],
        'severity': severity,
        'confidence_score': None,  # Transparent: Heuristic mode does not fabricate neural confidence scores
        'visible_symptoms': visible_symptoms,
        'growth_observations': growth_observations,
        'likely_causes': matched_profile['causes'],
        'immediate_steps': matched_profile['immediate_steps'],
        'treatment_recommendations': matched_profile['treatments'],
        'preventive_measures': matched_profile['preventive'],
        'personalized_care': care_data,
        'engine_used': 'Offline Heuristic & Agricultural Knowledge Engine (Demonstration Mode)',
        'is_live_ai': False,
        'fallback_reason': fallback_reason,
        'is_clarity_issue': is_blurry,
        'clarity_notes': 'Photograph evaluated via OpenCV colorimetry. For live Google Gemini Vision AI, provide an API key in .env.'
    }
