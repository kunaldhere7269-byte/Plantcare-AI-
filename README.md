# PlantCare AI – AI-Assisted Plant Growth Monitoring System
### College Community Engagement Project (CEP)

> **Tagline:** *"Smarter Plant Care Through AI"*  
> **Academic Context:** College Community Engagement Project (CEP) for Farmers, Gardeners, and Biology Students.  
> **Technology Stack:** Python (Flask), SQLite, OpenCV, Pillow, Google Gemini Vision API, Bootstrap 5, Chart.js.

---

## 1. Project Abstract
**PlantCare AI** is a complete, beginner-friendly, and functional web application engineered to bridge modern Artificial Intelligence and computer vision with sustainable agriculture. The platform allows smallholder farmers, school agricultural clubs, and urban terrace gardeners to upload plant leaf photographs, automatically identify plant health conditions and foliar pathogens, receive actionable Integrated Pest Management (IPM) treatment recommendations, and track plant vitality over time through a persistent monitoring journal.

Built with an emphasis on transparency, the system features a **Dual-Mode AI Engine**:
1. **Live Multimodal Vision AI Mode:** Powered by Google's Gemini Vision API when an API key is configured.
2. **Transparent Offline Heuristic Mode:** Powered by real OpenCV colorimetry (Laplacian blur variance, chlorophyll index, necrotic lesion ratio) and an agricultural pathology rule-base when running offline without an API key.

---

## 2. Problem Statement
Smallholder agriculturalists and community gardeners face frequent crop loss due to:
1. **Delayed Pathogen Identification:** Diseases such as Early Blight, Powdery Mildew, and Rust propagate exponentially before growers detect subtle early lesions.
2. **Excessive Chemical Overuse:** Lack of precise disease identification leads to excessive spraying of broad-spectrum synthetic pesticides, destroying beneficial insects (e.g., honeybees, ladybirds) and contaminating groundwater.
3. **Inaccessible Expert Diagnosis:** Professional plant pathologists and extension officers are rarely available on-demand for small community gardens.
4. **Misleading Digital Applications:** Many existing apps fabricate certainty on blurry images or claim to measure subterranean soil moisture or millimeter plant height from 2D photos.

---

## 3. Objectives
- **Accurate Foliar Screening:** Detect visible symptoms (chlorosis, necrotic spots, powdery coatings, wilting) from ordinary smartphone photographs.
- **Promote Ecological Sustainability:** Prioritize biological control, cultural sanitation, and Integrated Pest Management (IPM) before chemical pesticides.
- **Longitudinal Growth Tracking:** Maintain a persistent SQLite monitoring journal to compare past and present scans of the same crop.
- **Honest AI Design:** Guard against non-plant photos, flag blurry or poor-quality images, and transparently disclose whether live AI or offline heuristics are being used.
- **Low-Barrier Accessibility:** Ensure the application runs seamlessly on local Windows laptops with straightforward setup.

---

## 4. Main Features

### A. Modern Agricultural Landing Page
- Crisp green-and-white agricultural theme with glassmorphic cards and responsive navigation.
- Live dynamic counter calculating total analyses, plant varieties, and healthy vs. affected crops from actual database records.
- Feature highlights explaining disease detection, growth monitoring, and IPM recommendations.
- One-click sample test buttons for quick demonstrations.

### B. Plant Photo Upload & Live Diagnosis
- Drag-and-drop or file-picker upload supporting JPG, JPEG, PNG, and WEBP formats (max 10 MB).
- Real-time client-side preview with image dimensions, file size, and remove/replace controls.
- Optional growing context inputs: Plant Name (with autocomplete), Growth Stage, Location, Soil Type, Watering Routine, and clickable symptom tags.
- Animated laser-scanning overlay with progressive status feedback.

### C. Comprehensive Pathological Diagnosis
- Identified plant species and overall health status (`Healthy`, `Potentially Affected`, `Diseased`, `Unclear`).
- Suspected disease identification (e.g., *Early Blight*, *Powdery Mildew*, *Leaf Spot*, *Rust*, *Pests*).
- Severity assessment: `Low`, `Moderate`, or `High`.
- Confidence score (displayed only when provided by the live vision model; never fabricated).
- Concrete visible symptoms and evidence-grounded growth observations.

### D. Eco-Friendly IPM & Safe Treatments
- Immediate non-toxic containment measures (e.g., pruning infected foliage, sanitizing shears).
- Lower-risk biological and organic treatments (e.g., cold-pressed neem oil, *Bacillus subtilis*, copper soaps).
- Preventive cultural practices (crop rotation, clean straw mulching, ground-level drip irrigation).
- Strict pesticide safety precautions and reminders to consult local agricultural extension officers.

