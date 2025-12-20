/**
 * SpeakAlike Renderer - Frontend Logic
 */

// API_URL kommt vom preload.js als window.API_URL

// State
let currentAudioUrl = null;
let currentText = null;
let voiceModels = [];
let catalogTags = [];
let selectedFiles = [];
let currentTTSModel = 'xtts_v2';
let availableTTSModels = {};

// DOM Elements
const elements = {
    // Status
    status: document.getElementById('status'),
    statusText: document.querySelector('.status-text'),
    
    // TTS Model
    ttsModelSelect: document.getElementById('ttsModelSelect'),
    
    // Voice
    voiceSelect: document.getElementById('voiceSelect'),
    currentVoice: document.getElementById('currentVoice'),
    newVoiceBtn: document.getElementById('newVoiceBtn'),
    deleteVoiceBtn: document.getElementById('deleteVoiceBtn'),
    
    // Text
    textInput: document.getElementById('textInput'),
    languageSelect: document.getElementById('languageSelect'),
    charCount: document.getElementById('charCount'),
    speakBtn: document.getElementById('speakBtn'),
    stopBtn: document.getElementById('stopBtn'),
    
    // Audio
    audioPlayer: document.getElementById('audioPlayer'),
    
    // Catalog Preview
    catalogPreview: document.getElementById('catalogPreview'),
    openCatalogBtn: document.getElementById('openCatalogBtn'),
    
    // Settings Modal
    settingsBtn: document.getElementById('settingsBtn'),
    settingsModal: document.getElementById('settingsModal'),
    closeSettingsBtn: document.getElementById('closeSettingsBtn'),
    speedSlider: document.getElementById('speedSlider'),
    speedValue: document.getElementById('speedValue'),
    temperatureSlider: document.getElementById('temperatureSlider'),
    temperatureValue: document.getElementById('temperatureValue'),
    repetitionSlider: document.getElementById('repetitionSlider'),
    repetitionValue: document.getElementById('repetitionValue'),
    saveSettingsBtn: document.getElementById('saveSettingsBtn'),
    
    // New Voice Modal
    newVoiceModal: document.getElementById('newVoiceModal'),
    closeNewVoiceBtn: document.getElementById('closeNewVoiceBtn'),
    voiceName: document.getElementById('voiceName'),
    fileDropZone: document.getElementById('fileDropZone'),
    fileList: document.getElementById('fileList'),
    createVoiceBtn: document.getElementById('createVoiceBtn'),
    cancelNewVoiceBtn: document.getElementById('cancelNewVoiceBtn'),
    
    // Catalog Modal
    catalogModal: document.getElementById('catalogModal'),
    closeCatalogBtn: document.getElementById('closeCatalogBtn'),
    catalogSearch: document.getElementById('catalogSearch'),
    catalogSelectedTags: document.getElementById('catalogSelectedTags'),
    catalogTagDropdown: document.getElementById('catalogTagDropdown'),
    catalogTagSearch: document.getElementById('catalogTagSearch'),
    catalogTagList: document.getElementById('catalogTagList'),
    tagModeAnd: document.getElementById('tagModeAnd'),
    tagModeOr: document.getElementById('tagModeOr'),
    favoritesOnly: document.getElementById('favoritesOnly'),
    catalogGrid: document.getElementById('catalogGrid'),
    
    // Main Tag Filter
    mainTagFilterContainer: document.getElementById('mainTagFilterContainer'),
    mainSelectedTags: document.getElementById('mainSelectedTags'),
    mainTagDropdown: document.getElementById('mainTagDropdown'),
    mainTagSearch: document.getElementById('mainTagSearch'),
    mainTagList: document.getElementById('mainTagList'),
    mainTagModeAnd: document.getElementById('mainTagModeAnd'),
    mainTagModeOr: document.getElementById('mainTagModeOr'),
    
    // Save to Catalog Modal
    saveCatalogModal: document.getElementById('saveCatalogModal'),
    closeSaveCatalogBtn: document.getElementById('closeSaveCatalogBtn'),
    saveTextPreview: document.getElementById('saveTextPreview'),
    autoTagsBtn: document.getElementById('autoTagsBtn'),
    existingTags: document.getElementById('existingTags'),
    cancelSaveCatalogBtn: document.getElementById('cancelSaveCatalogBtn'),
    confirmSaveCatalogBtn: document.getElementById('confirmSaveCatalogBtn'),
    tagListContainer: document.getElementById('tagListContainer'),
    tagInputField: document.getElementById('tagInputField'),
    addTagBtn: document.getElementById('addTagBtn'),
    existingTagsList: document.getElementById('existingTagsList'),
    
    // Edit Tags Modal
    editTagsModal: document.getElementById('editTagsModal'),
    closeEditTagsBtn: document.getElementById('closeEditTagsBtn'),
    editTextPreview: document.getElementById('editTextPreview'),
    editTagListContainer: document.getElementById('editTagListContainer'),
    editTagInputField: document.getElementById('editTagInputField'),
    addEditTagBtn: document.getElementById('addEditTagBtn'),
    editExistingTagsList: document.getElementById('editExistingTagsList'),
    cancelEditTagsBtn: document.getElementById('cancelEditTagsBtn'),
    confirmEditTagsBtn: document.getElementById('confirmEditTagsBtn'),
    
    // Import MP3 Modal
    importMp3Btn: document.getElementById('importMp3Btn'),
    importMp3Modal: document.getElementById('importMp3Modal'),
    closeImportMp3Btn: document.getElementById('closeImportMp3Btn'),
    importDropZone: document.getElementById('importDropZone'),
    importFileName: document.getElementById('importFileName'),
    importText: document.getElementById('importText'),
    importTagListContainer: document.getElementById('importTagListContainer'),
    importTagInputField: document.getElementById('importTagInputField'),
    addImportTagBtn: document.getElementById('addImportTagBtn'),
    cancelImportMp3Btn: document.getElementById('cancelImportMp3Btn'),
    confirmImportMp3Btn: document.getElementById('confirmImportMp3Btn'),
    importExistingTagsList: document.getElementById('importExistingTagsList'),
    playImportAudioBtn: document.getElementById('playImportAudioBtn'),
    transcribeImportBtn: document.getElementById('transcribeImportBtn'),
    importAudioPlayer: document.getElementById('importAudioPlayer'),
    importAutoTagsBtn: document.getElementById('importAutoTagsBtn'),
    
    // History
    historyList: document.getElementById('historyList'),
    
    // Favorites
    favoritesList: document.getElementById('favoritesList')
};

// === Tag Filter State ===
let catalogSelectedTagsList = [];
let catalogTagMode = 'and';
let mainSelectedTagsList = [];
let mainTagMode = 'and';

// === API Functions ===

