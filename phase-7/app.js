/* ═══════════════════════════════════════════════════════════
   Zomato AI Recommender — App Logic
   ═══════════════════════════════════════════════════════════ */

(function () {
    'use strict';

    // ── Config ──────────────────────────────────────────────
    const API_URL = 'http://localhost:5000';

    // ── DOM refs ────────────────────────────────────────────
    const form = document.getElementById('preference-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.cta-btn__text');
    const btnLoading = submitBtn.querySelector('.cta-btn__loading');

    const errorBanner = document.getElementById('error-banner');
    const errorText = document.getElementById('error-text');
    const errorClose = document.getElementById('error-close');

    const resultsSection = document.getElementById('results-section');
    const resultsGrid = document.getElementById('results-grid');
    const skeletonGrid = document.getElementById('skeleton-grid');
    const emptyState = document.getElementById('empty-state');
    const footerModel = document.getElementById('footer-model');

    const ratingInput = document.getElementById('min-rating');
    const ratingMinus = document.getElementById('rating-minus');
    const ratingPlus = document.getElementById('rating-plus');

    // Area dropdown refs
    const areaDropdown = document.getElementById('area-dropdown');
    const areaInput = document.getElementById('area-input');
    const areaList = document.getElementById('area-list');

    // Cuisine multiselect refs
    const cuisineMulti = document.getElementById('cuisine-multiselect');
    const cuisineInput = document.getElementById('cuisine-input');
    const cuisineChips = document.getElementById('cuisine-chips');
    const cuisineList = document.getElementById('cuisine-list');

    // Price slider refs
    const priceMinInput = document.getElementById('price-min');
    const priceMaxInput = document.getElementById('price-max');
    const priceLabelMin = document.getElementById('price-label-min');
    const priceLabelMax = document.getElementById('price-label-max');
    const rangeFill = document.getElementById('range-fill');

    // Stats
    const statAreas = document.getElementById('stat-areas');
    const statCuisines = document.getElementById('stat-cuisines');

    // ── State ───────────────────────────────────────────────
    let allAreas = [];
    let allCuisines = [];
    let selectedArea = '';
    let selectedCuisines = [];
    let areaHighlightIdx = -1;
    let cuisineHighlightIdx = -1;

    // ══════════════════════════════════════════════════════════
    // 1. Fetch metadata on load
    // ══════════════════════════════════════════════════════════
    async function fetchMetadata() {
        try {
            const res = await fetch(`${API_URL}/metadata`);
            if (!res.ok) return;
            const data = await res.json();
            allAreas = data.areas || [];
            allCuisines = data.cuisines || [];
            statAreas.textContent = allAreas.length;
            statCuisines.textContent = allCuisines.length;
        } catch { /* silently fail — dropdowns will stay empty */ }
    }
    fetchMetadata();

    // ══════════════════════════════════════════════════════════
    // 2. Searchable Area Dropdown
    // ══════════════════════════════════════════════════════════
    function renderAreaList(filter = '') {
        const f = filter.toLowerCase();
        const items = f ? allAreas.filter(a => a.toLowerCase().includes(f)) : allAreas;
        areaList.innerHTML = items.map(a =>
            `<li role="option" data-value="${escapeAttr(a)}" class="${a === selectedArea ? 'selected' : ''}">${escapeHtml(a)}</li>`
        ).join('');
        areaHighlightIdx = -1;
    }

    areaInput.addEventListener('focus', () => {
        areaDropdown.classList.add('open');
        renderAreaList(areaInput.value);
    });

    areaInput.addEventListener('input', () => {
        areaDropdown.classList.add('open');
        renderAreaList(areaInput.value);
    });

    areaInput.addEventListener('keydown', (e) => {
        const items = areaList.querySelectorAll('li');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            areaHighlightIdx = Math.min(areaHighlightIdx + 1, items.length - 1);
            updateHighlight(items, areaHighlightIdx);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            areaHighlightIdx = Math.max(areaHighlightIdx - 1, 0);
            updateHighlight(items, areaHighlightIdx);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (areaHighlightIdx >= 0 && items[areaHighlightIdx]) {
                selectArea(items[areaHighlightIdx].dataset.value);
            }
        } else if (e.key === 'Escape') {
            closeAreaDropdown();
        }
    });

    areaList.addEventListener('click', (e) => {
        const li = e.target.closest('li');
        if (li) selectArea(li.dataset.value);
    });

    function selectArea(val) {
        selectedArea = val;
        areaInput.value = val;
        closeAreaDropdown();
    }

    function closeAreaDropdown() {
        areaDropdown.classList.remove('open');
    }

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!areaDropdown.contains(e.target)) closeAreaDropdown();
        if (!cuisineMulti.contains(e.target)) closeCuisineDropdown();
    });

    // ══════════════════════════════════════════════════════════
    // 3. Multi-Select Cuisine with Chips
    // ══════════════════════════════════════════════════════════
    function renderCuisineList(filter = '') {
        const f = filter.toLowerCase();
        const items = f ? allCuisines.filter(c => c.toLowerCase().includes(f)) : allCuisines;
        cuisineList.innerHTML = items.map(c =>
            `<li role="option" data-value="${escapeAttr(c)}" class="${selectedCuisines.includes(c) ? 'selected' : ''}">${escapeHtml(c)}</li>`
        ).join('');
        cuisineHighlightIdx = -1;
    }

    function renderChips() {
        // Remove old chips (keep the input)
        const oldChips = cuisineChips.querySelectorAll('.chip');
        oldChips.forEach(c => c.remove());

        // Add new chips before the input
        selectedCuisines.forEach(c => {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.innerHTML = `${escapeHtml(c)}<button type="button" class="chip__remove" data-value="${escapeAttr(c)}" aria-label="Remove ${escapeAttr(c)}">&times;</button>`;
            cuisineChips.insertBefore(chip, cuisineInput);
        });

        cuisineInput.placeholder = selectedCuisines.length ? '' : 'Search cuisines…';
    }

    cuisineChips.addEventListener('click', (e) => {
        const removeBtn = e.target.closest('.chip__remove');
        if (removeBtn) {
            const val = removeBtn.dataset.value;
            selectedCuisines = selectedCuisines.filter(c => c !== val);
            renderChips();
            renderCuisineList(cuisineInput.value);
            return;
        }
        // Focus input if clicking the chips area
        cuisineInput.focus();
    });

    cuisineInput.addEventListener('focus', () => {
        cuisineMulti.classList.add('open');
        renderCuisineList(cuisineInput.value);
    });

    cuisineInput.addEventListener('input', () => {
        cuisineMulti.classList.add('open');
        renderCuisineList(cuisineInput.value);
    });

    cuisineInput.addEventListener('keydown', (e) => {
        const items = cuisineList.querySelectorAll('li');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            cuisineHighlightIdx = Math.min(cuisineHighlightIdx + 1, items.length - 1);
            updateHighlight(items, cuisineHighlightIdx);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            cuisineHighlightIdx = Math.max(cuisineHighlightIdx - 1, 0);
            updateHighlight(items, cuisineHighlightIdx);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (cuisineHighlightIdx >= 0 && items[cuisineHighlightIdx]) {
                toggleCuisine(items[cuisineHighlightIdx].dataset.value);
            }
        } else if (e.key === 'Backspace' && !cuisineInput.value && selectedCuisines.length) {
            selectedCuisines.pop();
            renderChips();
            renderCuisineList();
        } else if (e.key === 'Escape') {
            closeCuisineDropdown();
        }
    });

    cuisineList.addEventListener('click', (e) => {
        const li = e.target.closest('li');
        if (li) toggleCuisine(li.dataset.value);
    });

    function toggleCuisine(val) {
        if (selectedCuisines.includes(val)) {
            selectedCuisines = selectedCuisines.filter(c => c !== val);
        } else {
            selectedCuisines.push(val);
        }
        cuisineInput.value = '';
        renderChips();
        renderCuisineList('');
        cuisineInput.focus();
    }

    function closeCuisineDropdown() {
        cuisineMulti.classList.remove('open');
    }

    // ── Shared highlight helper ─────────────────────────────
    function updateHighlight(items, idx) {
        items.forEach((li, i) => {
            li.classList.toggle('highlighted', i === idx);
            if (i === idx) li.scrollIntoView({ block: 'nearest' });
        });
    }

    // ══════════════════════════════════════════════════════════
    // 4. Dual Range Slider (Price)
    // ══════════════════════════════════════════════════════════
    function updateSlider() {
        let minVal = parseInt(priceMinInput.value);
        let maxVal = parseInt(priceMaxInput.value);

        // Prevent crossing
        if (minVal > maxVal) {
            const tmp = minVal;
            priceMinInput.value = maxVal;
            priceMaxInput.value = tmp;
            minVal = parseInt(priceMinInput.value);
            maxVal = parseInt(priceMaxInput.value);
        }

        priceLabelMin.textContent = `₹${minVal}`;
        priceLabelMax.textContent = maxVal >= 5000 ? '₹5000+' : `₹${maxVal}`;

        // Update fill bar
        const min = parseInt(priceMinInput.min);
        const max = parseInt(priceMinInput.max);
        const leftPct = ((minVal - min) / (max - min)) * 100;
        const rightPct = ((maxVal - min) / (max - min)) * 100;
        rangeFill.style.left = leftPct + '%';
        rangeFill.style.width = (rightPct - leftPct) + '%';
    }

    priceMinInput.addEventListener('input', updateSlider);
    priceMaxInput.addEventListener('input', updateSlider);
    updateSlider(); // initial render

    // ── Rating stepper ──────────────────────────────────────
    ratingMinus.addEventListener('click', () => {
        const val = parseFloat(ratingInput.value) || 0;
        ratingInput.value = Math.max(0, val - 0.5);
    });

    ratingPlus.addEventListener('click', () => {
        const val = parseFloat(ratingInput.value) || 0;
        ratingInput.value = Math.min(5, val + 0.5);
    });

    // ── Error close ─────────────────────────────────────────
    errorClose.addEventListener('click', () => { errorBanner.hidden = true; });

    // ══════════════════════════════════════════════════════════
    // 5. Form Submit
    // ══════════════════════════════════════════════════════════
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();
        showLoading();

        const payload = buildPayload();

        try {
            const response = await fetch(`${API_URL}/recommend`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (!response.ok) {
                const msg = data.details ? data.details.join('; ') : data.error || 'Something went wrong';
                showError(msg);
                hideLoading();
                return;
            }

            renderResults(data);
        } catch {
            showError('Could not reach the API server. Is the backend running on port 5000?');
        } finally {
            hideLoading();
        }
    });

    // ── Build payload ───────────────────────────────────────
    function buildPayload() {
        const payload = {};

        // Area → maps to "location" in the API
        if (selectedArea) payload.location = selectedArea;

        // Cuisines → send first selected (API supports single cuisine filter)
        // If multiple selected, we send the first one for API filtering
        // and the full list is informational
        if (selectedCuisines.length === 1) {
            payload.cuisine = selectedCuisines[0];
        } else if (selectedCuisines.length > 1) {
            // Send first cuisine as filter; backend filters by substring match
            payload.cuisine = selectedCuisines[0];
        }

        // Price range
        const minP = parseInt(priceMinInput.value);
        const maxP = parseInt(priceMaxInput.value);
        if (minP > 100) payload.price_min = minP;
        if (maxP < 5000) payload.price_max = maxP;

        // Rating
        const minRating = document.getElementById('min-rating').value.trim();
        if (minRating !== '') payload.min_rating = parseFloat(minRating);

        // Max results (clamped to 1–10)
        const maxResults = document.getElementById('max-results').value.trim();
        if (maxResults !== '') {
            payload.max_results = Math.max(1, Math.min(10, parseInt(maxResults, 10)));
        }

        return payload;
    }

    // ── Show / hide loading ─────────────────────────────────
    function showLoading() {
        submitBtn.disabled = true;
        btnText.hidden = true;
        btnLoading.hidden = false;
        resultsSection.hidden = false;
        skeletonGrid.hidden = false;
        resultsGrid.innerHTML = '';
        emptyState.hidden = true;
    }

    function hideLoading() {
        submitBtn.disabled = false;
        btnText.hidden = false;
        btnLoading.hidden = true;
        skeletonGrid.hidden = true;
    }

    // ── Error display ───────────────────────────────────────
    function showError(msg) { errorText.textContent = msg; errorBanner.hidden = false; }
    function hideError() { errorBanner.hidden = true; }

    // ── Render results ──────────────────────────────────────
    function renderResults(data) {
        const recs = data.recommendations || [];

        // Update footer with model name
        if (data.model_used) {
            footerModel.textContent = data.model_used;
        }

        if (recs.length === 0) {
            resultsGrid.innerHTML = '';
            emptyState.hidden = false;
            return;
        }

        emptyState.hidden = true;
        resultsGrid.innerHTML = recs.map(rec => createCard(rec)).join('');
    }

    function createCard(rec) {
        const attrs = rec.attributes || {};
        const tags = [];
        if (attrs.cuisines) tags.push(makeTag('🍴', attrs.cuisines));
        if (attrs.rating != null) tags.push(makeTag(parseFloat(attrs.rating) >= 4.0 ? '⭐' : '☆', `${attrs.rating}/5`));
        if (attrs.approx_cost) tags.push(makeTag('💰', `₹${attrs.approx_cost} for two`));
        if (attrs.location) tags.push(makeTag('📍', attrs.location));

        return `
            <div class="rec-card">
                <div class="rec-card__rank">#${rec.rank}</div>
                <div class="rec-card__body">
                    <div class="rec-card__name">${escapeHtml(rec.restaurant_name)}</div>
                    <div class="rec-card__explanation">${escapeHtml(rec.explanation || 'Matches your preferences.')}</div>
                    <div class="rec-card__tags">${tags.join('')}</div>
                </div>
            </div>
        `;
    }

    function makeTag(icon, text) {
        return `<span class="tag"><span class="tag__icon">${icon}</span> ${escapeHtml(text)}</span>`;
    }

    // ── Utilities ───────────────────────────────────────────
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function escapeAttr(str) {
        return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

})();
