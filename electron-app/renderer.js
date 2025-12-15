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

// DOM Elements
const elements = {
    // Status
    status: document.getElementById('status'),
    statusText: document.querySelector('.status-text'),
    
    // Voice
    voiceSelect: document.getElementById('voiceSelect'),
    currentVoice: document.getElementById('currentVoice'),
    newVoiceBtn: document.getElementById('newVoiceBtn'),
    
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
    catalogTagFilter: document.getElementById('catalogTagFilter'),
    favoritesOnly: document.getElementById('favoritesOnly'),
    catalogGrid: document.getElementById('catalogGrid'),
    
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
    
    // History
    historyList: document.getElementById('historyList')
};

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

function renderTagList(tags, container, isEdit = false) {
    container.innerHTML = '';
    tags.forEach((tag, index) => {
        const tagEl = document.createElement('span');
        tagEl.className = 'tag';
        tagEl.innerHTML = `
            ${escapeHtml(tag)}
            <button class="remove-tag" data-index="${index}">×</button>
        `;
        tagEl.querySelector('.remove-tag').onclick = () => {
            if (isEdit) {
                editCurrentTags.splice(index, 1);
                renderTagList(editCurrentTags, container, true);
            } else {
                currentTags.splice(index, 1);
                renderTagList(currentTags, container, false);
            }
        };
        container.appendChild(tagEl);
    });
}

function addTagFromInput(inputField, container, isEdit = false) {
    const tag = inputField.value.trim().toLowerCase();
    if (tag) {
        const tagList = isEdit ? editCurrentTags : currentTags;
        if (!tagList.includes(tag)) {
            tagList.push(tag);
            renderTagList(tagList, container, isEdit);
        }
        inputField.value = '';
    }
}