async function api(endpoint, options = {}) {
    try {
        const response = await fetch(`${window.API_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || 'API Error');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// === Playback History ===

async function addToPlaybackHistory(text, audioUrl, catalogId) {
    try {
        const params = new URLSearchParams({ text, audio_url: audioUrl });
        if (catalogId) params.append('catalog_id', catalogId);
        await api(`/api/history/add?${params}`, { method: 'POST' });
    } catch (error) {
        console.error('Failed to add to playback history:', error);
    }
}

// === Tag List Management ===

let currentTags = [];
let editCurrentTags = [];

function renderTagList(tags, container, mode = 'save') {
    // mode: 'save', 'edit', or 'import'
    container.innerHTML = '';
    tags.forEach((tag, index) => {
        const tagEl = document.createElement('span');
        tagEl.className = 'tag';
        tagEl.innerHTML = `
            ${escapeHtml(tag)}
            <button class="remove-tag" data-index="${index}">×</button>
        `;
        tagEl.querySelector('.remove-tag').onclick = () => {
            if (mode === 'edit') {
                editCurrentTags.splice(index, 1);
                renderTagList(editCurrentTags, container, 'edit');
            } else if (mode === 'import') {
                importCurrentTags.splice(index, 1);
                renderTagList(importCurrentTags, container, 'import');
            } else {
                currentTags.splice(index, 1);
                renderTagList(currentTags, container, 'save');
            }
        };
        container.appendChild(tagEl);
    });
}

function addTagFromInput(inputField, container, mode = 'save') {
    const tag = inputField.value.trim().toLowerCase();
    if (tag) {
        const tagList = mode === 'edit' ? editCurrentTags : (mode === 'import' ? importCurrentTags : currentTags);
        if (!tagList.includes(tag)) {
            tagList.push(tag);
            renderTagList(tagList, container, mode);
        }
        inputField.value = '';
    }
}

function addExistingTag(tag, mode = 'save') {
    const tagList = mode === 'edit' ? editCurrentTags : (mode === 'import' ? importCurrentTags : currentTags);
    const container = mode === 'edit' ? elements.editTagListContainer : (mode === 'import' ? elements.importTagListContainer : elements.tagListContainer);
    if (!tagList.includes(tag)) {
        tagList.push(tag);
        renderTagList(tagList, container, mode);
    }
    // Clear filter input after adding tag
    const inputField = mode === 'edit' ? elements.editTagInputField : (mode === 'import' ? elements.importTagInputField : elements.tagInputField);
    inputField.value = '';
    filterExistingTags('', mode);
}

function filterExistingTags(filter, mode = 'save') {
    const container = mode === 'edit' ? elements.editExistingTagsList : (mode === 'import' ? elements.importExistingTagsList : elements.existingTagsList);
    const currentTagList = mode === 'edit' ? editCurrentTags : (mode === 'import' ? importCurrentTags : currentTags);
    const filterLower = filter.toLowerCase();
    
    container.innerHTML = '';
    catalogTags
        .filter(tag => tag.name.toLowerCase().includes(filterLower))
        .forEach(tag => {
            const tagBtn = document.createElement('button');
            tagBtn.className = 'tag clickable';
            // Highlight already added tags
            if (currentTagList.includes(tag.name)) {
                tagBtn.classList.add('disabled');
            }
            tagBtn.textContent = tag.name;
            tagBtn.onclick = () => {
                if (!currentTagList.includes(tag.name)) {
                    addExistingTag(tag.name, mode);
                }
            };
            container.appendChild(tagBtn);
        });
}

// === Status ===

async function checkStatus() {
    try {
        const status = await api('/api/status');
        elements.status.classList.add('connected');
        elements.status.classList.remove('error');
        elements.statusText.textContent = status.message;
        
        // Speak-Button deaktivieren während TTS lädt
        if (status.loading) {
            elements.speakBtn.disabled = true;
            elements.speakBtn.textContent = '⏳ TTS lädt...';
            elements.status.classList.add('loading');
        } else {
            elements.speakBtn.disabled = false;
            elements.speakBtn.textContent = '🔊 Sprechen';
            elements.status.classList.remove('loading');
        }
        
        if (status.voice_loaded) {
            elements.currentVoice.querySelector('.voice-name').textContent = status.voice_loaded;
        }
        
        return status;
    } catch (error) {
        elements.status.classList.remove('connected');
        elements.status.classList.add('error');
        elements.statusText.textContent = 'Nicht verbunden';
        return null;
    }
}

// === Voice Models ===

async function loadVoiceModels() {
    try {
        voiceModels = await api('/api/voice-models');
        
        elements.voiceSelect.innerHTML = '<option value="">Standard (XTTS)</option>';
        
        let hasActiveVoice = false;
        voiceModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = `${model.name} (${model.sample_count} Samples)`;
            if (model.is_active) {
                option.selected = true;
                elements.currentVoice.querySelector('.voice-name').textContent = model.name;
                hasActiveVoice = true;
            }
            elements.voiceSelect.appendChild(option);
        });
        
        // Falls keine aktive Stimme, aber Stimmen vorhanden sind, wähle die erste
        if (!hasActiveVoice && voiceModels.length > 0) {
            const firstVoice = voiceModels[0].name;
            elements.voiceSelect.value = firstVoice;
            await loadVoiceModel(firstVoice);
        }
    } catch (error) {
        console.error('Failed to load voice models:', error);
    }
}

async function loadVoiceModel(name) {
    if (!name) {
        elements.currentVoice.querySelector('.voice-name').textContent = 'Standard';
        return;
    }
    
    try {
        elements.statusText.textContent = `Lade ${name}...`;
        await api(`/api/voice-models/${name}/load`, { method: 'POST' });
        elements.currentVoice.querySelector('.voice-name').textContent = name;
        await checkStatus();
    } catch (error) {
        alert(`Fehler beim Laden: ${error.message}`);
    }
}

async function deleteVoiceModel() {
    const selectedVoice = elements.voiceSelect.value;
    
    if (!selectedVoice) {
        alert('Bitte wähle zuerst eine Stimme aus, die gelöscht werden soll.');
        return;
    }
    
    const confirmed = confirm(`Möchtest du die Stimme "${selectedVoice}" wirklich löschen?\n\nDiese Aktion kann nicht rückgängig gemacht werden.`);
    
    if (!confirmed) {
        return;
    }
    
    try {
        elements.statusText.textContent = `Lösche ${selectedVoice}...`;
        await api(`/api/voice-models/${selectedVoice}`, { method: 'DELETE' });
        elements.statusText.textContent = `Stimme "${selectedVoice}" gelöscht`;
        elements.voiceSelect.value = '';
        elements.currentVoice.querySelector('.voice-name').textContent = 'Standard';
        await loadVoiceModels();
    } catch (error) {
        alert(`Fehler beim Löschen: ${error.message}`);
    }
}

// === Text-to-Speech ===

async function speak() {
    const text = elements.textInput.value.trim();
    if (!text) {
        showToast('Bitte geben Sie einen Text ein.', 'error');
        return;
    }
    
    currentText = text;
    elements.speakBtn.disabled = true;
    elements.stopBtn.disabled = false;
    elements.statusText.textContent = 'Generiere Audio...';
    
    try {
        const result = await api('/api/tts/speak', {
            method: 'POST',
            body: JSON.stringify({
                text: text,
                language: elements.languageSelect.value
            })
        });
        
        if (result.success) {
            currentAudioUrl = `${window.API_URL}${result.audio_url}`;
            console.log('Audio URL:', currentAudioUrl);
            elements.audioPlayer.src = currentAudioUrl;
            
            // Event-Listener für Debugging
            elements.audioPlayer.onerror = (e) => {
                console.error('Audio Fehler:', e, elements.audioPlayer.error);
                showToast('Audio-Fehler beim Abspielen', 'error');
            };
            
            elements.audioPlayer.oncanplay = () => {
                console.log('Audio kann abgespielt werden');
            };
            
            try {
                await elements.audioPlayer.play();
                console.log('Audio wird abgespielt');
            } catch (playError) {
                console.error('Play Fehler:', playError);
                showToast('Konnte Audio nicht abspielen', 'error');
            }
            
            // Zum Wiedergabe-Verlauf hinzufügen
            await addToPlaybackHistory(text, result.audio_url, null);
            
            // History aktualisieren
            loadHistory();
        }
    } catch (error) {
        showToast(`Fehler: ${error.message}`, 'error');
    } finally {
        elements.speakBtn.disabled = false;
        elements.stopBtn.disabled = true;
        checkStatus();
    }
}

async function stopSpeaking() {
    try {
        await api('/api/tts/stop', { method: 'POST' });
        elements.audioPlayer.pause();
    } catch (error) {
        console.error('Stop error:', error);
    }
    
    elements.speakBtn.disabled = false;
    elements.stopBtn.disabled = true;
    checkStatus();
}

// === Catalog ===

async function loadCatalogTags() {
    try {
        catalogTags = await api('/api/catalog/tags');
        
        // Render tag filter lists
        renderTagFilterList(elements.catalogTagList, 'catalog');
        renderTagFilterList(elements.mainTagList, 'main');
        
        // Update existing tags in save dialog
        elements.existingTags.innerHTML = '';
        catalogTags.slice(0, 15).forEach(tag => {
            const tagEl = document.createElement('span');
            tagEl.className = 'tag';
            tagEl.textContent = tag.name;
            tagEl.onclick = () => addTagToInput(tag.name);
            elements.existingTags.appendChild(tagEl);
        });
    } catch (error) {
        console.error('Failed to load tags:', error);
    }
}

function renderTagFilterList(container, context, filter = '') {
    if (!container) return;
    
    const selectedList = context === 'catalog' ? catalogSelectedTagsList : mainSelectedTagsList;
    const filterLower = filter.toLowerCase();
    
    container.innerHTML = '';
    catalogTags
        .filter(tag => tag.name.toLowerCase().includes(filterLower))
        .forEach(tag => {
            const isSelected = selectedList.includes(tag.name);
            const tagEl = document.createElement('div');
            tagEl.className = `tag-filter-item ${isSelected ? 'selected' : ''}`;
            tagEl.innerHTML = `
                <span class="tag-name">${tag.name}</span>
                <span class="tag-count">${tag.count}</span>
                ${isSelected ? '<span class="tag-check">✓</span>' : ''}
            `;
            tagEl.onclick = () => toggleTagFilter(tag.name, context);
            container.appendChild(tagEl);
        });
}

function toggleTagFilter(tagName, context) {
    const selectedList = context === 'catalog' ? catalogSelectedTagsList : mainSelectedTagsList;
    const index = selectedList.indexOf(tagName);
    
    if (index > -1) {
        selectedList.splice(index, 1);
    } else {
        selectedList.push(tagName);
    }
    
    // Update lists
    if (context === 'catalog') {
        catalogSelectedTagsList = selectedList;
        renderSelectedTags(elements.catalogSelectedTags, catalogSelectedTagsList, 'catalog');
        renderTagFilterList(elements.catalogTagList, 'catalog', elements.catalogTagSearch.value);
        loadCatalog();
    } else {
        mainSelectedTagsList = selectedList;
        renderSelectedTags(elements.mainSelectedTags, mainSelectedTagsList, 'main');
        renderTagFilterList(elements.mainTagList, 'main', elements.mainTagSearch.value);
        loadCatalogPreview();
    }
}

function renderSelectedTags(container, tags, context) {
    if (!container) return;
    
    if (tags.length === 0) {
        container.innerHTML = '<span class="tag-filter-placeholder">Tags filtern...</span>';
        return;
    }
    
    container.innerHTML = tags.map(tag => `
        <span class="tag selected-tag">
            ${tag}
            <span class="tag-remove" onclick="event.stopPropagation(); removeTagFilter('${tag}', '${context}')">×</span>
        </span>
    `).join('');
}

function removeTagFilter(tagName, context) {
    toggleTagFilter(tagName, context);
}

function setTagMode(mode, context) {
    if (context === 'catalog') {
        catalogTagMode = mode;
        elements.tagModeAnd.classList.toggle('active', mode === 'and');
        elements.tagModeOr.classList.toggle('active', mode === 'or');
        loadCatalog();
    } else {
        mainTagMode = mode;
        elements.mainTagModeAnd.classList.toggle('active', mode === 'and');
        elements.mainTagModeOr.classList.toggle('active', mode === 'or');
        loadCatalogPreview();
    }
}

function toggleTagDropdown(dropdown, show) {
    if (show) {
        dropdown.classList.add('active');
    } else {
        dropdown.classList.remove('active');
    }
}

async function loadCatalog() {
    try {
        const params = new URLSearchParams();
        if (elements.catalogSearch.value) params.set('search', elements.catalogSearch.value);
        if (catalogSelectedTagsList.length > 0) {
            params.set('tags', catalogSelectedTagsList.join(','));
            params.set('tag_mode', catalogTagMode);
        }
        if (elements.favoritesOnly.checked) params.set('favorites_only', 'true');
        
        const messages = await api(`/api/catalog?${params}`);
        
        elements.catalogGrid.innerHTML = '';
        
        if (messages.length === 0) {
            elements.catalogGrid.innerHTML = '<p class="muted" style="padding: 20px;">Keine Einträge gefunden</p>';
            return;
        }
        
        messages.forEach(msg => {
            const item = createCatalogItem(msg);
            elements.catalogGrid.appendChild(item);
        });
    } catch (error) {
        console.error('Failed to load catalog:', error);
    }
}

// Sprach-Tag Mapping (global verfügbar)
const langNames = {
    'de': 'deutsch', 'en': 'englisch', 'es': 'spanisch', 'fr': 'französisch',
    'it': 'italienisch', 'pt': 'portugiesisch', 'pl': 'polnisch', 'tr': 'türkisch',
    'ru': 'russisch', 'nl': 'niederländisch', 'ja': 'japanisch', 'zh-cn': 'chinesisch'
};

// Alle Sprach-Tags als Set für schnelle Prüfung
const allLangTags = new Set(Object.values(langNames));

// Prüft ob ein Eintrag zur aktuellen Sprache passt (oder kein Sprach-Tag hat)
function matchesLanguageFilter(item, currentLangTag) {
    const itemTags = item.tags || [];
    const hasAnyLangTag = itemTags.some(tag => allLangTags.has(tag));
    
    // Zeige an wenn: kein Sprach-Tag vorhanden ODER das aktuelle Sprach-Tag vorhanden
    return !hasAnyLangTag || itemTags.includes(currentLangTag);
}

async function loadCatalogPreview() {
    try {
        // Lade Einträge für die Vorschau
        const params = new URLSearchParams();
        params.set('order_by', 'play_count');
        params.set('limit', '100');  // Mehr laden, da wir im Frontend filtern
        
        // Nur die manuell ausgewählten Tags an Backend senden
        if (mainSelectedTagsList.length > 0) {
            params.set('tags', mainSelectedTagsList.join(','));
            params.set('tag_mode', mainTagMode);
        }
        
        let messages = await api(`/api/catalog?${params}`);
        
        // Im Frontend nach Sprache filtern
        const currentLang = elements.languageSelect.value;
        const langTag = langNames[currentLang] || currentLang;
        
        console.log(`\n=== Katalog-Vorschau Filter ===`);
        console.log(`Aktuelle Sprache: ${currentLang} → Tag: "${langTag}"`);
        console.log(`Einträge vom Backend: ${messages.length}`);
        
        const beforeFilter = messages.length;
        messages = messages.filter(msg => {
            const itemTags = msg.tags || [];
            const hasAnyLangTag = itemTags.some(tag => allLangTags.has(tag));
            const matches = matchesLanguageFilter(msg, langTag);
            
            if (!matches) {
                console.log(`  ✗ Gefiltert: "${msg.text.substring(0, 30)}..." | Tags: [${itemTags.join(', ')}]`);
            }
            return matches;
        });
        
        console.log(`Nach Sprachfilter: ${messages.length} (${beforeFilter - messages.length} entfernt)`);
        
        // Auf 50 begrenzen nach Filterung
        if (messages.length > 50) {
            console.log(`Abgeschnitten bei 50 (${messages.length - 50} weitere nicht angezeigt)`);
        }
        messages = messages.slice(0, 50);
        
        console.log(`Angezeigte Einträge: ${messages.length}`);
        messages.slice(0, 5).forEach(msg => {
            const tags = msg.tags || [];
            console.log(`  ✓ "${msg.text.substring(0, 30)}..." | Tags: [${tags.join(', ')}]`);
        });
        if (messages.length > 5) console.log(`  ... und ${messages.length - 5} weitere`);
        
        if (messages.length === 0) {
            elements.catalogPreview.innerHTML = '<p class="muted">Noch keine Einträge im Katalog</p>';
            return;
        }
        
        elements.catalogPreview.innerHTML = '';
        messages.forEach(msg => {
            const item = document.createElement('div');
            item.className = 'catalog-preview-item';
            item.innerHTML = `
                <span class="preview-text">${escapeHtml(msg.text.substring(0, 40))}${msg.text.length > 40 ? '...' : ''}</span>
                <button class="btn btn-small play-btn" data-id="${msg.id}">▶️</button>
            `;
            item.querySelector('.play-btn').onclick = () => playCatalogAudio(msg.id, msg.text);
            elements.catalogPreview.appendChild(item);
        });
    } catch (error) {
        console.error('Failed to load catalog preview:', error);
    }
}

async function loadHistory() {
    try {
        const history = await api('/api/history');
        
        if (!history || history.length === 0) {
            elements.historyList.innerHTML = '<p class="muted">Noch keine Nachrichten</p>';
            return;
        }
        
        elements.historyList.innerHTML = '';
        history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            
            // Zeit formatieren (nur Uhrzeit)
            const time = new Date(item.timestamp);
            const timeStr = time.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
            
            // Katalog-Status-Indikator (✓ wenn im Katalog)
            const catalogIndicator = item.in_catalog ? '✓ ' : '';
            
            div.innerHTML = `
                <span class="history-text">${catalogIndicator}${escapeHtml(item.text.substring(0, 40))}${item.text.length > 40 ? '...' : ''}</span>
                <span class="history-time">${timeStr}</span>
                <div class="history-actions">
                    <button class="btn btn-small play-btn" title="Abspielen">▶️</button>
                    <button class="btn btn-small save-btn" title="Speichern">💾</button>
                    ${!item.in_catalog ? '<button class="btn btn-small catalog-btn" title="Zum Katalog">📁</button>' : ''}
                </div>
            `;
            div.querySelector('.play-btn').onclick = () => playHistoryAudio(item.audio_url, item.text, item.catalog_id);
            div.querySelector('.save-btn').onclick = () => saveHistoryAudio(item.audio_url, item.text);
            const catalogBtn = div.querySelector('.catalog-btn');
            if (catalogBtn) {
                catalogBtn.onclick = () => openSaveCatalogModalForHistory(item);
            }
            elements.historyList.appendChild(div);
        });
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

async function playHistoryAudio(audioUrl, text, catalogId) {
    elements.audioPlayer.src = `${window.API_URL}${audioUrl}`;
    elements.audioPlayer.play();
    
    // Zum Wiedergabe-Verlauf hinzufügen
    await addToPlaybackHistory(text, audioUrl, catalogId);
    loadHistory();
}

async function saveHistoryAudio(audioUrl, text) {
    try {
        // Audio herunterladen und speichern
        const response = await fetch(`${window.API_URL}${audioUrl}`);
        const blob = await response.blob();
        
        // Dateiname aus Text erstellen (erste 30 Zeichen)
        const safeName = text.substring(0, 30).replace(/[^a-zA-Z0-9äöüÄÖÜß\s]/g, '').trim().replace(/\s+/g, '_');
        const filename = `${safeName}.wav`;
        
        // Download-Link erstellen
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        alert(`Fehler beim Speichern: ${error.message}`);
    }
}

// === Favorites ===

async function loadFavorites() {
    try {
        const allFavorites = await api('/api/catalog?favorites_only=true&limit=50');
        
        if (!allFavorites || allFavorites.length === 0) {
            elements.favoritesList.innerHTML = '<p class="muted">Noch keine Favoriten</p>';
            return;
        }
        
        // Nach aktueller Sprache filtern (oder wenn kein Sprach-Tag vorhanden)
        const currentLang = elements.languageSelect.value;
        const langTag = langNames[currentLang] || currentLang;
        
        console.log(`\n=== Favoriten Filter ===`);
        console.log(`Aktuelle Sprache: ${currentLang} → Tag: "${langTag}"`);
        console.log(`Favoriten vom Backend: ${allFavorites.length}`);
        
        const filtered = allFavorites.filter(item => {
            const itemTags = item.tags || [];
            const matches = matchesLanguageFilter(item, langTag);
            
            if (!matches) {
                console.log(`  ✗ Gefiltert: "${item.text.substring(0, 30)}..." | Tags: [${itemTags.join(', ')}]`);
            }
            return matches;
        });
        
        console.log(`Nach Sprachfilter: ${filtered.length} (${allFavorites.length - filtered.length} entfernt)`);
        
        const favorites = filtered.slice(0, 20);
        if (filtered.length > 20) {
            console.log(`Abgeschnitten bei 20 (${filtered.length - 20} weitere nicht angezeigt)`);
        }
        
        favorites.forEach(item => {
            const tags = item.tags || [];
            console.log(`  ✓ "${item.text.substring(0, 30)}..." | Tags: [${tags.join(', ')}]`);
        });
        
        if (favorites.length === 0) {
            elements.favoritesList.innerHTML = '<p class="muted">Keine Favoriten für diese Sprache</p>';
            return;
        }
        
        elements.favoritesList.innerHTML = '';
        favorites.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            
            div.innerHTML = `
                <span class="history-text">${escapeHtml(item.text.substring(0, 40))}${item.text.length > 40 ? '...' : ''}</span>
                <span class="history-time">${item.play_count || 0}×</span>
                <div class="history-actions">
                    <button class="btn btn-small play-btn" title="Abspielen">▶️</button>
                    <button class="btn btn-small unfav-btn" title="Entfernen">⭐</button>
                </div>
            `;
            div.querySelector('.play-btn').onclick = () => playCatalogItem(item);
            div.querySelector('.unfav-btn').onclick = () => toggleFavorite(item.id, false);
            elements.favoritesList.appendChild(div);
        });
    } catch (error) {
        console.error('Failed to load favorites:', error);
    }
}

async function playCatalogItem(item) {
    if (item.audio_url) {
        elements.audioPlayer.src = `${window.API_URL}${item.audio_url}`;
        elements.audioPlayer.play();
        
        // Play count erhöhen
        await api(`/api/catalog/${item.id}/play`, { method: 'POST' });
        loadFavorites();
        loadCatalogPreview();
    }
}

let currentHistoryItem = null;

function openSaveCatalogModalForHistory(item) {
    currentHistoryItem = item;
    currentText = item.text;
    currentAudioUrl = `${window.API_URL}${item.audio_url}`;
    
    elements.saveTextPreview.textContent = item.text;
    
    // Reset current tags
    currentTags = [];
    renderTagList(currentTags, elements.tagListContainer, 'save');
    
    // Existing tags anzeigen (mit Filter)
    loadCatalogTags();
    filterExistingTags('', 'save');
    
    elements.saveCatalogModal.classList.add('active');
}

function createCatalogItem(msg) {
    const div = document.createElement('div');
    div.className = 'catalog-item';
    div.innerHTML = `
        <div class="catalog-item-header">
            <button class="favorite-btn ${msg.is_favorite ? 'active' : ''}" data-id="${msg.id}">
                ${msg.is_favorite ? '⭐' : '☆'}
            </button>
            <div class="catalog-item-actions">
                <button class="btn btn-small play-btn" data-id="${msg.id}">▶️</button>
                <button class="btn btn-small edit-btn" data-id="${msg.id}">🏷️</button>
                <button class="btn btn-small delete-btn" data-id="${msg.id}">🗑️</button>
            </div>
        </div>
        <div class="catalog-item-text">${escapeHtml(msg.text)}</div>
        <div class="catalog-item-tags">
            ${msg.tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        </div>
        <div class="catalog-item-meta">
            <span>${formatDuration(msg.duration)}</span>
            <span>${formatDate(msg.created_at)}</span>
        </div>
    `;
    
    // Event handlers
    div.querySelector('.favorite-btn').onclick = () => toggleFavorite(msg.id);
    div.querySelector('.play-btn').onclick = () => playCatalogAudio(msg.id, msg.text);
    div.querySelector('.edit-btn').onclick = () => openEditTagsModal(msg);
    div.querySelector('.delete-btn').onclick = () => deleteCatalogMessage(msg.id);
    
    return div;
}

async function toggleFavorite(id, setTo = null) {
    try {
        if (setTo !== null) {
            // Direkt auf Wert setzen
            await api(`/api/catalog/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ is_favorite: setTo })
            });
        } else {
            // Toggle
            await api(`/api/catalog/${id}/favorite`, { method: 'PUT' });
        }
        loadCatalog();
        loadFavorites();
        loadCatalogPreview();
    } catch (error) {
        console.error('Toggle favorite error:', error);
    }
}