### E. Personalized Growth Monitoring Guidelines
- Ground-level watering recommendations.
- Photoperiod and sunlight requirements.
- Soil aeration and drainage advice.
- Organic nutrient and fertilizer suggestions.
- Next scheduled monitoring session timeline.

### F. Longitudinal Monitoring Journal & Scan Comparison
- Searchable and filterable history log stored in SQLite (`data/plantcare.db`).
- Interactive side-by-side comparison tool to track symptom changes between two scans of the same plant.
- In-place editable observation notes for recording treatments, weather changes, and pruning dates.

### G. Dynamic Analytics Dashboard
- Live metrics computed from actual saved database rows.
- Interactive Chart.js charts:
  - **Health Status Distribution** (Doughnut chart)
  - **Top Plant Varieties Monitored** (Bar chart)
  - **Diagnostic Activity Trend** (Line chart)
- Recent activity feed with high-performance thumbnail previews.
- Practical plant care tips and "How to Take a Good Plant Photo" educational guide.

---

## 5. Technology Stack

| Layer | Technologies Used | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (ES6), Bootstrap 5.3.3 | Responsive UI, drag-and-drop upload, laser scan animation |
| **Data Visualization** | Chart.js 4.4 | Interactive health and activity charts on dashboard |
| **Backend** | Python 3.10+ / 3.14, Flask 3.1, Werkzeug | RESTful routing, input validation, file upload security |
| **Image Processing** | Pillow (PIL) 12.3, OpenCV 4.13 | Image integrity verification, resizing, thumbnails, blur & colorimetry |
| **AI Vision Layer** | Google Gemini Vision API (REST v1beta) | Multimodal visual pathology diagnosis |
| **Offline Heuristics** | OpenCV + Expert Agricultural Pathology Rules | Transparent offline diagnostic fallback |
| **Database** | SQLite 3 | Persistent storage of analyses, symptoms, care notes, and metrics |

---

## 6. System Architecture

```
[ User Browser (Mobile / Desktop) ]
                |
                v (HTTP GET/POST - Multipart Form)
[ Flask Web Application (app.py) ]
      |                      |
      v                      v
[ Image Processor ]    [ Database Manager (database.py) ]
  - Pillow verification   - SQLite3 (data/plantcare.db)
  - Max dimension resize  - Seed sample records
  - Thumbnail generation  - Dynamic aggregations
  - OpenCV blur & color
      |
      v
[ AI Analyzer (services/ai_analyzer.py) ]
      |
      +---> If GEMINI_API_KEY is present in .env
      |       --> Call Google Gemini Vision REST API
      |
      +---> If GEMINI_API_KEY is absent / offline
              --> Transparent Offline Heuristic & Pathology Knowledge Engine
```

---

## 7. Project Directory Structure

```
CEP Project/
├── app.py                      # Main Flask application, routing & API endpoints
├── database.py                 # SQLite database schema, CRUD methods, and stats
├── requirements.txt            # Python dependencies (Flask, Pillow, python-dotenv, requests, opencv)
├── .env.example                # Template for environment configuration
├── .env                        # Local environment configuration file
├── .gitignore                  # Git ignore rules for uploads, databases, and secrets
├── README.md                   # College CEP Project Documentation
├── services/
│   ├── __init__.py
│   ├── ai_analyzer.py          # Dual AI engine (Gemini Vision API + Offline Heuristics)
│   └── image_processor.py      # Secure image processing & OpenCV feature extraction
├── static/
│   ├── css/
│   │   └── style.css           # Custom agricultural theme, glassmorphism & animations
│   ├── js/
│   │   ├── main.js             # Global bootstrap tooltips & utilities
│   │   ├── analyze.js          # Client upload, image preview, scan overlay & AJAX
│   │   └── dashboard.js        # Chart.js visualizations
│   └── images/
│       ├── hero_plant_tech.jpg # High-resolution hero banner
│       ├── photo_guide.jpg     # Smartphone plant photography guide image
│       ├── sample_tomato_blight.jpg
│       └── sample_healthy_leaf.jpg
├── templates/
│   ├── base.html               # Base layout, navbar, flash alerts & footer
│   ├── index.html              # Modern landing home page
│   ├── analyze.html            # Plant photo upload & diagnosis page
│   ├── dashboard.html          # Dynamic metrics, Chart.js graphs & seasonal tips
│   ├── history.html            # Monitoring journal, filters & search
│   ├── detail.html             # Detailed single inspection report & notes editor
│   ├── compare.html            # Side-by-side longitudinal comparison tool
│   ├── guide.html              # "How to Take a Good Plant Photo" visual guide
│   ├── faq.html                # Frequently Asked Questions
│   └── about.html              # College CEP documentation & architecture
├── uploads/                    # Secure local image storage
│   └── thumbnails/             # High-performance 400x400 thumbnails
└── data/                       # Local SQLite database (plantcare.db)
```

---

