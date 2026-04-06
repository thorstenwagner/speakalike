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
let privacyMode = false;

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
    privacyLastWord: document.getElementById('privacyLastWord'),
    privacyIndicator: document.getElementById('privacyIndicator'),
    languageSelect: document.getElementById('languageSelect'),
    charCount: document.getElementById('charCount'),
    speakBtn: document.getElementById('speakBtn'),
    generateBtn: document.getElementById('generateBtn'),
    
    // Volume
    volumeSlider: document.getElementById('volumeSlider'),
    volumeIcon: document.getElementById('volumeIcon'),
    volumeValue: document.getElementById('volumeValue'),
    
    // Audio
    audioPlayer: document.getElementById('audioPlayer'),
    
    // Catalog Preview
    catalogPreview: document.getElementById('catalogPreview'),
    openCatalogBtn: document.getElementById('openCatalogBtn'),
    
    // Settings Modal
    settingsBtn: document.getElementById('settingsBtn'),
    settingsModal: document.getElementById('settingsModal'),
    closeSettingsBtn: document.getElementById('closeSettingsBtn'),
    audioDeviceSelect: document.getElementById('audioDeviceSelect'),
    refreshDevicesBtn: document.getElementById('refreshDevicesBtn'),
    micDeviceSelect: document.getElementById('micDeviceSelect'),
    micToggleBtn: document.getElementById('micToggleBtn'),
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
    
    // AI Mode

    apiKeyInput: document.getElementById('apiKeyInput'),
    aiModelSelect: document.getElementById('aiModelSelect'),
    aiContextInput: document.getElementById('aiContextInput'),
    
    // ElevenLabs
    ttsProviderSelect: document.getElementById('ttsProviderSelect'),
    elevenlabsSettings: document.getElementById('elevenlabsSettings'),
    coquiSettings: document.getElementById('coquiSettings'),
    elevenlabsApiKeyInput: document.getElementById('elevenlabsApiKeyInput'),
    elevenlabsVoiceSelect: document.getElementById('elevenlabsVoiceSelect'),
    elevenlabsModelSelect: document.getElementById('elevenlabsModelSelect'),
    refreshElevenVoicesBtn: document.getElementById('refreshElevenVoicesBtn'),
    elevenStabilitySlider: document.getElementById('elevenStabilitySlider'),
    elevenStabilityValue: document.getElementById('elevenStabilityValue'),
    elevenSimilaritySlider: document.getElementById('elevenSimilaritySlider'),
    elevenSimilarityValue: document.getElementById('elevenSimilarityValue'),
    elevenStyleSlider: document.getElementById('elevenStyleSlider'),
    elevenStyleValue: document.getElementById('elevenStyleValue'),
    elevenSpeakerBoostCheckbox: document.getElementById('elevenSpeakerBoostCheckbox'),
    
    // AI Confirm Modal
    aiConfirmModal: document.getElementById('aiConfirmModal'),
    closeAiConfirmBtn: document.getElementById('closeAiConfirmBtn'),
    aiOriginalText: document.getElementById('aiOriginalText'),
    aiCompletedText: document.getElementById('aiCompletedText'),
    rejectAiBtn: document.getElementById('rejectAiBtn'),
    acceptAiBtn: document.getElementById('acceptAiBtn'),
    
    // History
    historyList: document.getElementById('historyList'),
    
    // Favorites
    favoritesList: document.getElementById('favoritesList'),
    
    // Quick Access
    quickAccessList: document.getElementById('quickAccessList'),
    clearQuickAccessBtn: document.getElementById('clearQuickAccessBtn'),
    
    // Global Search
    globalSearchInput: document.getElementById('globalSearchInput'),
    searchModeOr: document.getElementById('searchModeOr'),
    searchModeAnd: document.getElementById('searchModeAnd'),
    clearSearchBtn: document.getElementById('clearSearchBtn'),
    toggleViewBtn: document.getElementById('toggleViewBtn'),
    
    // Tag Browser
    tagBrowserRow: document.getElementById('tagBrowserRow'),
    tagCloud: document.getElementById('tagCloud'),
    tagBrowserActiveFilters: document.getElementById('tagBrowserActiveFilters'),
    clearTagBrowserFilters: document.getElementById('clearTagBrowserFilters'),
    tagBrowserMessagesList: document.getElementById('tagBrowserMessagesList'),
    tagBrowserMessagesTitle: document.getElementById('tagBrowserMessagesTitle'),
    tagBrowserCount: document.getElementById('tagBrowserCount'),
    
    // Mini-Modus
    miniModeBtn: document.getElementById('miniModeBtn'),

    miniRepeatBtn: document.getElementById('miniRepeatBtn'),
    miniPositionBtn: document.getElementById('miniPositionBtn'),
    miniExitBtn: document.getElementById('miniExitBtn'),
    toggleInputPositionBtn: document.getElementById('toggleInputPositionBtn')
};

// === Tag Filter State ===
let catalogSelectedTagsList = [];
let catalogTagMode = 'and';
let mainSelectedTagsList = [];
let mainTagMode = 'and';

// === Global Search State ===
let globalSearchTerms = [];
let globalSearchMode = 'or'; // Default: ODER

// === API Functions ===