async function playCatalogAudio(id, text) {
    const audioUrl = `/api/catalog/${id}/audio`;
    elements.audioPlayer.src = `${window.API_URL}${audioUrl}`;
    elements.audioPlayer.play();
    
    // Zum Wiedergabe-Verlauf hinzufügen
    await addToPlaybackHistory(text, audioUrl, id);
    loadHistory();
}

async function deleteCatalogMessage(id) {
    if (!confirm('Nachricht wirklich löschen?')) return;
    
    try {
        await api(`/api/catalog/${id}`, { method: 'DELETE' });
        loadCatalog();
        loadFavorites();
    } catch (error) {
        alert(`Fehler: ${error.message}`);
    }
}

// === Edit Tags ===
let currentEditMessageId = null;

function openEditTagsModal(msg) {
    currentEditMessageId = msg.id;
    elements.editTextPreview.textContent = msg.text;
    
    // Set current tags from message
    editCurrentTags = [...msg.tags];
    renderTagList(editCurrentTags, elements.editTagListContainer, 'edit');
    
    // Show existing tags (mit Filter)
    filterExistingTags('', 'edit');
    
    elements.editTagsModal.classList.add('active');
}

function closeEditTagsModal() {
    elements.editTagsModal.classList.remove('active');
    currentEditMessageId = null;
    editCurrentTags = [];
}