## 8. Installation & Setup Instructions

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14 installed on your computer.
- A modern web browser (Google Chrome, Microsoft Edge, Mozilla Firefox).

### Step 1: Open the Project Directory
Open your terminal (PowerShell or Command Prompt) and navigate to the project directory:
```powershell
cd "c:\Users\kunal\OneDrive\Documents\CEP Project"
```

### Step 2: Install Python Dependencies
Run pip using Python:
```powershell
python -m pip install -r requirements.txt
```

### Step 3: (Optional) Configure Google Gemini Vision API Key
If you want to use live multimodal AI analysis:
1. Obtain a free API key from [Google AI Studio](https://aistudio.google.com/).
2. Open the `.env` file in the project root and add your key:
```env
GEMINI_API_KEY=AIzaSy...your_actual_key_here
```
> **Note:** If you do not have an API key, leave it blank! PlantCare AI will automatically and transparently run in **Offline Heuristic & Knowledge Engine Mode**.

### Step 4: Run the Application
Start the Flask development server:
```powershell
python app.py
```

### Step 5: Open in Your Web Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 9. How to Test the Application

1. **Test the Landing Page (`/`):**
   - Review the metrics counter, feature cards, and 3-step workflow.
2. **Test One-Click Instant Demo Scans (`/analyze`):**
   - Click **"Tomato Early Blight Sample"** &rarr; The preview loads automatically. Click **"Analyze Plant Health"** to see the full diagnostic breakdown.
   - Click **"Healthy Basil Leaf Sample"** &rarr; Notice how the AI detects vibrant chlorophyll and reports zero disease symptoms.
3. **Test Custom Photo Upload (`/analyze`):**
   - Upload any plant photo from your device or use drag-and-drop.
   - Select optional context (growth stage, watering frequency, symptoms).
   - Observe the laser-scan animation and inspect the generated diagnosis and care guide.
4. **Test the Monitoring History (`/history`):**
   - Filter records by health state (`Healthy`, `Diseased`) or search for "Tomato".
   - Click **"Full Report"** to view high-resolution photos and update observation notes.
5. **Test Side-by-Side Comparison (`/compare`):**
   - Select Scan A and Scan B from the dropdowns to compare symptoms and recovery across days.
6. **Test the Dashboard (`/dashboard`):**
   - Verify that the Doughnut chart, Bar chart, and Line chart reflect your actual saved records.

---

## 10. Beginner Explanation of Important Files
*(Helpful for explaining the project to your college professor or external evaluator)*

1. **`app.py`**:
   The controller and entry point. It receives web requests from the user, coordinates image saving and AI diagnosis, interacts with the database, and returns HTML pages or JSON responses.
2. **`database.py`**:
   The persistence manager. It creates the SQLite database, stores analysis records, handles user notes updates, and calculates live dashboard statistics like total scans and health status counts.
3. **`services/image_processor.py`**:
   The computer vision pre-processor. It ensures files are genuine images, resizes heavy photos for fast loading, generates square thumbnails, and uses OpenCV to check image sharpness (blur detection) and greenness ratios.
4. **`services/ai_analyzer.py`**:
   The diagnostic brain. It checks if a Gemini API key is configured. If yes, it communicates with Google's vision AI. If no, it transparently uses an agricultural pathology knowledge base to analyze the leaf without making fake claims.
5. **`static/js/analyze.js`**:
   The frontend upload controller. It creates the image preview instantly when you pick a file, handles drag-and-drop, runs the laser scan animation, and sends data to Flask asynchronously without reloading the page.
6. **`templates/base.html`**:
   The master layout. It contains the navigation bar, responsive footer, agricultural design theme, and the AI engine status badge shown at the top.

---

## 11. Limitations and Future Scope

### Current Limitations:
- **2D Visual Limitations:** The system cannot scientifically measure subterranean soil pH, moisture percentages, or millimeter root depth from an ordinary 2D photo.
- **Microscopic Pathogens:** Viral pathogens that cause subtle cellular mosaic patterns may require molecular PCR confirmation.
- **Lighting Sensitivity:** Heavy flash glare or pitch-black night photography can impede accurate lesion identification.

### Future Scope:
- **IoT Sensor Integration:** Connect low-cost ESP32 soil moisture and temperature sensors to feed real-time telemetry alongside photographic scans.
- **Vernacular Language Support:** Add multi-language voice guidance in regional languages (e.g., Hindi, Marathi, Telugu, Tamil, Bengali) for non-English-speaking rural farmers.
- **Offline Progressive Web App (PWA):** Enable full offline caching so farmers can use the application in remote areas with zero cellular connectivity.

---

## 12. College Project Credits & License
- **Project:** PlantCare AI – AI-Assisted Plant Growth Monitoring System
- **Category:** Community Engagement Project (CEP)
- **License:** Open Source for Academic & Community Educational Use