async function api(endpoint, options = {}) {
    try {
        const { headers: extraHeaders, ...restOptions } = options;
        const response = await fetch(`${window.API_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...extraHeaders
            },
            ...restOptions
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
            elements.speakBtn.innerHTML = '⏳ <span class="hide-in-mini">TTS lädt...</span>';
            elements.status.classList.add('loading');
        } else {
            elements.speakBtn.disabled = false;
            elements.speakBtn.innerHTML = '🔊 <span class="hide-in-mini">Sprechen</span>';
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

// AI Sentence Completion
async function completeWithAI(text) {
    const apiKey = localStorage.getItem('claudeApiKey') || '';
    if (!apiKey) {
        showToast('Bitte API Key in den Einstellungen hinterlegen.', 'error');
        return null;
    }
    
    // Letzte 5 Minuten Nachrichten als Kontext holen
    let recentMessages = [];
    try {
        const history = await api('/api/history');
        if (history && history.length > 0) {
            const fiveMinAgo = Date.now() - 5 * 60 * 1000;
            recentMessages = history
                .filter(item => new Date(item.timestamp).getTime() > fiveMinAgo)
                .map(item => item.text)
                .reverse(); // älteste zuerst
        }
    } catch (e) {
        console.warn('Could not load recent history for AI context:', e);
    }
    
    try {
        const result = await api('/api/ai/complete-sentence', {
            method: 'POST',
            headers: {
                'X-API-Key': apiKey
            },
            body: JSON.stringify({
                text,
                model: localStorage.getItem('claudeModel') || 'claude-haiku-4-5-20251001',
                language: elements.languageSelect.value || 'de',
                context: localStorage.getItem('aiContext') || '',
                recent_messages: recentMessages
            })
        });
        return result.completed;
    } catch (error) {
        console.error('AI Completion Error:', error);
        showToast(`KI-Fehler: ${error.message}`, 'error');
        return null;
    }
}

// Show AI Confirm Modal and wait for user decision
function showAiConfirmModal(original, completed) {
    return new Promise((resolve) => {
        elements.aiOriginalText.textContent = original;
        elements.aiCompletedText.value = completed;
        elements.aiConfirmModal.classList.add('active');
        // Fokus auf das editierbare Textfeld
        setTimeout(() => elements.aiCompletedText.focus(), 100);
        
        const cleanup = () => {
            elements.aiConfirmModal.classList.remove('active');
            elements.acceptAiBtn.removeEventListener('click', onAccept);
            elements.rejectAiBtn.removeEventListener('click', onReject);
            elements.closeAiConfirmBtn.removeEventListener('click', onReject);
        };
        
        const onAccept = () => {
            const editedText = elements.aiCompletedText.value.trim();
            cleanup();
            resolve(editedText || completed);
        };
        
        const onReject = () => {
            cleanup();
            resolve(null);  // null = abbrechen, nicht sprechen
        };
        
        elements.acceptAiBtn.addEventListener('click', onAccept);
        elements.rejectAiBtn.addEventListener('click', onReject);
        elements.closeAiConfirmBtn.addEventListener('click', onReject);
    });
}

async function speak() {
    let text = elements.textInput.value.trim();
    if (!text) {
        showToast('Bitte geben Sie einen Text ein.', 'error');
        return;
    }
    
    // AI-Flag zurücksetzen
    delete elements.textInput.dataset.aiCompleted;
    
    currentText = text;
    elements.speakBtn.disabled = true;
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
            
            // Audio über Backend auf ausgewähltem Gerät abspielen
            try {
                const volume = elements.volumeSlider.value / 100;
                await api('/api/tts/play-audio', {
                    method: 'POST',
                    body: JSON.stringify({
                        audio_url: result.audio_url,
                        volume: volume
                    })
                });
                console.log('Audio wird auf Backend-Gerät abgespielt');
            } catch (playError) {
                console.error('Backend Play Fehler:', playError);
                // Fallback: Im Browser abspielen
                elements.audioPlayer.src = currentAudioUrl;
                await elements.audioPlayer.play();
            }
            
            // Zum Wiedergabe-Verlauf hinzufügen
            await addToPlaybackHistory(text, result.audio_url, null);
            
            // History aktualisieren
            loadHistory();
            
            // Textfeld leeren
            elements.textInput.value = '';
            updatePrivacyOverlay();
            if (elements.charCount) {
                elements.charCount.textContent = '0 Zeichen';
            }
        }
    } catch (error) {
        showToast(`Fehler: ${error.message}`, 'error');
    } finally {
        elements.speakBtn.disabled = false;
        checkStatus();
    }
}

// Nur generieren ohne abspielen
async function generateOnly() {
    const text = elements.textInput.value.trim();
    if (!text) {
        showToast('Bitte geben Sie einen Text ein.', 'error');
        return;
    }
    
    currentText = text;
    elements.generateBtn.disabled = true;
    elements.speakBtn.disabled = true;
    const originalText = elements.generateBtn.textContent;
    elements.generateBtn.textContent = '⏳ Generiere...';
    elements.statusText.textContent = 'Generiere Audio im Hintergrund...';
    
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
            console.log('Audio generiert (nicht abgespielt):', currentAudioUrl);
            
            // Zum Wiedergabe-Verlauf hinzufügen
            await addToPlaybackHistory(text, result.audio_url, null);
            
            // History aktualisieren
            loadHistory();
            
            // Textfeld leeren
            elements.textInput.value = '';
            updatePrivacyOverlay();
            if (elements.charCount) {
                elements.charCount.textContent = '0 Zeichen';
            }
            
            showToast('Audio erfolgreich generiert!', 'success');
        }
    } catch (error) {
        showToast(`Fehler: ${error.message}`, 'error');
    } finally {
        elements.generateBtn.disabled = false;
        elements.speakBtn.disabled = false;
        elements.generateBtn.textContent = originalText;
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
    checkStatus();
}

// === Catalog ===

async function loadCatalogTags() {
    try {
        catalogTags = await api('/api/catalog/tags');
        
        // Render tag filter lists
        renderTagFilterList(elements.catalogTagList, 'catalog');
        renderTagFilterList(elements.mainTagList, 'main');
        
        // Update existing tags in save dialog - use existingTagsList (not existingTags container)
        if (elements.existingTagsList) {
            elements.existingTagsList.innerHTML = '';
            catalogTags.slice(0, 15).forEach(tag => {
                const tagEl = document.createElement('button');
                tagEl.className = 'tag clickable';
                tagEl.textContent = tag.name;
                tagEl.onclick = () => addExistingTag(tag.name, 'save');
                elements.existingTagsList.appendChild(tagEl);
            });
        }
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
        
        // Globale Suche anwenden
        messages = messages.filter(msg => matchesGlobalSearch(msg));
        
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
            const noResultsText = globalSearchTerms.length > 0 ? 'Keine Treffer' : 'Noch keine Einträge im Katalog';
            elements.catalogPreview.innerHTML = `<p class="muted">${noResultsText}</p>`;
            return;
        }
        
        elements.catalogPreview.innerHTML = '';
        messages.forEach(msg => {
            const item = document.createElement('div');
            item.className = 'catalog-preview-item';
            item.innerHTML = `
                <span class="preview-text">${escapeHtml(msg.text.substring(0, 40))}${msg.text.length > 40 ? '...' : ''}</span>
                <div class="preview-actions">
                    <button class="btn btn-small play-btn" data-id="${msg.id}">▶️</button>
                    <button class="btn btn-small add-quick-btn" title="Zum Schnellzugriff">➕</button>
                </div>
            `;
            item.querySelector('.play-btn').onclick = () => playCatalogAudio(msg.id, msg.text);
            item.querySelector('.add-quick-btn').onclick = () => addToQuickAccess(msg);
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
        
        // Globale Suche anwenden
        const filteredHistory = history.filter(item => matchesGlobalSearch(item));
        
        if (filteredHistory.length === 0) {
            elements.historyList.innerHTML = '<p class="muted">Keine Treffer</p>';
            return;
        }
        
        elements.historyList.innerHTML = '';
        filteredHistory.forEach(item => {
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
                    <button class="btn btn-small add-quick-btn" title="Zum Schnellzugriff">➕</button>
                    <button class="btn btn-small save-btn" title="Speichern">💾</button>
                    ${!item.in_catalog ? '<button class="btn btn-small catalog-btn" title="Zum Katalog">📁</button>' : ''}
                </div>
            `;
            div.querySelector('.play-btn').onclick = () => playHistoryAudio(item.audio_url, item.text, item.catalog_id);
            div.querySelector('.add-quick-btn').onclick = () => addToQuickAccess({
                id: item.catalog_id || `history_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                text: item.text,
                audio_url: item.audio_url,
                is_favorite: false
            });
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
    // Audio über Backend auf ausgewähltem Gerät abspielen
    try {
        const volume = elements.volumeSlider.value / 100;
        await api('/api/tts/play-audio', {
            method: 'POST',
            body: JSON.stringify({ audio_url: audioUrl, volume: volume })
        });
    } catch (error) {
        console.error('Backend Play Fehler:', error);
        // Fallback: Im Browser abspielen
        elements.audioPlayer.src = `${window.API_URL}${audioUrl}`;
        elements.audioPlayer.play();
    }
    
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
        
        let filtered = allFavorites.filter(item => {
            const itemTags = item.tags || [];
            const matches = matchesLanguageFilter(item, langTag);
            
            if (!matches) {
                console.log(`  ✗ Gefiltert: "${item.text.substring(0, 30)}..." | Tags: [${itemTags.join(', ')}]`);
            }
            return matches;
        });
        
        console.log(`Nach Sprachfilter: ${filtered.length} (${allFavorites.length - filtered.length} entfernt)`);
        
        // Globale Suche anwenden
        filtered = filtered.filter(item => matchesGlobalSearch(item));
        
        const favorites = filtered.slice(0, 20);
        if (filtered.length > 20) {
            console.log(`Abgeschnitten bei 20 (${filtered.length - 20} weitere nicht angezeigt)`);
        }
        
        favorites.forEach(item => {
            const tags = item.tags || [];
            console.log(`  ✓ "${item.text.substring(0, 30)}..." | Tags: [${tags.join(', ')}]`);
        });
        
        if (favorites.length === 0) {
            const noResultsText = globalSearchTerms.length > 0 ? 'Keine Treffer' : 'Keine Favoriten für diese Sprache';
            elements.favoritesList.innerHTML = `<p class="muted">${noResultsText}</p>`;
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
                    <button class="btn btn-small add-quick-btn" title="Zum Schnellzugriff">➕</button>
                    <button class="btn btn-small unfav-btn" title="Entfernen">⭐</button>
                </div>
            `;
            div.querySelector('.play-btn').onclick = () => playCatalogItem(item);
            div.querySelector('.add-quick-btn').onclick = () => addToQuickAccess(item);
            div.querySelector('.unfav-btn').onclick = () => toggleFavorite(item.id, false);
            elements.favoritesList.appendChild(div);
        });
    } catch (error) {
        console.error('Failed to load favorites:', error);
    }
}

async function playCatalogItem(item) {
    if (item.audio_url) {
        // Audio über Backend auf ausgewähltem Gerät abspielen
        try {
            const volume = elements.volumeSlider.value / 100;
            await api('/api/tts/play-audio', {
                method: 'POST',
                body: JSON.stringify({ audio_url: item.audio_url, volume: volume })
            });
        } catch (error) {
            console.error('Backend Play Fehler:', error);
            // Fallback: Im Browser abspielen
            elements.audioPlayer.src = `${window.API_URL}${item.audio_url}`;
            elements.audioPlayer.play();
        }
        
        // Play count erhöhen
        await api(`/api/catalog/${item.id}/play`, { method: 'POST' });
        loadFavorites();
        loadCatalogPreview();
        loadQuickAccess();
    }
}

// === Quick Access ===

// Schnellzugriff-Liste wird im localStorage gespeichert
let quickAccessItems = [];

function loadQuickAccessFromStorage() {
    try {
        const stored = localStorage.getItem('quickAccessItems');
        if (stored) {
            quickAccessItems = JSON.parse(stored);
        }
    } catch (e) {
        quickAccessItems = [];
    }
}

function saveQuickAccessToStorage() {
    try {
        localStorage.setItem('quickAccessItems', JSON.stringify(quickAccessItems));
    } catch (e) {
        console.error('Failed to save quick access:', e);
    }
}

function addToQuickAccess(item) {
    // Prüfen ob schon vorhanden
    const exists = quickAccessItems.some(q => q.id === item.id);
    if (exists) {
        showToast('Bereits im Schnellzugriff', 'info');
        return;
    }
    
    // Am Anfang hinzufügen (inkl. tags für Suchfilter)
    quickAccessItems.unshift({
        id: item.id,
        text: item.text,
        audio_url: item.audio_url,
        is_favorite: item.is_favorite,
        tags: item.tags || []
    });
    
    // Max 20 Items
    if (quickAccessItems.length > 20) {
        quickAccessItems = quickAccessItems.slice(0, 20);
    }
    
    saveQuickAccessToStorage();
    renderQuickAccess();
    showToast('Zum Schnellzugriff hinzugefügt', 'success');
}

function removeFromQuickAccess(itemId) {
    quickAccessItems = quickAccessItems.filter(q => q.id !== itemId);
    saveQuickAccessToStorage();
    renderQuickAccess();
}

let clearQuickAccessPending = false;

function clearQuickAccess() {
    if (quickAccessItems.length === 0) return;
    
    // Doppelklick zum Bestätigen
    if (!clearQuickAccessPending) {
        clearQuickAccessPending = true;
        showToast('Nochmal klicken zum Bestätigen', 'info');
        setTimeout(() => {
            clearQuickAccessPending = false;
        }, 2000);
        return;
    }
    
    clearQuickAccessPending = false;
    quickAccessItems = [];
    saveQuickAccessToStorage();
    renderQuickAccess();
    showToast('Schnellzugriff geleert', 'success');
}

function renderQuickAccess() {
    if (!elements.quickAccessList) return;
    
    // Globale Suche anwenden
    const filteredItems = quickAccessItems.filter(item => matchesGlobalSearch(item));
    
    if (filteredItems.length === 0) {
        const emptyText = globalSearchTerms.length > 0 ? 'Keine Treffer' : 'Nachrichten hier hinzufügen mit dem ➕ Button';
        elements.quickAccessList.innerHTML = `<p class="muted">${emptyText}</p>`;
        return;
    }
    
    elements.quickAccessList.innerHTML = '';
    filteredItems.forEach(item => {
        const div = document.createElement('div');
        div.className = 'quick-access-item';
        
        const textPreview = item.text.substring(0, 50) + (item.text.length > 50 ? '...' : '');
        
        div.innerHTML = `
            <span class="quick-text" title="${escapeHtml(item.text)}">${escapeHtml(textPreview)}</span>
            <div class="quick-actions">
                <button class="btn btn-success btn-small play-btn" title="Abspielen">▶️</button>
                <button class="btn btn-secondary btn-small use-btn" title="Text übernehmen">📝</button>
                <button class="btn btn-danger btn-small remove-btn" title="Entfernen">✕</button>
            </div>
        `;
        
        div.querySelector('.play-btn').onclick = (e) => {
            e.stopPropagation();
            playQuickAccessItem(item);
        };
        div.querySelector('.use-btn').onclick = (e) => {
            e.stopPropagation();
            useQuickAccessText(item);
        };
        div.querySelector('.remove-btn').onclick = (e) => {
            e.stopPropagation();
            removeFromQuickAccess(item.id);
        };
        
        // Klick auf Karte = Abspielen
        div.onclick = () => playQuickAccessItem(item);
        
        elements.quickAccessList.appendChild(div);
    });
}

async function playQuickAccessItem(item) {
    if (item.audio_url) {
        // Audio über Backend auf ausgewähltem Gerät abspielen
        try {
            const volume = elements.volumeSlider.value / 100;
            await api('/api/tts/play-audio', {
                method: 'POST',
                body: JSON.stringify({ audio_url: item.audio_url, volume: volume })
            });
        } catch (error) {
            console.error('Backend Play Fehler:', error);
            // Fallback: Im Browser abspielen
            elements.audioPlayer.src = `${window.API_URL}${item.audio_url}`;
            elements.audioPlayer.play();
        }
        
        // Play count erhöhen
        await api(`/api/catalog/${item.id}/play`, { method: 'POST' });
    }
}

function useQuickAccessText(item) {
    if (elements.textInput) {
        elements.textInput.value = item.text;
        elements.textInput.focus();
    }
}

// === Global Search ===

function handleGlobalSearch() {
    const searchValue = elements.globalSearchInput.value.trim().toLowerCase();
    
    if (!searchValue) {
        globalSearchTerms = [];
    } else {
        // Aufteilen in einzelne Suchbegriffe (durch Leerzeichen getrennt)
        globalSearchTerms = searchValue.split(/\s+/).filter(term => term.length > 0);
    }
    
    // Alle 4 Spalten neu laden/filtern
    applyGlobalSearch();
}

function setGlobalSearchMode(mode) {
    globalSearchMode = mode;
    updateSearchModeButtons();
    
    // Suche erneut anwenden wenn Suchbegriffe vorhanden
    if (globalSearchTerms.length > 0) {
        applyGlobalSearch();
    }
}

function updateSearchModeButtons() {
    if (elements.searchModeOr) {
        elements.searchModeOr.classList.toggle('active', globalSearchMode === 'or');
    }
    if (elements.searchModeAnd) {
        elements.searchModeAnd.classList.toggle('active', globalSearchMode === 'and');
    }
}

function clearGlobalSearch() {
    if (elements.globalSearchInput) {
        elements.globalSearchInput.value = '';
    }
    globalSearchTerms = [];
    applyGlobalSearch();
}

function applyGlobalSearch() {
    // Alle Spalten aktualisieren
    loadHistory();
    loadFavorites();
    loadCatalogPreview();
    renderQuickAccess();
}

function matchesGlobalSearch(item) {
    // Wenn keine Suchbegriffe, alles anzeigen
    if (globalSearchTerms.length === 0) {
        return true;
    }
    
    // Text und Tags zum Durchsuchen vorbereiten
    const text = (item.text || '').toLowerCase();
    const tags = (item.tags || []).map(t => t.toLowerCase());
    const searchableContent = text + ' ' + tags.join(' ');
    
    if (globalSearchMode === 'or') {
        // ODER: Mindestens ein Begriff muss matchen
        return globalSearchTerms.some(term => searchableContent.includes(term));
    } else {
        // UND: Alle Begriffe müssen matchen
        return globalSearchTerms.every(term => searchableContent.includes(term));
    }
}

// === Tag-Browser View ===
let isTagBrowserView = false;
let tagBrowserSelectedTags = [];

function toggleView() {
    isTagBrowserView = !isTagBrowserView;
    
    const bottomRow = document.querySelector('.bottom-row');
    if (isTagBrowserView) {
        bottomRow.style.display = 'none';
        elements.tagBrowserRow.style.display = 'flex';
        elements.toggleViewBtn.innerHTML = '📊 Spalten';
        elements.toggleViewBtn.title = 'Zur Spalten-Ansicht wechseln';
        loadTagCloud();
    } else {
        bottomRow.style.display = 'flex';
        elements.tagBrowserRow.style.display = 'none';
        elements.toggleViewBtn.innerHTML = '🏷️ Tag-Browser';
        elements.toggleViewBtn.title = 'Zum Tag-Browser wechseln';
    }
    
    localStorage.setItem('viewMode', isTagBrowserView ? 'tags' : 'columns');
}

function loadTagCloud(filteredTags) {
    // Wenn Tags selektiert sind, zeige nur Tags aus den gefilterten Nachrichten
    const tags = filteredTags || catalogTags;
    
    if (!tags || tags.length === 0) {
        elements.tagCloud.innerHTML = '<p class="muted">Keine Tags vorhanden</p>';
        return;
    }
    
    const maxCount = Math.max(...tags.map(t => t.count));
    const minCount = Math.min(...tags.map(t => t.count));
    
    // Tags rendern mit relativer Gewichtung (0-1)
    elements.tagCloud.innerHTML = '';
    const tagElements = [];
    tags.forEach(tag => {
        const weight = maxCount === minCount ? 1 : (tag.count - minCount) / (maxCount - minCount);
        const isActive = tagBrowserSelectedTags.includes(tag.name);
        
        const el = document.createElement('div');
        el.className = `tag-cloud-item ${isActive ? 'active' : ''}`;
        el.dataset.weight = weight;
        el.innerHTML = `${escapeHtml(tag.name)} <span class="tag-cloud-count">${tag.count}</span>`;
        el.onclick = () => toggleTagBrowserFilter(tag.name);
        elements.tagCloud.appendChild(el);
        tagElements.push(el);
    });
    
    // Auto-Skalierung: Schriftgröße so groß wie möglich ohne Scrollen
    requestAnimationFrame(() => fitTagCloud(tagElements));
}

function fitTagCloud(tagElements) {
    if (!tagElements.length) return;
    const container = elements.tagCloud;
    const containerH = container.clientHeight;
    if (containerH <= 0) return;
    
    // Basis-Schriftgrößen: Min und Max in px
    const MIN_BASE = 0.7;
    const MAX_BASE = 3.0;
    let lo = MIN_BASE, hi = MAX_BASE;
    
    // Binäre Suche nach optimaler Basisgröße
    for (let i = 0; i < 10; i++) {
        const mid = (lo + hi) / 2;
        applyTagSizes(tagElements, mid);
        if (container.scrollHeight > containerH + 2) {
            hi = mid;
        } else {
            lo = mid;
        }
    }
    applyTagSizes(tagElements, lo);
}

function applyTagSizes(tagElements, baseRem) {
    tagElements.forEach(el => {
        const w = parseFloat(el.dataset.weight);
        // Gewichtete Größe: kleine Tags = 60% der Basis, große = 100%
        const size = baseRem * (0.6 + 0.4 * w);
        el.style.fontSize = `${size}rem`;
        const pad = Math.max(4, size * 5);
        el.style.padding = `${pad * 0.5}px ${pad}px`;
    });
}

function toggleTagBrowserFilter(tagName) {
    const index = tagBrowserSelectedTags.indexOf(tagName);
    if (index > -1) {
        tagBrowserSelectedTags.splice(index, 1);
    } else {
        tagBrowserSelectedTags.push(tagName);
    }
    
    updateTagBrowserActiveFilters();
    loadTagBrowserMessages(); // lädt Nachrichten und aktualisiert Tag-Cloud
}

function updateTagBrowserActiveFilters() {
    if (tagBrowserSelectedTags.length === 0) {
        elements.tagBrowserActiveFilters.innerHTML = '';
        elements.clearTagBrowserFilters.style.display = 'none';
        return;
    }
    
    elements.clearTagBrowserFilters.style.display = '';
    elements.tagBrowserActiveFilters.innerHTML = tagBrowserSelectedTags.map(tag => `
        <span class="tag" onclick="toggleTagBrowserFilter('${escapeHtml(tag)}')">${escapeHtml(tag)} ×</span>
    `).join('');
}

function clearAllTagBrowserFilters() {
    tagBrowserSelectedTags = [];
    updateTagBrowserActiveFilters();
    loadTagCloud(); // Alle Tags anzeigen
    elements.tagBrowserMessagesList.innerHTML = '<p class="muted">Wähle einen Tag um Nachrichten anzuzeigen</p>';
    elements.tagBrowserCount.textContent = '';
}

async function loadTagBrowserMessages() {
    if (tagBrowserSelectedTags.length === 0) {
        elements.tagBrowserMessagesList.innerHTML = '<p class="muted">Wähle einen Tag um Nachrichten anzuzeigen</p>';
        elements.tagBrowserCount.textContent = '';
        return;
    }
    
    try {
        const params = new URLSearchParams();
        params.set('tags', tagBrowserSelectedTags.join(','));
        params.set('tag_mode', 'and');
        params.set('limit', '100');
        
        const messages = await api(`/api/catalog?${params.toString()}`);
        
        // Tags aus gefilterten Nachrichten extrahieren und Tag-Cloud aktualisieren
        const tagCounts = {};
        messages.forEach(msg => {
            (msg.tags || []).forEach(t => {
                tagCounts[t] = (tagCounts[t] || 0) + 1;
            });
        });
        const filteredTags = Object.entries(tagCounts)
            .map(([name, count]) => ({ name, count }))
            .sort((a, b) => b.count - a.count);
        loadTagCloud(filteredTags);
        
        elements.tagBrowserCount.textContent = `${messages.length} Einträge`;
        
        if (messages.length === 0) {
            elements.tagBrowserMessagesList.innerHTML = '<p class="muted">Keine Nachrichten mit diesen Tags</p>';
            return;
        }
        
        elements.tagBrowserMessagesList.innerHTML = '';
        messages.forEach(msg => {
            const tags = msg.tags || [];
            const item = document.createElement('div');
            item.className = 'tag-browser-msg-item';
            item.innerHTML = `
                <div class="tag-browser-msg-text">${escapeHtml(msg.text)}</div>
                <div class="tag-browser-msg-tags">
                    ${tags.map(t => `<span class="tag ${tagBrowserSelectedTags.includes(t) ? 'active-filter' : ''}" onclick="event.stopPropagation(); toggleTagBrowserFilter('${escapeHtml(t)}')">${escapeHtml(t)}</span>`).join('')}
                </div>
                <div class="tag-browser-msg-actions">
                    <button class="btn btn-small play-btn" title="Abspielen">▶️</button>
                    <button class="btn btn-small" title="Zum Schnellzugriff">➕</button>
                    <button class="btn btn-small" title="In Textfeld übernehmen">📝</button>
                </div>
            `;
            
            // Action handlers
            item.querySelector('.play-btn').onclick = (e) => {
                e.stopPropagation();
                playCatalogAudio(msg.id, msg.text);
            };
            item.querySelectorAll('.tag-browser-msg-actions .btn')[1].onclick = (e) => {
                e.stopPropagation();
                addToQuickAccess(msg);
                showToast('Zum Schnellzugriff hinzugefügt', 'success');
            };
            item.querySelectorAll('.tag-browser-msg-actions .btn')[2].onclick = (e) => {
                e.stopPropagation();
                elements.textInput.value = msg.text;
                if (elements.charCount) elements.charCount.textContent = `${msg.text.length} Zeichen`;
                showToast('Text übernommen', 'info');
            };
            
            elements.tagBrowserMessagesList.appendChild(item);
        });
    } catch (error) {
        console.error('Failed to load tag browser messages:', error);
        elements.tagBrowserMessagesList.innerHTML = '<p class="muted">Fehler beim Laden</p>';
    }
}

let currentHistoryItem = null;

async function openSaveCatalogModalForHistory(item) {
    currentHistoryItem = item;
    currentText = item.text;
    currentAudioUrl = `${window.API_URL}${item.audio_url}`;
    
    elements.saveTextPreview.textContent = item.text;
    
    // Reset current tags
    currentTags = [];
    renderTagList(currentTags, elements.tagListContainer, 'save');
    
    // Existing tags anzeigen (mit Filter) - await, damit Tags geladen sind
    await loadCatalogTags();
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
                <button class="btn btn-small add-quick-btn" data-id="${msg.id}" title="Zum Schnellzugriff">➕</button>
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
    div.querySelector('.add-quick-btn').onclick = () => addToQuickAccess(msg);
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
    
    // Audio über Backend auf ausgewähltem Gerät abspielen
    try {
        const volume = elements.volumeSlider.value / 100;
        await api('/api/tts/play-audio', {
            method: 'POST',
            body: JSON.stringify({ audio_url: audioUrl, volume: volume })
        });
    } catch (error) {
        console.error('Backend Play Fehler:', error);
        // Fallback: Im Browser abspielen
        elements.audioPlayer.src = `${window.API_URL}${audioUrl}`;
        elements.audioPlayer.play();
    }
    
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

async function loadAudioDevices() {
    try {
        const data = await api('/api/audio-devices');
        const select = elements.audioDeviceSelect;
        const micSelect = elements.micDeviceSelect;
        
        // Leere die Liste und füge Standard hinzu
        select.innerHTML = '<option value="-1">Standard</option>';
        micSelect.innerHTML = '<option value="-1">Nicht konfiguriert</option>';
        
        // Füge alle Geräte hinzu
        data.devices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.index;
            option.textContent = device.name;
            select.appendChild(option);
            
            // Auch zum Mikrofon-Select hinzufügen
            const micOption = document.createElement('option');
            micOption.value = device.index;
            micOption.textContent = device.name;
            micSelect.appendChild(micOption);
        });
        
        // Wähle aktuelles Gerät aus
        if (data.current !== null && data.current !== undefined) {
            select.value = data.current;
        } else {
            select.value = '-1';
        }
        
        // Mikrofon-Gerät laden
        try {
            const micData = await api('/api/mic-device');
            if (micData.device !== null && micData.device !== undefined) {
                micSelect.value = micData.device;
            } else {
                micSelect.value = '-1';
            }
            // Toggle-Button Status aktualisieren
            updateMicToggleUI(micData.enabled, micData.device);
        } catch (e) {
            console.log('Mikrofon-Gerät konnte nicht geladen werden');
        }
    } catch (error) {
        console.error('Failed to load audio devices:', error);
    }
}