async function saveEditedTags() {
    if (!currentEditMessageId) return;
    
    try {
        await api(`/api/catalog/${currentEditMessageId}/tags`, {
            method: 'PUT',
            body: JSON.stringify(editCurrentTags)
        });
        closeEditTagsModal();
        loadCatalog();
        loadCatalogTags();
    } catch (error) {
        alert(`Fehler beim Speichern: ${error.message}`);
    }
}

async function saveToCatalog() {
    const tags = [...currentTags];
    
    // Add language tag (nutzt globale langNames)
    const langTag = langNames[elements.languageSelect.value] || elements.languageSelect.value;
    if (!tags.includes(langTag)) {
        tags.unshift(langTag);
    }
    
    try {
        await api('/api/catalog/save', {
            method: 'POST',
            body: JSON.stringify({ tags })
        });
        
        closeSaveCatalogModal();
        
        // Toast statt alert, um Fokus-Probleme zu vermeiden
        showToast('Zum Katalog hinzugefügt!', 'success');
        
        loadCatalogTags();
        loadFavorites();
        loadCatalogPreview();
    } catch (error) {
        showToast(`Fehler: ${error.message}`, 'error');
    }
}

async function generateAutoTags() {
    if (!currentText) return;
    
    elements.autoTagsBtn.disabled = true;
    elements.autoTagsBtn.textContent = '⏳ Generiere...';
    
    try {
        const result = await api('/api/tags/generate', {
            method: 'POST',
            body: JSON.stringify({
                text: currentText,
                num_tags: 5
            })
        });
        
        if (result.tags && result.tags.length > 0) {
            // Add each generated tag to the list
            result.tags.forEach(tag => {
                if (!currentTags.includes(tag)) {
                    currentTags.push(tag);
                }
            });
            renderTagList(currentTags, elements.tagListContainer, 'save');
        }
    } catch (error) {
        console.error('Auto-tags error:', error);
    } finally {
        elements.autoTagsBtn.disabled = false;
        elements.autoTagsBtn.textContent = '🤖 Auto-Tags';
    }
}

