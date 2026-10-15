/**
 * analyze.js - Plant Photo Upload, Validation, Preview & AI Diagnosis Workflow
 */

document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('plantImageInput');
    const dropzone = document.getElementById('dropzone');
    const previewContainer = document.getElementById('previewContainer');
    const previewImg = document.getElementById('previewImg');
    const previewMeta = document.getElementById('previewMeta');
    const removeBtn = document.getElementById('removeImageBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const form = document.getElementById('analysisForm');
    const scanOverlay = document.getElementById('scanOverlay');
    const scanStatusText = document.getElementById('scanStatusText');
    const resultsContainer = document.getElementById('resultsContainer');
    const errorAlert = document.getElementById('uploadErrorAlert');
    const errorMessage = document.getElementById('uploadErrorMessage');

    let currentFile = null;
    let selectedSample = null;

    // Allowed image formats and max size
    const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
    const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

    // -------------------------------------------------------------
    // Helper: Show & Hide Error
    // -------------------------------------------------------------
    function showError(msg) {
        if (!errorAlert || !errorMessage) return;
        errorMessage.textContent = msg;
        errorAlert.classList.remove('d-none');
        errorAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function clearError() {
        if (!errorAlert) return;
        errorAlert.classList.add('d-none');
    }

    // -------------------------------------------------------------
    // File Validation & Preview
    // -------------------------------------------------------------
    function handleFile(file) {
        clearError();
        selectedSample = null;

        if (!file) return;

        if (!ALLOWED_TYPES.includes(file.type)) {
            showError('Invalid file format. Please upload a JPG, JPEG, PNG, or WEBP image.');
            return;
        }

        if (file.size > MAX_SIZE_BYTES) {
            showError('File is too large. Maximum allowed size is 10 MB.');
            return;
        }

        currentFile = file;

        // Render preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            const sizeKb = (file.size / 1024).toFixed(1);
            previewMeta.textContent = `${file.name} • ${sizeKb} KB`;
            dropzone.classList.add('d-none');
            previewContainer.classList.remove('d-none');
            analyzeBtn.removeAttribute('disabled');
        };
        reader.readAsDataURL(file);
    }

    // File Input change
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                handleFile(e.target.files[0]);
            }
        });
    }

    // Drag and Drop
    if (dropzone) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('drag-over');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt.files && dt.files[0]) {
                handleFile(dt.files[0]);
            }
        });

        dropzone.addEventListener('click', () => {
            fileInput.click();
        });
    }

    // Remove / Replace image
    if (removeBtn) {
        removeBtn.addEventListener('click', () => {
            currentFile = null;
            selectedSample = null;
            if (fileInput) fileInput.value = '';
            previewImg.src = '';
            previewContainer.classList.add('d-none');
            dropzone.classList.remove('d-none');
            analyzeBtn.setAttribute('disabled', 'true');
            clearError();
        });
    }

    // -------------------------------------------------------------
    // Quick Demo Sample Selectors
    // -------------------------------------------------------------
    const sampleButtons = document.querySelectorAll('.btn-sample-demo');
    sampleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            clearError();
            const sampleType = btn.dataset.sample;
            selectedSample = sampleType;
            currentFile = null;
            if (fileInput) fileInput.value = '';

            if (sampleType === 'tomato_blight') {
                previewImg.src = '/static/images/sample_tomato_blight.jpg';
                previewMeta.textContent = 'Demo Sample: Tomato Leaf with Early Blight';
                document.getElementById('plantNameInput').value = 'Tomato (Solanum lycopersicum)';
                document.getElementById('userSymptomsInput').value = 'Dark brown target-like concentric spots on lower leaves with yellow halos.';
                document.getElementById('wateringSelect').value = 'Every 2-3 Days';
                document.getElementById('locationSelect').value = 'Outdoor Garden';
            } else if (sampleType === 'healthy_basil') {
                previewImg.src = '/static/images/sample_healthy_leaf.jpg';
                previewMeta.textContent = 'Demo Sample: Pristine Healthy Basil Leaf';
                document.getElementById('plantNameInput').value = 'Sweet Basil (Ocimum basilicum)';
                document.getElementById('userSymptomsInput').value = 'Healthy growth check. Vibrant green foliage without visible blemishes.';
                document.getElementById('wateringSelect').value = 'Every 2-3 Days';
                document.getElementById('locationSelect').value = 'Indoor / Balcony';
            }

            dropzone.classList.add('d-none');
            previewContainer.classList.remove('d-none');
            analyzeBtn.removeAttribute('disabled');
        });
    });

    // -------------------------------------------------------------
    // Clickable Symptom Tag Buttons
    // -------------------------------------------------------------
    const symptomTags = document.querySelectorAll('.symptom-tag-btn');
    const userSymptomsInput = document.getElementById('userSymptomsInput');

    symptomTags.forEach(tag => {
        tag.addEventListener('click', () => {
            tag.classList.toggle('active');
            const tagValue = tag.dataset.value;
            let currentText = userSymptomsInput.value.trim();

            if (tag.classList.contains('active')) {
                if (currentText && !currentText.endsWith(',')) {
                    currentText += ', ';
                }
                userSymptomsInput.value = currentText ? `${currentText}${tagValue}` : tagValue;
            } else {
                // Remove tag text
                const regex = new RegExp(`\\b${tagValue}\\b,?\\s*`, 'gi');
                userSymptomsInput.value = currentText.replace(regex, '').replace(/,\s*$/, '').trim();
            }
        });
    });

    // -------------------------------------------------------------
    // Form Submission & Animated Scan
    // -------------------------------------------------------------
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearError();

            if (!currentFile && !selectedSample) {
                showError('Please select or upload a plant photo before starting analysis.');
                return;
            }

            // Start scan animation
            scanOverlay.classList.remove('d-none');
            analyzeBtn.setAttribute('disabled', 'true');

            // Progressive status animation text
            const statusSteps = [
                'Verifying image resolution & chlorophyll spectrum...',
                'Extracting foliar texture & lesion patterns...',
                'Querying PlantCare AI pathology diagnostic model...',
                'Synthesizing integrated pest management & growth care...'
            ];

            let stepIdx = 0;
            const interval = setInterval(() => {
                stepIdx = (stepIdx + 1) % statusSteps.length;
                scanStatusText.textContent = statusSteps[stepIdx];
            }, 1800);

            const formData = new FormData(form);
            if (currentFile) {
                formData.set('plant_image', currentFile);
            }
            if (selectedSample) {
                formData.set('sample_image', selectedSample);
            }

            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    body: formData
                });

                clearInterval(interval);
                scanOverlay.classList.add('d-none');
                analyzeBtn.removeAttribute('disabled');

                const data = await response.json();

                if (!response.ok || !data.success) {
                    showError(data.error || 'Failed to complete analysis. Please try again.');
                    return;
                }

                // Render in-page results
                renderResults(data.data, data.redirect_url);

            } catch (err) {
                clearInterval(interval);
                scanOverlay.classList.add('d-none');
                analyzeBtn.removeAttribute('disabled');
                showError('Network error or server unavailable. Please check your connection.');
                console.error(err);
            }
        });
    }

    // -------------------------------------------------------------
    // Render Results In-Page
    // -------------------------------------------------------------
    function renderResults(res, detailUrl) {
        if (!resultsContainer) return;

        // Determine badge styling
        let statusBadge = '';
        if (res.health_status === 'Healthy') {
            statusBadge = '<span class="badge-status badge-healthy"><i class="bi bi-check-circle-fill"></i> Healthy Plant</span>';
        } else if (res.health_status === 'Potentially Affected') {
            statusBadge = '<span class="badge-status badge-affected"><i class="bi bi-exclamation-circle-fill"></i> Potentially Affected</span>';
        } else if (res.health_status === 'Diseased') {
            statusBadge = '<span class="badge-status badge-diseased"><i class="bi bi-x-circle-fill"></i> Diseased / Infested</span>';
        } else {
            statusBadge = '<span class="badge-status badge-unclear"><i class="bi bi-question-circle-fill"></i> Unclear Subject</span>';
        }

        // Severity badge
        let sevBadge = '';
        if (res.severity === 'Low') {
            sevBadge = '<span class="badge badge-sev-low px-3 py-1 rounded-pill">Severity: Low</span>';
        } else if (res.severity === 'Moderate') {
            sevBadge = '<span class="badge badge-sev-moderate px-3 py-1 rounded-pill">Severity: Moderate</span>';
        } else if (res.severity === 'High') {
            sevBadge = '<span class="badge badge-sev-high px-3 py-1 rounded-pill">Severity: High Alert</span>';
        }

        // Confidence score
        let confidenceHtml = '';
        if (res.confidence_score !== null && res.confidence_score !== undefined) {
            const pct = Math.round(res.confidence_score * 100);
            confidenceHtml = `<span class="badge bg-light text-dark border px-3 py-1 rounded-pill"><i class="bi bi-cpu text-success me-1"></i> ${pct}% AI Confidence</span>`;
        }

        // Engine indicator
        const engineBadge = res.is_live_ai 
            ? `<span class="badge bg-success text-white px-3 py-1 rounded-pill"><i class="bi bi-cloud-check-fill me-1"></i> Live Gemini Vision AI</span>`
            : `<span class="badge bg-warning text-dark px-3 py-1 rounded-pill"><i class="bi bi-shield-check me-1"></i> Offline Heuristic Engine</span>`;

        // Build lists
        const symptomsList = (res.visible_symptoms || []).map(s => `<li class="mb-2"><i class="bi bi-dot text-success fs-5"></i> ${s}</li>`).join('');
        const growthList = (res.growth_observations || []).map(g => `<li class="mb-2"><i class="bi bi-dot text-primary fs-5"></i> ${g}</li>`).join('');
        const causesList = (res.likely_causes || []).map(c => `<li class="mb-2"><i class="bi bi-arrow-right-short text-warning fs-5"></i> ${c}</li>`).join('');
        const immediateList = (res.immediate_steps || []).map(i => `<li class="mb-2"><i class="bi bi-check2-circle text-danger fs-5"></i> <strong>${i}</strong></li>`).join('');
        const treatmentsList = (res.treatment_recommendations || []).map(t => `<li class="mb-2"><i class="bi bi-shield-plus text-success fs-5"></i> ${t}</li>`).join('');
        const preventiveList = (res.preventive_measures || []).map(p => `<li class="mb-2"><i class="bi bi-flower1 text-info fs-5"></i> ${p}</li>`).join('');

        const care = res.personalized_care || {};

        resultsContainer.innerHTML = `
            <div class="card card-modern border-success mt-4 p-4 shadow-lg">
                <!-- Header Banner -->
                <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 pb-3 border-bottom mb-4">
                    <div>
                        <div class="d-flex align-items-center gap-2 mb-1">
                            ${statusBadge}
                            ${sevBadge}
                            ${confidenceHtml}
                            ${engineBadge}
                        </div>
                        <h2 class="mb-0 text-success">${res.plant_name}</h2>
                        <div class="text-muted fw-bold mt-1">Diagnosis: <span class="text-dark">${res.disease_name}</span></div>
                    </div>
                    <div class="d-flex gap-2">
                        <a href="${detailUrl}" class="btn btn-primary-pc btn-sm px-3">
                            <i class="bi bi-folder-check me-1"></i> Open Full Report
                        </a>
                        <button onclick="window.print()" class="btn btn-outline-secondary btn-sm px-3">
                            <i class="bi bi-printer me-1"></i> Print
                        </button>
                    </div>
                </div>

                ${res.fallback_reason ? `
                <div class="alert alert-warning d-flex align-items-center gap-2 py-2 mb-4" role="alert">
                    <i class="bi bi-info-circle-fill text-warning fs-5"></i>
                    <div><small><strong>Note:</strong> ${res.fallback_reason}</small></div>
                </div>` : ''}

                <!-- Diagnostic Breakdown Grid -->
                <div class="row g-4 mb-4">
                    <!-- Left: Visible Evidence & Causes -->
                    <div class="col-lg-6">
                        <div class="p-3 bg-light rounded-4 h-100 border">
                            <h5 class="fw-bold text-success mb-3"><i class="bi bi-eye-fill me-2"></i> Visible Symptoms Detected</h5>
                            <ul class="list-unstyled mb-4">${symptomsList || '<li class="text-muted">No adverse foliar symptoms detected.</li>'}</ul>

                            <h5 class="fw-bold text-primary mb-3"><i class="bi bi-graph-up-arrow me-2"></i> Growth Observations</h5>
                            <ul class="list-unstyled mb-4">${growthList || '<li class="text-muted">Canopy structure appears normal.</li>'}</ul>

                            ${causesList ? `
                            <h5 class="fw-bold text-warning-emphasis mb-3"><i class="bi bi-lightbulb-fill me-2"></i> Likely Causes</h5>
                            <ul class="list-unstyled mb-0">${causesList}</ul>` : ''}
                        </div>
                    </div>

                    <!-- Right: Immediate Action & IPM Treatments -->
                    <div class="col-lg-6">
                        <div class="p-3 bg-light rounded-4 h-100 border">
                            ${immediateList ? `
                            <div class="p-3 bg-white rounded-3 border-start border-4 border-danger mb-4 shadow-sm">
                                <h5 class="fw-bold text-danger mb-2"><i class="bi bi-exclamation-triangle-fill me-2"></i> Immediate Protective Steps</h5>
                                <ul class="list-unstyled mb-0">${immediateList}</ul>
                            </div>` : ''}

                            <h5 class="fw-bold text-success mb-3"><i class="bi bi-heart-pulse-fill me-2"></i> Recommended Treatments (IPM First)</h5>
                            <ul class="list-unstyled mb-4">${treatmentsList || '<li class="text-muted">No chemical or bio-treatments required.</li>'}</ul>

                            <h5 class="fw-bold text-info-emphasis mb-3"><i class="bi bi-shield-check me-2"></i> Preventive Practices</h5>
                            <ul class="list-unstyled mb-0">${preventiveList || '<li class="text-muted">Maintain standard hygiene.</li>'}</ul>
                        </div>
                    </div>
                </div>

                <!-- Personalized Growth Care Guidelines -->
                <h4 class="fw-bold mb-3"><i class="bi bi-compass-fill text-success me-2"></i> Personalized Growth Guidelines</h4>
                <div class="row g-3 mb-4">
                    <div class="col-md-4">
                        <div class="care-grid-card">
                            <div class="care-grid-icon"><i class="bi bi-droplet-fill text-info"></i></div>
                            <h6 class="fw-bold mb-1">Watering</h6>
                            <p class="small text-muted mb-0">${care.watering || 'Provide consistent moisture according to species requirements.'}</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="care-grid-card">
                            <div class="care-grid-icon"><i class="bi bi-sun-fill text-warning"></i></div>
                            <h6 class="fw-bold mb-1">Sunlight</h6>
                            <p class="small text-muted mb-0">${care.sunlight || 'Provide appropriate light exposure.'}</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="care-grid-card">
                            <div class="care-grid-icon"><i class="bi bi-moisture text-success"></i></div>
                            <h6 class="fw-bold mb-1">Soil & Drainage</h6>
                            <p class="small text-muted mb-0">${care.soil_drainage || 'Ensure loose, well-draining soil with organic compost.'}</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="care-grid-card">
                            <div class="care-grid-icon"><i class="bi bi-flower2 text-primary"></i></div>
                            <h6 class="fw-bold mb-1">Nutrients & Fertilizer</h6>
                            <p class="small text-muted mb-0">${care.nutrients || 'Apply balanced organic fertilizer during active growth.'}</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="care-grid-card">
                            <div class="care-grid-icon"><i class="bi bi-thermometer-half text-danger"></i></div>
                            <h6 class="fw-bold mb-1">Climate & Humidity</h6>
                            <p class="small text-muted mb-0">${care.temperature_humidity || 'Maintain adequate aeration around canopy.'}</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="care-grid-card">
                            <div class="care-grid-icon"><i class="bi bi-calendar2-check text-purple"></i></div>
                            <h6 class="fw-bold mb-1">Next Session</h6>
                            <p class="small text-muted mb-0">${care.next_session || 'Re-inspect in 7-10 days.'}</p>
                        </div>
                    </div>
                </div>

                <!-- Footer Disclaimer -->
                <div class="p-3 bg-light rounded-3 text-muted small border">
                    <i class="bi bi-shield-exclamation text-warning me-1"></i>
                    <strong>Agricultural Advisory Note:</strong> This assessment is generated using computer vision and AI models. Always inspect physical conditions, verify pesticide safety labels, and consult local agricultural extension officers before applying chemical treatments.
                </div>
            </div>
        `;

        resultsContainer.classList.remove('d-none');
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
});