async function setAudioDevice(deviceIndex) {
    try {
        await api('/api/audio-device', {
            method: 'PUT',
            body: JSON.stringify({ index: parseInt(deviceIndex) })
        });
    } catch (error) {
        console.error('Failed to set audio device:', error);
    }
}

async function loadSettings() {
    try {
        const settings = await api('/api/settings');
        
        elements.speedSlider.value = settings.speed || 1.0;
        elements.speedValue.textContent = `${settings.speed || 1.0}x`;
        
        elements.temperatureSlider.value = settings.temperature || 0.3;
        elements.temperatureValue.textContent = settings.temperature || 0.3;
        
        elements.repetitionSlider.value = settings.repetition_penalty || 5.0;
        elements.repetitionValue.textContent = settings.repetition_penalty || 5.0;
        
        // API Key und Modell aus localStorage laden
        const savedApiKey = localStorage.getItem('claudeApiKey') || '';
        elements.apiKeyInput.value = savedApiKey;
        const savedModel = localStorage.getItem('claudeModel') || 'claude-haiku-4-5-20251001';
        elements.aiModelSelect.value = savedModel;
        
        // ElevenLabs Provider & Settings laden
        const provider = settings.tts_provider || 'coqui';
        elements.ttsProviderSelect.value = provider;
        updateProviderUI(provider);
        
        if (settings.elevenlabs_model_id) {
            elements.elevenlabsModelSelect.value = settings.elevenlabs_model_id;
        }
        // ElevenLabs Voice Settings laden
        const stability = settings.elevenlabs_stability ?? 0.5;
        const similarity = settings.elevenlabs_similarity_boost ?? 0.75;
        const style = settings.elevenlabs_style ?? 0.0;
        const speakerBoost = settings.elevenlabs_use_speaker_boost ?? false;
        elements.elevenStabilitySlider.value = stability;
        elements.elevenStabilityValue.textContent = stability.toFixed(2);
        elements.elevenSimilaritySlider.value = similarity;
        elements.elevenSimilarityValue.textContent = similarity.toFixed(2);
        elements.elevenStyleSlider.value = style;
        elements.elevenStyleValue.textContent = style.toFixed(2);
        elements.elevenSpeakerBoostCheckbox.checked = speakerBoost;
        // API Key aus localStorage laden
        const savedElevenKey = localStorage.getItem('elevenlabsApiKey') || '';
        elements.elevenlabsApiKeyInput.value = savedElevenKey;

        // ElevenLabs Stimmen automatisch laden wenn konfiguriert
        if (savedElevenKey || settings.elevenlabs_configured) {
            await loadElevenLabsVoices();
        } else if (settings.elevenlabs_voice_id) {
            // Fallback: Temporäre Option setzen wenn kein API Key vorhanden
            const opt = document.createElement('option');
            opt.value = settings.elevenlabs_voice_id;
            opt.textContent = settings.elevenlabs_voice_id;
            opt.selected = true;
            elements.elevenlabsVoiceSelect.appendChild(opt);
        }
        
        // Audio-Geräte laden
        await loadAudioDevices();
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

async function saveSettings() {
    try {
        // Einstellungen speichern
        await api('/api/settings', {
            method: 'PUT',
            body: JSON.stringify({
                speed: parseFloat(elements.speedSlider.value),
                temperature: parseFloat(elements.temperatureSlider.value),
                repetition_penalty: parseFloat(elements.repetitionSlider.value)
            })
        });
        
        // Audio-Gerät speichern
        await setAudioDevice(elements.audioDeviceSelect.value);
        
        // Mikrofon-Gerät speichern
        const micIndex = parseInt(elements.micDeviceSelect.value);
        await api('/api/mic-device', {
            method: 'PUT',
            body: JSON.stringify({ index: micIndex })
        });
        updateMicToggleUI(undefined, micIndex !== -1 ? micIndex : null);
        
        // API Key und Modell lokal speichern (nicht an Server senden)
        const apiKey = elements.apiKeyInput.value.trim();
        if (apiKey) {
            localStorage.setItem('claudeApiKey', apiKey);
        } else {
            localStorage.removeItem('claudeApiKey');
        }
        localStorage.setItem('claudeModel', elements.aiModelSelect.value);
        
        // ElevenLabs Konfiguration speichern
        const elevenApiKey = elements.elevenlabsApiKeyInput.value.trim();
        if (elevenApiKey) {
            localStorage.setItem('elevenlabsApiKey', elevenApiKey);
        } else {
            localStorage.removeItem('elevenlabsApiKey');
        }
        
        // ElevenLabs Config an Backend senden
        await api('/api/elevenlabs/config', {
            method: 'POST',
            body: JSON.stringify({
                api_key: elevenApiKey || null,
                voice_id: elements.elevenlabsVoiceSelect.value || null,
                model_id: elements.elevenlabsModelSelect.value,
                stability: parseFloat(elements.elevenStabilitySlider.value),
                similarity_boost: parseFloat(elements.elevenSimilaritySlider.value),
                style: parseFloat(elements.elevenStyleSlider.value),
                use_speaker_boost: elements.elevenSpeakerBoostCheckbox.checked
            })
        });
        
        // Provider wechseln
        const provider = elements.ttsProviderSelect.value;
        await api('/api/tts/provider/switch', {
            method: 'POST',
            body: JSON.stringify({ provider: provider })
        });
        
        closeSettingsModal();
        showToast('Einstellungen gespeichert', 'success');
    } catch (error) {
        alert(`Fehler: ${error.message}`);
    }
}

// === ElevenLabs Functions ===

function updateProviderUI(provider) {
    if (provider === 'elevenlabs') {
        elements.elevenlabsSettings.classList.remove('hidden');
        elements.coquiSettings.classList.add('hidden');
    } else {
        elements.elevenlabsSettings.classList.add('hidden');
        elements.coquiSettings.classList.remove('hidden');
    }
}

async function loadElevenLabsVoices() {
    try {
        // Erst API Key ans Backend senden, falls noch nicht gespeichert
        const apiKey = elements.elevenlabsApiKeyInput.value.trim();
        if (apiKey) {
            await api('/api/elevenlabs/config', {
                method: 'POST',
                body: JSON.stringify({ api_key: apiKey })
            });
        }
        
        const result = await api('/api/elevenlabs/voices');
        const currentVoiceId = result.current_voice_id;
        
        elements.elevenlabsVoiceSelect.innerHTML = '<option value="">Stimme wählen...</option>';
        for (const voice of result.voices) {
            const option = document.createElement('option');
            option.value = voice.voice_id;
            option.textContent = `${voice.name} (${voice.category})`;
            if (voice.voice_id === currentVoiceId) {
                option.selected = true;
            }
            elements.elevenlabsVoiceSelect.appendChild(option);
        }
        
        if (result.voices.length > 0) {
            showToast(`${result.voices.length} Stimmen geladen`, 'success');
        } else {
            showToast('Keine Stimmen gefunden. API Key korrekt?', 'error');
        }
    } catch (error) {
        console.error('Failed to load ElevenLabs voices:', error);
        showToast('Fehler beim Laden der Stimmen', 'error');
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

async function openSaveCatalogModal() {
    if (!currentText || !currentAudioUrl) {
        alert('Keine Audio zum Speichern vorhanden.');
        return;
    }
    
    elements.saveTextPreview.textContent = currentText;
    
    // Reset current tags
    currentTags = [];
    elements.tagInputField.value = '';
    renderTagList(currentTags, elements.tagListContainer, 'save');
    
    // Load existing tags (mit Filter) - await, damit Tags geladen sind
    await loadCatalogTags();
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

// === Fenstertitel mit Sprache ===

const langFlags = { de: '🇩🇪 DE', en: '🇬🇧 EN', es: '🇪🇸 ES', fr: '🇫🇷 FR' };

function updateTitle() {
    const lang = elements.languageSelect?.value || 'de';
    const flag = langFlags[lang] || lang.toUpperCase();
    document.title = `SpeakAlike – ${flag}`;
}

// === Mini-Modus ===

let currentMiniPosition = 'top';

async function toggleMiniMode() {
    try {
        const isMiniMode = await window.electronAPI.toggleMiniMode();
        
        if (isMiniMode) {
            document.body.classList.add('mini-mode');
            updateMiniPositionUI(currentMiniPosition);
        } else {
            document.body.classList.remove('mini-mode', 'mini-top', 'mini-bottom');
        }
    } catch (error) {
        console.error('Fehler beim Mini-Modus Toggle:', error);
    }
}

async function toggleMiniPosition() {
    try {
        const position = await window.electronAPI.toggleMiniPosition();
        currentMiniPosition = position;
        updateMiniPositionUI(position);
    } catch (error) {
        console.error('Fehler beim Positions-Toggle:', error);
    }
}

function updateMiniPositionUI(position) {
    document.body.classList.remove('mini-top', 'mini-bottom');
    document.body.classList.add(`mini-${position}`);
    
    if (elements.miniPositionBtn) {
        elements.miniPositionBtn.textContent = position === 'top' ? '⬇️' : '⬆️';
        elements.miniPositionBtn.title = position === 'top' ? 'Nach unten verschieben' : 'Nach oben verschieben';
    }
}

// Letzte Nachricht wiederholen
async function repeatLastMessage() {
    if (!currentAudioUrl) {
        showToast('Keine letzte Nachricht vorhanden.', 'info');
        return;
    }
    
    elements.miniRepeatBtn.disabled = true;
    
    try {
        // Audio-URL extrahieren (relativer Pfad für Backend)
        const audioPath = currentAudioUrl.replace(window.API_URL, '');
        
        // Audio über Backend auf ausgewähltem Gerät abspielen
        try {
            const volume = elements.volumeSlider.value / 100;
            await api('/api/tts/play-audio', {
                method: 'POST',
                body: JSON.stringify({
                    audio_url: audioPath,
                    volume: volume
                })
            });
        } catch (playError) {
            console.error('Backend Play Fehler:', playError);
            // Fallback: Im Browser abspielen
            elements.audioPlayer.src = currentAudioUrl;
            await elements.audioPlayer.play();
        }
    } catch (error) {
        showToast(`Fehler beim Wiederholen: ${error.message}`, 'error');
    } finally {
        elements.miniRepeatBtn.disabled = false;
    }
}

// === Tipp-Geräusch (HTML5 Audio) ===
let typingSoundInterval = null;
let typingSoundTimeout = null;
let typingSoundReady = false;
let typingSoundPool = []; // Pool von Audio-Elementen
const TYPING_SOUND_INTERVAL_MS = 85;
const TYPING_STOP_DELAY_MS = 800;
const TYPING_POOL_SIZE = 4;

// Sound beim App-Start vorladen
function preloadTypingSound() {
    if (typingSoundReady) return;
    try {
        const url = `${window.API_URL}/api/typing-sound`;
        console.log('[Typing] Lade Sound via:', url);
        for (let i = 0; i < TYPING_POOL_SIZE; i++) {
            const audio = new Audio(url);
            audio.volume = 0.3;
            audio.preload = 'auto';
            typingSoundPool.push(audio);
        }
        // Warte bis mindestens eines geladen ist
        typingSoundPool[0].addEventListener('canplaythrough', () => {
            typingSoundReady = true;
            console.log('[Typing] Sound bereit, Dauer:', typingSoundPool[0].duration.toFixed(2) + 's');
        }, { once: true });
        typingSoundPool[0].addEventListener('error', (e) => {
            console.error('[Typing] Laden fehlgeschlagen:', e);
        }, { once: true });
    } catch (e) {
        console.error('[Typing] preloadTypingSound Fehler:', e);
    }
}

let typingPoolIndex = 0;
function playTypingClick() {
    if (!typingSoundReady || typingSoundPool.length === 0) return;
    try {
        const audio = typingSoundPool[typingPoolIndex];
        typingPoolIndex = (typingPoolIndex + 1) % typingSoundPool.length;
        
        const duration = audio.duration || 2;
        // Zufälligen Startpunkt wählen
        const clipLen = 0.08;
        const maxStart = Math.max(0, duration - clipLen - 0.1);
        audio.currentTime = Math.random() * maxStart;
        audio.volume = 0.2 + Math.random() * 0.15;
        audio.playbackRate = 0.9 + Math.random() * 0.2;
        
        const playPromise = audio.play();
        if (playPromise) {
            playPromise.catch(() => {});
        }
        // Nach kurzem Clip stoppen
        setTimeout(() => {
            audio.pause();
        }, clipLen * 1000);
    } catch (e) {
        // Ignorieren
    }
}

function startTypingSound() {
    if (typingSoundInterval) return; // Läuft bereits
    
    // Sicherstellen dass Sound geladen ist
    if (!typingSoundReady) {
        preloadTypingSound();
    }
    
    typingSoundInterval = setInterval(playTypingClick, TYPING_SOUND_INTERVAL_MS);
    
    // Auch über Mic-Device abspielen wenn aktiv
    if (micOutputEnabled) {
        api('/api/mic-device/typing/start', { method: 'POST' }).catch(() => {});
    }
}

function stopTypingSound() {
    if (typingSoundInterval) {
        clearInterval(typingSoundInterval);
        typingSoundInterval = null;
    }
    
    // Mic-Device Typing stoppen
    api('/api/mic-device/typing/stop', { method: 'POST' }).catch(() => {});
}

function onTypingActivity() {
    // Timeout zurücksetzen
    if (typingSoundTimeout) {
        clearTimeout(typingSoundTimeout);
    }
    // Sound starten falls noch nicht läuft
    startTypingSound();
    // Sound stoppen nach Pause
    typingSoundTimeout = setTimeout(() => {
        stopTypingSound();
        typingSoundTimeout = null;
    }, TYPING_STOP_DELAY_MS);
}

// === Mikrofon-Ausgabe (für Telefonie) ===
let micOutputEnabled = false;

function updateMicToggleUI(enabled, device) {
    if (enabled !== undefined) {
        micOutputEnabled = enabled;
    }
    
    const btn = elements.micToggleBtn;
    if (!btn) return;
    
    const hasDevice = device !== null && device !== undefined && device !== -1;
    
    if (micOutputEnabled && hasDevice) {
        btn.classList.add('mic-active');
        btn.title = 'Mikrofon-Ausgabe aktiv (Klick zum Deaktivieren)';
        btn.innerHTML = '🎙️';
    } else if (hasDevice) {
        btn.classList.remove('mic-active');
        btn.title = 'Mikrofon-Ausgabe aktivieren (für Telefonie)';
        btn.innerHTML = '🎤';
    } else {
        btn.classList.remove('mic-active');
        btn.title = 'Kein Mikrofon-Gerät konfiguriert (in Einstellungen setzen)';
        btn.innerHTML = '🎤';
        btn.style.opacity = '0.4';
        return;
    }
    btn.style.opacity = '1';
}

async function toggleMicOutput() {
    try {
        // Prüfe ob ein Mic-Device konfiguriert ist
        const micData = await api('/api/mic-device');
        if (micData.device === null || micData.device === undefined) {
            showToast('Bitte zuerst ein Mikrofon-Gerät in den Einstellungen konfigurieren (z.B. VB-Cable)', 'error');
            openSettingsModal();
            return;
        }
        
        const result = await api('/api/mic-device/toggle', {
            method: 'PUT',
            body: JSON.stringify({})
        });
        
        updateMicToggleUI(result.enabled, result.device);
        
        if (result.enabled) {
            showToast('🎙️ Mikrofon-Ausgabe aktiviert – Sprache wird auch über das virtuelle Mikrofon ausgegeben', 'success');
        } else {
            showToast('🎤 Mikrofon-Ausgabe deaktiviert', 'info');
        }
    } catch (error) {
        console.error('Mikrofon-Toggle Fehler:', error);
        showToast('Fehler beim Umschalten der Mikrofon-Ausgabe', 'error');
    }
}

// Echo-Test für Mikrofon-Ausgabe
async function micEchoTest() {
    const btn = document.getElementById('micEchoTestBtn');
    if (!btn) return;
    
    const micIndex = parseInt(elements.micDeviceSelect.value);
    if (micIndex === -1) {
        showToast('Bitte zuerst ein Mikrofon-Gerät auswählen', 'error');
        return;
    }
    
    // Erst Mic-Device setzen (falls noch nicht gespeichert)
    await api('/api/mic-device', {
        method: 'PUT',
        body: JSON.stringify({ index: micIndex })
    });
    
    btn.disabled = true;
    btn.textContent = '⏳ Test...';
    showToast('🔊 Testton wird auf Mic-Gerät abgespielt...', 'info');
    
    try {
        const result = await api('/api/mic-device/echo-test', {
            method: 'POST'
        });
        showToast('✅ Testton abgespielt – wenn du ihn in der Telefon-App hörst, funktioniert die Verbindung!', 'success');
    } catch (error) {
        console.error('Echo-Test Fehler:', error);
        showToast('❌ Testton fehlgeschlagen: ' + (error.message || error), 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔊 Test';
    }
}

// Signalton abspielen (Aufmerksamkeit erregen)
function playSignalTone() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Zwei-Ton Signal (Ding-Dong)
        const playTone = (frequency, startTime, duration) => {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = frequency;
            oscillator.type = 'sine';
            
            // Sanfter Ein- und Ausklang
            gainNode.gain.setValueAtTime(0, startTime);
            gainNode.gain.linearRampToValueAtTime(0.5, startTime + 0.05);
            gainNode.gain.linearRampToValueAtTime(0, startTime + duration);
            
            oscillator.start(startTime);
            oscillator.stop(startTime + duration);
        };
        
        const now = audioContext.currentTime;
        playTone(880, now, 0.15);        // Erster Ton (A5)
        playTone(1100, now + 0.15, 0.2); // Zweiter Ton (höher)
        
        // AudioContext nach Abspielen schließen
        setTimeout(() => audioContext.close(), 500);
    } catch (error) {
        console.error('Fehler beim Abspielen des Signaltons:', error);
    }
}

// === Privacy Mode ===
function togglePrivacyMode() {
    privacyMode = !privacyMode;
    const wrapper = elements.textInput.closest('.text-input-wrapper');
    if (privacyMode) {
        wrapper.classList.add('privacy-active');
        updatePrivacyOverlay();
        showToast('🔒 Privacy-Modus aktiviert', 'info');
    } else {
        wrapper.classList.remove('privacy-active');
        elements.privacyLastWord.textContent = '';
        elements.privacyLastWord.classList.remove('has-word');
        showToast('🔓 Privacy-Modus deaktiviert', 'info');
    }
}

function updatePrivacyOverlay() {
    if (!privacyMode) return;
    const text = elements.textInput.value;
    if (!text || !text.trim()) {
        elements.privacyLastWord.textContent = '';
        elements.privacyLastWord.classList.remove('has-word');
        return;
    }
    const words = text.trimEnd().split(/\s+/);
    const lastWord = words[words.length - 1] || '';
    elements.privacyLastWord.textContent = lastWord;
    elements.privacyLastWord.classList.toggle('has-word', !!lastWord);
}

// === Event Listeners ===

// Tastatur API URL
const KEYBOARD_API_URL = 'http://127.0.0.1:3847';

async function startKeyboard() {
    try {
        console.log('Starte Tastatur...');
        
        // Tastatur starten
        await fetch(`${KEYBOARD_API_URL}/start`, { 
            method: 'POST',
            mode: 'no-cors'
        });
        
        // Large Keys Modus aktivieren
        await fetch(`${KEYBOARD_API_URL}/largekeys`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: true }),
            mode: 'no-cors'
        });
        
        // Dock-Position entgegengesetzt zur eigenen Position setzen
        // Wenn wir oben sind, Tastatur unten öffnen und umgekehrt
        const keyboardDockPosition = currentMiniPosition === 'top' ? 'bottom' : 'top';
        await fetch(`${KEYBOARD_API_URL}/dock`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ position: keyboardDockPosition }),
            mode: 'no-cors'
        });
        
        console.log(`Tastatur gestartet (Large Mode, Position: ${keyboardDockPosition})`);
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
        // Tipp-Geräusch abspielen
        onTypingActivity();
    });
    
    // Tastatur starten bei Fokus
    elements.textInput.addEventListener('focus', () => {
        startKeyboard();
    });
    
    // Tastatur stoppen bei Fokusverlust
    elements.textInput.addEventListener('blur', () => {
        stopKeyboard();
        stopTypingSound(); // Tipp-Geräusch sofort stoppen
    });
    
    // Enter key to speak, Ctrl+Enter for AI completion
    elements.textInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            // Ctrl+Enter = KI-Vervollständigung (unabhängig von Checkbox)
            e.preventDefault();
            const text = elements.textInput.value.trim();
            if (!text) return;
            elements.statusText.textContent = 'KI vervollständigt...';
            const completed = await completeWithAI(text);
            if (completed) {
                elements.textInput.value = completed;
                if (elements.charCount) {
                    elements.charCount.textContent = `${completed.length} Zeichen`;
                }
                elements.statusText.textContent = 'KI-Text übernommen – Enter zum Sprechen';
                elements.textInput.focus();
            }
        } else if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const text = elements.textInput.value.trim();
            if (text) {
                speak();
            } else if (currentAudioUrl) {
                // Leeres Textfeld + Enter = letzte Nachricht wiederholen
                repeatLastMessage();
            }
        } else if (e.key === 'l' && e.ctrlKey) {
            // Strg+L = Sprache umschalten
            e.preventDefault();
            const sel = elements.languageSelect;
            const idx = sel.selectedIndex;
            sel.selectedIndex = (idx + 1) % sel.options.length;
            sel.dispatchEvent(new Event('change'));
            showToast(`Sprache: ${sel.options[sel.selectedIndex].text}`, 'info');
            updateTitle();
        } else if (e.key === 'd' && e.ctrlKey) {
            // Strg+D = Signalton
            e.preventDefault();
            playSignalTone();
        } else if (e.key === 'p' && e.ctrlKey) {
            // Strg+P = Privacy-Modus
            e.preventDefault();
            togglePrivacyMode();
        }
    });

    // Privacy overlay bei Texteingabe aktualisieren
    elements.textInput.addEventListener('input', updatePrivacyOverlay);
    
    // Context input - live save to localStorage
    elements.aiContextInput.value = localStorage.getItem('aiContext') || '';
    elements.aiContextInput.addEventListener('input', () => {
        const ctx = elements.aiContextInput.value.trim();
        if (ctx) {
            localStorage.setItem('aiContext', ctx);
        } else {
            localStorage.removeItem('aiContext');
        }
    });
    document.getElementById('clearContextBtn').addEventListener('click', () => {
        elements.aiContextInput.value = '';
        localStorage.removeItem('aiContext');
    });
    
    // TTS Model select
    if (elements.ttsModelSelect) {
        elements.ttsModelSelect.addEventListener('change', (e) => {
            switchTTSModel(e.target.value);
        });
    }
    
    // TTS Provider select
    if (elements.ttsProviderSelect) {
        elements.ttsProviderSelect.addEventListener('change', (e) => {
            updateProviderUI(e.target.value);
        });
    }
    
    // ElevenLabs Voices refresh
    if (elements.refreshElevenVoicesBtn) {
        elements.refreshElevenVoicesBtn.addEventListener('click', loadElevenLabsVoices);
    }
    
    // ElevenLabs Slider-Werte anzeigen
    elements.elevenStabilitySlider.addEventListener('input', (e) => {
        elements.elevenStabilityValue.textContent = parseFloat(e.target.value).toFixed(2);
    });
    elements.elevenSimilaritySlider.addEventListener('input', (e) => {
        elements.elevenSimilarityValue.textContent = parseFloat(e.target.value).toFixed(2);
    });
    elements.elevenStyleSlider.addEventListener('input', (e) => {
        elements.elevenStyleValue.textContent = parseFloat(e.target.value).toFixed(2);
    });
    
    // Voice select
    elements.voiceSelect.addEventListener('change', (e) => {
        loadVoiceModel(e.target.value);
    });
    
    // Language select - aktualisiert Katalog-Vorschau und Favoriten
    elements.languageSelect.addEventListener('change', () => {
        loadCatalogPreview();
        loadFavorites();
        updateTitle();
    });
    
    // TTS buttons
    elements.speakBtn.addEventListener('click', speak);
    elements.generateBtn.addEventListener('click', generateOnly);
    
    // Volume control
    let previousVolume = 100;
    elements.volumeSlider.addEventListener('input', (e) => {
        const volume = e.target.value / 100;
        elements.audioPlayer.volume = volume;
        elements.volumeValue.textContent = `${e.target.value}%`;
        updateVolumeIcon(e.target.value);
    });
    
    elements.volumeIcon.addEventListener('click', () => {
        if (elements.audioPlayer.volume > 0) {
            previousVolume = elements.volumeSlider.value;
            elements.volumeSlider.value = 0;
            elements.audioPlayer.volume = 0;
            elements.volumeValue.textContent = '0%';
            updateVolumeIcon(0);
        } else {
            elements.volumeSlider.value = previousVolume;
            elements.audioPlayer.volume = previousVolume / 100;
            elements.volumeValue.textContent = `${previousVolume}%`;
            updateVolumeIcon(previousVolume);
        }
    });
    
    function updateVolumeIcon(value) {
        if (value == 0) {
            elements.volumeIcon.textContent = '🔇';
        } else if (value < 50) {
            elements.volumeIcon.textContent = '🔉';
        } else {
            elements.volumeIcon.textContent = '🔊';
        }
    }
    
    // Settings
    elements.settingsBtn.addEventListener('click', openSettingsModal);
    elements.closeSettingsBtn.addEventListener('click', closeSettingsModal);
    elements.saveSettingsBtn.addEventListener('click', saveSettings);
    elements.refreshDevicesBtn.addEventListener('click', loadAudioDevices);
    
    // Echo-Test Button
    const echoTestBtn = document.getElementById('micEchoTestBtn');
    if (echoTestBtn) {
        echoTestBtn.addEventListener('click', micEchoTest);
    }
    
    // Mikrofon-Ausgabe Toggle
    if (elements.micToggleBtn) {
        elements.micToggleBtn.addEventListener('click', toggleMicOutput);
    }
    
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
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.tag-filter-container')) {
            toggleTagDropdown(elements.catalogTagDropdown, false);
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
    
    // Quick Access
    if (elements.clearQuickAccessBtn) {
        elements.clearQuickAccessBtn.addEventListener('click', clearQuickAccess);
    }
    
    // Global Search
    if (elements.globalSearchInput) {
        elements.globalSearchInput.addEventListener('input', debounce(handleGlobalSearch, 300));
        elements.globalSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                clearGlobalSearch();
            }
        });
    }
    if (elements.searchModeOr) {
        elements.searchModeOr.addEventListener('click', () => setGlobalSearchMode('or'));
    }
    if (elements.searchModeAnd) {
        elements.searchModeAnd.addEventListener('click', () => setGlobalSearchMode('and'));
    }
    if (elements.clearSearchBtn) {
        elements.clearSearchBtn.addEventListener('click', clearGlobalSearch);
    }
    
    // View Toggle (Spalten / Tag-Browser)
    if (elements.toggleViewBtn) {
        elements.toggleViewBtn.addEventListener('click', toggleView);
    }
    if (elements.clearTagBrowserFilters) {
        elements.clearTagBrowserFilters.addEventListener('click', clearAllTagBrowserFilters);
    }
    
    // Initial search mode
    updateSearchModeButtons();
    
    // Mini-Modus
    if (elements.miniModeBtn) {
        elements.miniModeBtn.addEventListener('click', toggleMiniMode);
    }
    
    // Texteingabe Position toggle (oben/unten)
    if (elements.toggleInputPositionBtn) {
        elements.toggleInputPositionBtn.addEventListener('click', () => {
            const main = document.querySelector('.main');
            const isBottom = main.classList.toggle('input-bottom');
            elements.toggleInputPositionBtn.textContent = isBottom ? '⬆️' : '⬇️';
            localStorage.setItem('inputPosition', isBottom ? 'bottom' : 'top');
        });
        // Gespeicherte Position wiederherstellen
        if (localStorage.getItem('inputPosition') === 'bottom') {
            document.querySelector('.main').classList.add('input-bottom');
            elements.toggleInputPositionBtn.textContent = '⬆️';
        }
    }
    
    if (elements.miniRepeatBtn) {
        elements.miniRepeatBtn.addEventListener('click', repeatLastMessage);
    }
    if (elements.miniPositionBtn) {
        elements.miniPositionBtn.addEventListener('click', toggleMiniPosition);
    }
    if (elements.miniExitBtn) {
        elements.miniExitBtn.addEventListener('click', toggleMiniMode);
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            // Im Mini-Modus: ESC beendet den Mini-Modus
            if (document.body.classList.contains('mini-mode')) {
                toggleMiniMode();
            } else {
                document.querySelectorAll('.modal.active').forEach(m => m.classList.remove('active'));
            }
        }
        
        if (e.ctrlKey && e.key === 'Enter') {
            // Wird bereits vom textInput keydown-Handler behandelt
            // Nur sprechen wenn Focus NICHT im Textfeld ist
            if (document.activeElement !== elements.textInput) {
                speak();
            }
        }
        
        // Ctrl+M für Mini-Modus Toggle
        if (e.ctrlKey && e.key === 'm') {
            e.preventDefault();
            toggleMiniMode();
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
    updateTitle();
    
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
    
    // Typing-Sound verzögert im Hintergrund vorladen
    setTimeout(() => {
        try { preloadTypingSound(); } catch(e) { console.error('[Typing] Init-Fehler:', e); }
    }, 2000);
    
    if (connected) {
        // Katalog und History können sofort geladen werden
        await loadCatalogTags();
        loadCatalogPreview();
        loadHistory();
        loadFavorites();
        
        // Quick Access aus localStorage laden
        loadQuickAccessFromStorage();
        renderQuickAccess();
        
        // Mikrofon-Ausgabe Status laden
        try {
            const micData = await api('/api/mic-device');
            updateMicToggleUI(micData.enabled, micData.device);
        } catch (e) {
            console.log('Mikrofon-Status konnte nicht geladen werden');
        }
        
        // Gespeicherte Ansicht wiederherstellen
        if (localStorage.getItem('viewMode') === 'tags') {
            toggleView();
        }
        
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