// === Import MP3 ===

let importCurrentTags = [];
let importFile = null;

function openImportMp3Modal() {
    importCurrentTags = [];
    importFile = null;
    elements.importFileName.textContent = '';
    elements.importText.value = '';
    elements.playImportAudioBtn.disabled = true;
    elements.playImportAudioBtn.textContent = '▶️';
    elements.transcribeImportBtn.disabled = true;
    elements.importAudioPlayer.src = '';
    elements.importTagInputField.value = '';
    renderTagList(importCurrentTags, elements.importTagListContainer, 'import');
    
    // Load existing tags (mit Filter)
    loadCatalogTags();
    filterExistingTags('', 'import');
    
    elements.importMp3Modal.classList.add('active');
}

function closeImportMp3Modal() {
    elements.importMp3Modal.classList.remove('active');
    importCurrentTags = [];
    importFile = null;
    elements.importAudioPlayer.pause();
    elements.importAudioPlayer.src = '';
}

function setupImportDropZone() {
    const dropZone = elements.importDropZone;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
    });
    
    // Handle dropped files
    dropZone.addEventListener('drop', handleImportDrop, false);
    
    // Handle click to select file
    dropZone.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'audio/mp3,audio/wav,audio/ogg,audio/m4a,.mp3,.wav,.ogg,.m4a';
        input.onchange = (e) => {
            if (e.target.files.length > 0) {
                setImportFile(e.target.files[0]);
            }
        };
        input.click();
    });
}