function addExistingTag(tag, isEdit = false) {
    const tagList = isEdit ? editCurrentTags : currentTags;
    const container = isEdit ? elements.editTagListContainer : elements.tagListContainer;
    if (!tagList.includes(tag)) {
        tagList.push(tag);
        renderTagList(tagList, container, isEdit);
    }
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

// === Text-to-Speech ===

async function speak() {
    const text = elements.textInput.value.trim();
    if (!text) {
        alert('Bitte geben Sie einen Text ein.');
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
            elements.audioPlayer.src = currentAudioUrl;
            elements.audioPlayer.play();
            
            // Zum Wiedergabe-Verlauf hinzufügen
            await addToPlaybackHistory(text, result.audio_url, null);
            
            // History aktualisieren
            loadHistory();
        }
    } catch (error) {
        alert(`Fehler: ${error.message}`);
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
        
        elements.catalogTagFilter.innerHTML = '<option value="">Alle Tags</option>';
        catalogTags.forEach(tag => {
            const option = document.createElement('option');
            option.value = tag.name;
            option.textContent = `${tag.name} (${tag.count})`;
            elements.catalogTagFilter.appendChild(option);
        });
        
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

async function loadCatalog() {
    try {
        const params = new URLSearchParams();
        if (elements.catalogSearch.value) params.set('search', elements.catalogSearch.value);
        if (elements.catalogTagFilter.value) params.set('tag', elements.catalogTagFilter.value);
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

async function loadCatalogPreview() {
    try {
        // Lade die neuesten 5 Einträge für die Vorschau
        const messages = await api('/api/catalog?limit=5');
        
        if (messages.length === 0) {
            elements.catalogPreview.innerHTML = '<p class="muted">Noch keine Einträge im Katalog</p>';
            return;
        }
        
        elements.catalogPreview.innerHTML = '';
        messages.forEach(msg => {
            const item = document.createElement('div');
            item.className = 'catalog-preview-item';
            item.innerHTML = `
                <span class="preview-text">${escapeHtml(msg.text.substring(0, 50))}${msg.text.length > 50 ? '...' : ''}</span>
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

let currentHistoryItem = null;

function openSaveCatalogModalForHistory(item) {
    currentHistoryItem = item;
    currentText = item.text;
    currentAudioUrl = `${window.API_URL}${item.audio_url}`;
    
    elements.saveTextPreview.textContent = item.text;
    
    // Reset current tags
    currentTags = [];
    renderTagList(currentTags, elements.tagListContainer, false);
    
    // Existing tags anzeigen
    elements.existingTagsList.innerHTML = '';
    catalogTags.forEach(tag => {
        const tagBtn = document.createElement('button');
        tagBtn.className = 'tag clickable';
        tagBtn.textContent = tag.name;
        tagBtn.onclick = () => addExistingTag(tag.name, false);
        elements.existingTagsList.appendChild(tagBtn);
    });
    
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

async function toggleFavorite(id) {
    try {
        await api(`/api/catalog/${id}/favorite`, { method: 'PUT' });
        loadCatalog();
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
    renderTagList(editCurrentTags, elements.editTagListContainer, true);
    
    // Show existing tags
    elements.editExistingTagsList.innerHTML = '';
    catalogTags.forEach(tag => {
        const tagBtn = document.createElement('button');
        tagBtn.className = 'tag clickable';
        tagBtn.textContent = tag.name;
        tagBtn.onclick = () => addExistingTag(tag.name, true);
        elements.editExistingTagsList.appendChild(tagBtn);
    });
    
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
    
    // Add language tag
    const langNames = {
        'de': 'deutsch', 'en': 'englisch', 'es': 'spanisch', 'fr': 'französisch',
        'it': 'italienisch', 'pt': 'portugiesisch', 'pl': 'polnisch', 'tr': 'türkisch',
        'ru': 'russisch', 'nl': 'niederländisch', 'ja': 'japanisch', 'zh-cn': 'chinesisch'
    };
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
        alert('Zum Katalog hinzugefügt!');
        loadCatalogTags();
    } catch (error) {
        alert(`Fehler: ${error.message}`);
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
            renderTagList(currentTags, elements.tagListContainer, false);
        }
    } catch (error) {
        console.error('Auto-tags error:', error);
    } finally {
        elements.autoTagsBtn.disabled = false;
        elements.autoTagsBtn.textContent = '🤖 Auto-Tags';
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
        alert(`Stimme "${name}" erfolgreich erstellt!`);
        loadVoiceModels();
    } catch (error) {
        alert(`Fehler: ${error.message}`);
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
    renderTagList(currentTags, elements.tagListContainer, false);
    
    // Load existing tags
    loadCatalogTags();
    elements.existingTagsList.innerHTML = '';
    catalogTags.forEach(tag => {
        const tagBtn = document.createElement('button');
        tagBtn.className = 'tag clickable';
        tagBtn.textContent = tag.name;
        tagBtn.onclick = () => addExistingTag(tag.name, false);
        elements.existingTagsList.appendChild(tagBtn);
    });
    
    elements.saveCatalogModal.classList.add('active');
}

function closeSaveCatalogModal() {
    elements.saveCatalogModal.classList.remove('active');
    currentTags = [];
}

// === Utility Functions ===

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

function setupEventListeners() {
    // Text input
    elements.textInput.addEventListener('input', () => {
        elements.charCount.textContent = `${elements.textInput.value.length} Zeichen`;
    });
    
    // Enter key to speak
    elements.textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            speak();
        }
    });
    
    // Voice select
    elements.voiceSelect.addEventListener('change', (e) => {
        loadVoiceModel(e.target.value);
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
    elements.closeNewVoiceBtn.addEventListener('click', closeNewVoiceModal);
    elements.cancelNewVoiceBtn.addEventListener('click', closeNewVoiceModal);
    elements.createVoiceBtn.addEventListener('click', createVoice);
    
    elements.fileDropZone.addEventListener('click', async () => {
        const result = await window.electronAPI.openFileDialog();
        if (!result.canceled && result.filePaths.length > 0) {
            // Convert file paths to File objects
            // Note: This is simplified - in real app need proper file handling
            console.log('Selected files:', result.filePaths);
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
    elements.catalogTagFilter.addEventListener('change', loadCatalog);
    elements.favoritesOnly.addEventListener('change', loadCatalog);
    
    // Save to Catalog
    elements.closeSaveCatalogBtn.addEventListener('click', closeSaveCatalogModal);
    elements.cancelSaveCatalogBtn.addEventListener('click', closeSaveCatalogModal);
    elements.confirmSaveCatalogBtn.addEventListener('click', saveToCatalog);
    elements.autoTagsBtn.addEventListener('click', generateAutoTags);
    
    // Tag input for Save Catalog Modal
    elements.addTagBtn.addEventListener('click', () => {
        addTagFromInput(elements.tagInputField, elements.tagListContainer, false);
    });
    elements.tagInputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTagFromInput(elements.tagInputField, elements.tagListContainer, false);
        }
    });
    
    // Edit Tags Modal
    elements.closeEditTagsBtn.addEventListener('click', closeEditTagsModal);
    elements.cancelEditTagsBtn.addEventListener('click', closeEditTagsModal);
    elements.confirmEditTagsBtn.addEventListener('click', saveEditedTags);
    
    // Tag input for Edit Tags Modal
    elements.addEditTagBtn.addEventListener('click', () => {
        addTagFromInput(elements.editTagInputField, elements.editTagListContainer, true);
    });
    elements.editTagInputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTagFromInput(elements.editTagInputField, elements.editTagListContainer, true);
        }
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
            return;
        }
        await new Promise(r => setTimeout(r, 1000));
    }
    console.error('TTS loading timeout');
}

// Start
document.addEventListener('DOMContentLoaded', init);