function handleImportDrop(e) {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        setImportFile(files[0]);
    }
}

function setImportFile(file) {
    const validTypes = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/x-m4a'];
    const validExtensions = ['.mp3', '.wav', '.ogg', '.m4a'];
    
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!validTypes.includes(file.type) && !validExtensions.includes(ext)) {
        alert('Bitte wählen Sie eine Audio-Datei (MP3, WAV, OGG, M4A)');
        return;
    }
    
    importFile = file;
    elements.importFileName.textContent = `📄 ${file.name}`;
    
    // Enable playback and transcription buttons
    elements.playImportAudioBtn.disabled = false;
    elements.transcribeImportBtn.disabled = false;
    
    // Set up audio player
    const objectUrl = URL.createObjectURL(file);
    elements.importAudioPlayer.src = objectUrl;
}

function playImportAudio() {
    if (!importFile) return;
    
    const player = elements.importAudioPlayer;
    if (player.paused) {
        player.play();
        elements.playImportAudioBtn.textContent = '⏸️';
    } else {
        player.pause();
        elements.playImportAudioBtn.textContent = '▶️';
    }
}

async function transcribeImportAudio() {
    if (!importFile) return;
    
    elements.transcribeImportBtn.disabled = true;
    elements.transcribeImportBtn.textContent = '⏳ Erkenne...';
    
    try {
        const formData = new FormData();
        formData.append('audio', importFile);
        
        const response = await fetch(`${window.API_URL}/api/transcribe`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Transkription fehlgeschlagen');
        }
        
        const result = await response.json();
        if (result.text) {
            elements.importText.value = result.text;
        }
    } catch (error) {
        console.error('Transcription error:', error);
        alert('Fehler bei der Spracherkennung: ' + error.message);
    } finally {
        elements.transcribeImportBtn.disabled = false;
        elements.transcribeImportBtn.textContent = '🎤 Erkennen';
    }
}

async function generateImportAutoTags() {
    const text = elements.importText.value.trim();
    if (!text) {
        alert('Bitte geben Sie zuerst den Text ein oder nutzen Sie die Spracherkennung.');
        return;
    }
    
    elements.importAutoTagsBtn.disabled = true;
    elements.importAutoTagsBtn.textContent = '⏳';
    
    try {
        const response = await api('/api/tags/generate', {
            method: 'POST',
            body: JSON.stringify({ text: text, num_tags: 3 })
        });
        
        if (response.tags && response.tags.length > 0) {
            response.tags.forEach(tag => {
                if (!importCurrentTags.includes(tag)) {
                    importCurrentTags.push(tag);
                }
            });
            renderTagList(importCurrentTags, elements.importTagListContainer, 'import');
        }
    } catch (error) {
        console.error('Auto-tags error:', error);
    } finally {
        elements.importAutoTagsBtn.disabled = false;
        elements.importAutoTagsBtn.textContent = '🤖';
    }
}

function addImportTag(tag) {
    if (tag && !importCurrentTags.includes(tag)) {
        importCurrentTags.push(tag);
        renderTagList(importCurrentTags, elements.importTagListContainer, 'import');
    }
}

async function importMp3() {
    if (!importFile) {
        alert('Bitte wählen Sie eine Audio-Datei aus.');
        return;
    }
    
    const text = elements.importText.value.trim();
    if (!text) {
        alert('Bitte geben Sie den Text der Nachricht ein.');
        return;
    }
    
    elements.confirmImportMp3Btn.disabled = true;
    elements.confirmImportMp3Btn.textContent = '⏳ Importiere...';
    
    try {
        const formData = new FormData();
        formData.append('audio', importFile);
        formData.append('text', text);
        formData.append('tags', importCurrentTags.join(','));
        
        const response = await fetch(`${window.API_URL}/api/catalog/import`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Import fehlgeschlagen');
        }
        
        closeImportMp3Modal();
        loadCatalog();
        loadCatalogPreview();
        showToast('Audio erfolgreich importiert!', 'success');
        
    } catch (error) {
        showToast(`Fehler beim Import: ${error.message}`, 'error');
    } finally {
        elements.confirmImportMp3Btn.disabled = false;
        elements.confirmImportMp3Btn.textContent = '📥 Importieren';
    }
}

// === New Voice ===

async function createVoice() {
    const name = elements.voiceName.value.trim();
    if (!name) {
        alert('Bitte geben Sie einen Namen ein.');
        return;
    }
    
    if (selectedFiles.length === 0) {
        alert('Bitte wählen Sie mindestens eine Audio-Datei aus.');
        return;
    }
    
    elements.createVoiceBtn.disabled = true;
    elements.createVoiceBtn.textContent = 'Erstelle...';
    
    try {
        const formData = new FormData();
        formData.append('name', name);
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        const response = await fetch(`${window.API_URL}/api/voice-models/create`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Fehler beim Erstellen');
        }
        
        closeNewVoiceModal();
        showToast(`Stimme "${name}" erfolgreich erstellt!`, 'success');
        loadVoiceModels();
    } catch (error) {
        showToast(`Fehler: ${error.message}`, 'error');
    } finally {
        elements.createVoiceBtn.disabled = false;
        elements.createVoiceBtn.textContent = 'Stimme erstellen';
    }
}

function handleFileSelect(files) {
    selectedFiles = Array.from(files).filter(f => 
        f.type.startsWith('audio/') || 
        f.name.endsWith('.wav') || 
        f.name.endsWith('.mp3') || 
        f.name.endsWith('.ogg')
    );
    
    updateFileList();
    elements.createVoiceBtn.disabled = selectedFiles.length === 0;
}

function updateFileList() {
    elements.fileList.innerHTML = '';
    selectedFiles.forEach((file, index) => {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
            <span>🎵 ${file.name}</span>
            <button class="btn btn-small" data-index="${index}">✕</button>
        `;
        div.querySelector('button').onclick = () => {
            selectedFiles.splice(index, 1);
            updateFileList();
            elements.createVoiceBtn.disabled = selectedFiles.length === 0;
        };
        elements.fileList.appendChild(div);
    });
}

// === Settings ===

async function loadSettings() {
    try {
        const settings = await api('/api/settings');
        
        elements.speedSlider.value = settings.speed || 1.0;
        elements.speedValue.textContent = `${settings.speed || 1.0}x`;
        
        elements.temperatureSlider.value = settings.temperature || 0.3;
        elements.temperatureValue.textContent = settings.temperature || 0.3;
        
        elements.repetitionSlider.value = settings.repetition_penalty || 5.0;
        elements.repetitionValue.textContent = settings.repetition_penalty || 5.0;
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

async function saveSettings() {
    try {
        await api('/api/settings', {
            method: 'PUT',
            body: JSON.stringify({
                speed: parseFloat(elements.speedSlider.value),
                temperature: parseFloat(elements.temperatureSlider.value),
                repetition_penalty: parseFloat(elements.repetitionSlider.value)
            })
        });
        
        // Pitch-Korrektur speichern
        await api('/api/pitch', {
            method: 'POST',
            body: JSON.stringify({
                semitones: parseFloat(elements.pitchSlider.value)
            })
        });
        
        closeSettingsModal();
    } catch (error) {
        alert(`Fehler: ${error.message}`);
    }
}

// === Modal Functions ===

function openSettingsModal() {
    loadSettings();
    elements.settingsModal.classList.add('active');
}

function closeSettingsModal() {
    elements.settingsModal.classList.remove('active');
}

function openNewVoiceModal() {
    elements.voiceName.value = '';
    selectedFiles = [];
    updateFileList();
    elements.createVoiceBtn.disabled = true;
    elements.newVoiceModal.classList.add('active');
}

function closeNewVoiceModal() {
    elements.newVoiceModal.classList.remove('active');
}

function openCatalogModal() {
    loadCatalogTags();
    loadCatalog();
    elements.catalogModal.classList.add('active');
}

function closeCatalogModal() {
    elements.catalogModal.classList.remove('active');
}

function openSaveCatalogModal() {
    if (!currentText || !currentAudioUrl) {
        alert('Keine Audio zum Speichern vorhanden.');
        return;
    }
    
    elements.saveTextPreview.textContent = currentText;
    
    // Reset current tags
    currentTags = [];
    elements.tagInputField.value = '';
    renderTagList(currentTags, elements.tagListContainer, 'save');
    
    // Load existing tags (mit Filter)
    loadCatalogTags();
    filterExistingTags('', 'save');
    
    elements.saveCatalogModal.classList.add('active');
}

function closeSaveCatalogModal() {
    elements.saveCatalogModal.classList.remove('active');
    currentTags = [];
}

// === Utility Functions ===

function showToast(message, type = 'info') {
    // Bestehenden Toast entfernen
    const existingToast = document.querySelector('.toast');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Animation
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('de-DE', { 
        day: '2-digit', 
        month: '2-digit',
        year: '2-digit'
    });
}

// === Event Listeners ===

// Tastatur API URL
const KEYBOARD_API_URL = 'http://127.0.0.1:3847';

async function startKeyboard() {
    try {
        console.log('Starte Tastatur...');
        const response = await fetch(`${KEYBOARD_API_URL}/start`, { 
            method: 'POST',
            mode: 'no-cors'
        });
        console.log('Tastatur gestartet');
    } catch (error) {
        console.log('Tastatur-API nicht erreichbar:', error.message);
    }
}

async function stopKeyboard() {
    try {
        console.log('Stoppe Tastatur...');
        await fetch(`${KEYBOARD_API_URL}/stop`, { 
            method: 'POST',
            mode: 'no-cors'
        });
        console.log('Tastatur gestoppt');
    } catch (error) {
        console.log('Tastatur-API nicht erreichbar:', error.message);
    }
}

function setupEventListeners() {
    // Text input
    elements.textInput.addEventListener('input', () => {
        if (elements.charCount) {
            elements.charCount.textContent = `${elements.textInput.value.length} Zeichen`;
        }
    });
    
    // Tastatur starten bei Fokus
    elements.textInput.addEventListener('focus', () => {
        startKeyboard();
    });
    
    // Tastatur stoppen bei Fokusverlust
    elements.textInput.addEventListener('blur', () => {
        stopKeyboard();
    });
    
    // Enter key to speak
    elements.textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            speak();
        }
    });
    
    // TTS Model select
    if (elements.ttsModelSelect) {
        elements.ttsModelSelect.addEventListener('change', (e) => {
            switchTTSModel(e.target.value);
        });
    }
    
    // Voice select
    elements.voiceSelect.addEventListener('change', (e) => {
        loadVoiceModel(e.target.value);
    });
    
    // Language select - aktualisiert Katalog-Vorschau und Favoriten
    elements.languageSelect.addEventListener('change', () => {
        loadCatalogPreview();
        loadFavorites();
    });
    
    // TTS buttons
    elements.speakBtn.addEventListener('click', speak);
    elements.stopBtn.addEventListener('click', stopSpeaking);
    
    // Settings
    elements.settingsBtn.addEventListener('click', openSettingsModal);
    elements.closeSettingsBtn.addEventListener('click', closeSettingsModal);
    elements.saveSettingsBtn.addEventListener('click', saveSettings);
    
    elements.speedSlider.addEventListener('input', (e) => {
        elements.speedValue.textContent = `${e.target.value}x`;
    });
    elements.temperatureSlider.addEventListener('input', (e) => {
        elements.temperatureValue.textContent = e.target.value;
    });
    elements.repetitionSlider.addEventListener('input', (e) => {
        elements.repetitionValue.textContent = e.target.value;
    });
    
    // New Voice
    elements.newVoiceBtn.addEventListener('click', openNewVoiceModal);
    elements.deleteVoiceBtn.addEventListener('click', deleteVoiceModel);
    elements.closeNewVoiceBtn.addEventListener('click', closeNewVoiceModal);
    elements.cancelNewVoiceBtn.addEventListener('click', closeNewVoiceModal);
    elements.createVoiceBtn.addEventListener('click', createVoice);
    
    elements.fileDropZone.addEventListener('click', async () => {
        const result = await window.electronAPI.openFileDialog();
        if (!result.canceled && result.filePaths.length > 0) {
            // Read files via IPC and convert to File objects
            const files = await Promise.all(result.filePaths.map(async (filePath) => {
                const fileData = await window.electronAPI.readFileAsBuffer(filePath);
                const binaryString = atob(fileData.data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: fileData.mimeType });
                return new File([blob], fileData.fileName, { type: fileData.mimeType });
            }));
            handleFileSelect(files);
        }
    });
    
    elements.fileDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.fileDropZone.classList.add('dragover');
    });
    
    elements.fileDropZone.addEventListener('dragleave', () => {
        elements.fileDropZone.classList.remove('dragover');
    });
    
    elements.fileDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.fileDropZone.classList.remove('dragover');
        handleFileSelect(e.dataTransfer.files);
    });
    
    // Catalog
    elements.openCatalogBtn.addEventListener('click', openCatalogModal);
    elements.closeCatalogBtn.addEventListener('click', closeCatalogModal);
    
    elements.catalogSearch.addEventListener('input', debounce(loadCatalog, 300));
    elements.favoritesOnly.addEventListener('change', loadCatalog);
    
    // Catalog Tag Filter
    elements.catalogSelectedTags.addEventListener('click', () => {
        toggleTagDropdown(elements.catalogTagDropdown, !elements.catalogTagDropdown.classList.contains('active'));
    });
    elements.catalogTagSearch.addEventListener('input', (e) => {
        renderTagFilterList(elements.catalogTagList, 'catalog', e.target.value);
    });
    elements.tagModeAnd.addEventListener('click', () => setTagMode('and', 'catalog'));
    elements.tagModeOr.addEventListener('click', () => setTagMode('or', 'catalog'));
    
    // Main Tag Filter
    elements.mainSelectedTags.addEventListener('click', () => {
        toggleTagDropdown(elements.mainTagDropdown, !elements.mainTagDropdown.classList.contains('active'));
    });
    elements.mainTagSearch.addEventListener('input', (e) => {
        renderTagFilterList(elements.mainTagList, 'main', e.target.value);
    });
    elements.mainTagModeAnd.addEventListener('click', () => setTagMode('and', 'main'));
    elements.mainTagModeOr.addEventListener('click', () => setTagMode('or', 'main'));
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.tag-filter-container')) {
            toggleTagDropdown(elements.catalogTagDropdown, false);
            toggleTagDropdown(elements.mainTagDropdown, false);
        }
    });
    
    // Save to Catalog
    elements.closeSaveCatalogBtn.addEventListener('click', closeSaveCatalogModal);
    elements.cancelSaveCatalogBtn.addEventListener('click', closeSaveCatalogModal);
    elements.confirmSaveCatalogBtn.addEventListener('click', saveToCatalog);
    elements.autoTagsBtn.addEventListener('click', generateAutoTags);
    
    // Tag input for Save Catalog Modal
    elements.addTagBtn.addEventListener('click', () => {
        addTagFromInput(elements.tagInputField, elements.tagListContainer, 'save');
    });
    elements.tagInputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTagFromInput(elements.tagInputField, elements.tagListContainer, 'save');
        }
    });
    elements.tagInputField.addEventListener('input', (e) => {
        filterExistingTags(e.target.value, 'save');
    });
    
    // Edit Tags Modal
    elements.closeEditTagsBtn.addEventListener('click', closeEditTagsModal);
    elements.cancelEditTagsBtn.addEventListener('click', closeEditTagsModal);
    elements.confirmEditTagsBtn.addEventListener('click', saveEditedTags);
    
    // Tag input for Edit Tags Modal
    elements.addEditTagBtn.addEventListener('click', () => {
        addTagFromInput(elements.editTagInputField, elements.editTagListContainer, 'edit');
    });
    elements.editTagInputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTagFromInput(elements.editTagInputField, elements.editTagListContainer, 'edit');
        }
    });
    elements.editTagInputField.addEventListener('input', (e) => {
        filterExistingTags(e.target.value, 'edit');
    });
    
    // Import MP3 Modal
    elements.importMp3Btn.addEventListener('click', openImportMp3Modal);
    elements.closeImportMp3Btn.addEventListener('click', closeImportMp3Modal);
    elements.cancelImportMp3Btn.addEventListener('click', closeImportMp3Modal);
    elements.confirmImportMp3Btn.addEventListener('click', importMp3);
    elements.playImportAudioBtn.addEventListener('click', playImportAudio);
    elements.transcribeImportBtn.addEventListener('click', transcribeImportAudio);
    elements.importAutoTagsBtn.addEventListener('click', generateImportAutoTags);
    elements.importAudioPlayer.addEventListener('ended', () => {
        elements.playImportAudioBtn.textContent = '▶️';
    });
    setupImportDropZone();
    
    // Tag input for Import Modal
    elements.addImportTagBtn.addEventListener('click', () => {
        const tag = elements.importTagInputField.value.trim().toLowerCase();
        addImportTag(tag);
        elements.importTagInputField.value = '';
        filterExistingTags('', 'import');
    });
    elements.importTagInputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const tag = elements.importTagInputField.value.trim().toLowerCase();
            addImportTag(tag);
            elements.importTagInputField.value = '';
            filterExistingTags('', 'import');
        }
    });
    elements.importTagInputField.addEventListener('input', (e) => {
        filterExistingTags(e.target.value, 'import');
    });
    
    // Close modals on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(m => m.classList.remove('active'));
        }
        
        if (e.ctrlKey && e.key === 'Enter') {
            speak();
        }
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// === Initialization ===

async function init() {
    console.log('Initializing SpeakAlike...');
    
    setupEventListeners();
    
    // Wait for backend
    let connected = false;
    for (let i = 0; i < 10; i++) {
        const status = await checkStatus();
        if (status) {
            connected = true;
            break;
        }
        await new Promise(r => setTimeout(r, 1000));
    }
    
    if (connected) {
        // Katalog und History können sofort geladen werden
        loadCatalogTags();
        loadCatalogPreview();
        loadHistory();
        loadFavorites();
        
        // Voice-Models erst laden wenn TTS bereit ist
        await waitForTTSAndLoadModels();
    }
    
    // Periodic status check
    setInterval(checkStatus, 5000);
}

async function waitForTTSAndLoadModels() {
    // Warte bis TTS geladen ist (max 60 Sekunden)
    for (let i = 0; i < 60; i++) {
        const status = await api('/api/status');
        if (!status.loading) {
            loadVoiceModels();
            loadTTSModels();
            return;
        }
        await new Promise(r => setTimeout(r, 1000));
    }
    console.error('TTS loading timeout');
}

// === TTS Model Functions ===

async function loadTTSModels() {
    try {
        const response = await api('/api/tts/models');
        if (response && response.models) {
            availableTTSModels = response.models;
            currentTTSModel = response.current_model;
            
            // Dropdown aktualisieren
            if (elements.ttsModelSelect) {
                elements.ttsModelSelect.innerHTML = '';
                
                for (const [modelId, modelInfo] of Object.entries(availableTTSModels)) {
                    const option = document.createElement('option');
                    option.value = modelId;
                    option.textContent = modelInfo.name;
                    option.title = modelInfo.description;
                    if (modelId === currentTTSModel) {
                        option.selected = true;
                    }
                    elements.ttsModelSelect.appendChild(option);
                }
            }
            
            // Voice-Auswahl basierend auf Modell aktivieren/deaktivieren
            updateVoiceCloningAvailability();
        }
    } catch (error) {
        console.error('Fehler beim Laden der TTS-Modelle:', error);
    }
}

async function switchTTSModel(modelId) {
    if (modelId === currentTTSModel) return;
    
    try {
        updateStatus('Wechsle TTS-Modell...', 'connecting');
        
        const response = await api('/api/tts/models/switch', {
            method: 'POST',
            body: { model_id: modelId }
        });
        
        if (response && response.success) {
            currentTTSModel = response.model_id;
            updateStatus('Bereit', 'connected');
            
            // Voice-Auswahl aktualisieren
            updateVoiceCloningAvailability();
            
            // Voice neu laden falls nötig
            loadVoiceModels();
        } else {
            updateStatus('Modellwechsel fehlgeschlagen', 'error');
            // Dropdown zurücksetzen
            if (elements.ttsModelSelect) {
                elements.ttsModelSelect.value = currentTTSModel;
            }
        }
    } catch (error) {
        console.error('Fehler beim Modellwechsel:', error);
        updateStatus('Fehler beim Modellwechsel', 'error');
        // Dropdown zurücksetzen
        if (elements.ttsModelSelect) {
            elements.ttsModelSelect.value = currentTTSModel;
        }
    }
}

function updateVoiceCloningAvailability() {
    const modelInfo = availableTTSModels[currentTTSModel];
    const supportsCloning = modelInfo ? modelInfo.supports_cloning : true;
    
    // Voice-Auswahl und New Voice Button
    if (elements.voiceSelect) {
        elements.voiceSelect.disabled = !supportsCloning;
        if (!supportsCloning) {
            elements.voiceSelect.value = '';
        }
    }
    
    if (elements.newVoiceBtn) {
        elements.newVoiceBtn.disabled = !supportsCloning;
        elements.newVoiceBtn.title = supportsCloning ? 
            'Neue Stimme erstellen' : 
            'Dieses Modell unterstützt kein Voice Cloning';
    }
    
    // Sprach-Auswahl basierend auf Modell aktualisieren
    if (elements.languageSelect && modelInfo && modelInfo.languages) {
        const currentLang = elements.languageSelect.value;
        const availableLangs = modelInfo.languages;
        
        // Prüfen ob aktuelle Sprache unterstützt wird
        if (!availableLangs.includes(currentLang)) {
            // Auf erste verfügbare Sprache wechseln
            elements.languageSelect.value = availableLangs[0] || 'de';
        }
    }
}

// Start
document.addEventListener('DOMContentLoaded', init);
