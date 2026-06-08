/**
 * SpeakAlike Renderer - Frontend Logic
 */

// Theme sofort anwenden (vor Rendering)
document.documentElement.setAttribute('data-theme', localStorage.getItem('theme') || 'dark');

// i18n shorthand (falls i18n.js noch nicht geladen)
function charStr(n) { return `${n} ${window.t ? window.t('chars') : 'Zeichen'}`; }

// i18n sofort anwenden (gespeicherte Sprache aus localStorage)
if (window.i18n) window.i18n.apply();

// API_URL kommt vom preload.js als window.API_URL

// State
let currentAudioUrl = null;
let currentText = null;
let catalogTags = [];
let selectedFiles = [];
let currentTTSModel = 'xtts_v2';
let availableTTSModels = {};
let privacyMode = false;
let privacyShowWord = false; // default: letztes Wort nicht anzeigen
let confirmSend = true; // default: confirmation dialog active
let currentProvider = 'pyttsx3';
let kiAutoCorrect = false;
let signalBeforeSpeak = false;
let _suggestTimer = null;
let _suggestions = [];
let _suggestIndex = -1;

// DOM Elements
const elements = {
    // Status
    status: document.getElementById('status'),
    statusText: document.querySelector('.status-text'),
    
    // TTS Model
    ttsModelSelect: document.getElementById('ttsModelSelect'),
    
    // Voice
    currentVoice: document.getElementById('currentVoice'),
    elevenlabsVoiceQuick: document.getElementById('elevenlabsVoiceQuick'),
    elevenlabsVoiceQuickSelect: document.getElementById('elevenlabsVoiceQuickSelect'),
    
    // Text
    textInput: document.getElementById('textInput'),
    suggestionsDropdown: document.getElementById('suggestionsDropdown'),
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
    privacyShowWordDefault: document.getElementById('privacyShowWordDefault'),
    confirmSendDefault: document.getElementById('confirmSendDefault'),
    
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
    themeSelect: document.getElementById('themeSelect'),
    uiLangSelect: document.getElementById('uiLangSelect'),
    aiContextInput: document.getElementById('aiContextInput'),
    
    // ElevenLabs
    ttsProviderSelect: document.getElementById('ttsProviderSelect'),
    elevenlabsSettings: document.getElementById('elevenlabsSettings'),
    pyttsx3Settings: document.getElementById('pyttsx3Settings'),
    pyttsx3VoiceSelect: document.getElementById('pyttsx3VoiceSelect'),
    pyttsx3GenderSelect: document.getElementById('pyttsx3GenderSelect'),
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
    newQuickAccessSetBtn: document.getElementById('newQuickAccessSetBtn'),
    quickAccessSetBtn: document.getElementById('quickAccessSetBtn'),
    setPickerPopup: document.getElementById('setPickerPopup'),
    setPickerList: document.getElementById('setPickerList'),
    saveQuickAccessSetBtn: document.getElementById('saveQuickAccessSetBtn'),
    setManager: document.getElementById('setManager'),
    
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
        // Translate known backend status messages
        const msg = status.message || '';
        if (msg === 'Bereit' || msg === 'Ready') {
            elements.statusText.textContent = t('status_ready');
        } else if (msg.startsWith('Voice-Modell geladen:') || msg.startsWith('Loading voice model:') || msg.startsWith('Voice model')) {
            elements.statusText.textContent = msg;
        } else {
            elements.statusText.textContent = msg;
        }
        
        // Disable speak button while TTS is loading
        if (status.loading) {
            elements.speakBtn.disabled = true;
            elements.speakBtn.innerHTML = `⏳ <span class="hide-in-mini">${t('tts_loading')}</span>`;
            elements.status.classList.add('loading');
        } else {
            elements.speakBtn.disabled = false;
            elements.speakBtn.innerHTML = `🔊 <span class="hide-in-mini" data-i18n="speak_label">${t('speak_label')}</span>`;
            elements.status.classList.remove('loading');
        }
        
        if (status.voice_loaded && currentProvider === 'elevenlabs') {
            // ElevenLabs voice name handled via quick select
        }
        
        return status;
    } catch (error) {
        elements.status.classList.remove('connected');
        elements.status.classList.add('error');
        elements.statusText.textContent = t('not_connected');
        return null;
    }
}

// === Text-to-Speech ===

// AI Sentence Completion
async function completeWithAI(text) {
    const apiKey = localStorage.getItem('claudeApiKey') || '';
    if (!apiKey) {
        showToast(t('toast_no_api_key'), 'error');
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
                .reverse(); // oldest first
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
    hideSuggestions();
    let text = elements.textInput.value.trim();
    if (!text) {
        showToast('Bitte geben Sie einen Text ein.', 'error');
        return;
    }

    // Reset AI flag
    delete elements.textInput.dataset.aiCompleted;
    
    currentText = text;
    elements.speakBtn.disabled = true;
    elements.statusText.textContent = t('generating_audio');
    
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

            // Vor-Signal: Signalton + 2s Pause nach Generierung, vor Wiedergabe
            if (signalBeforeSpeak) {
                playSignalTone();
                await new Promise(resolve => setTimeout(resolve, 2000));
            }

            // Play audio via backend on selected device
            try {
                const volume = elements.volumeSlider.value / 100;
                await api('/api/tts/play-audio', {
                    method: 'POST',
                    body: JSON.stringify({
                        audio_url: result.audio_url,
                        volume: volume
                    })
                });
                console.log('Audio playing on backend device');
            } catch (playError) {
                console.error('Backend Play Fehler:', playError);
                // Fallback: Im Browser abspielen
                elements.audioPlayer.src = currentAudioUrl;
                await elements.audioPlayer.play();
            }
            
            // Add to playback history
            await addToPlaybackHistory(text, result.audio_url, null);
            
            // History aktualisieren
            loadHistory();
            
            // Textfeld leeren
            elements.textInput.value = '';
            updatePrivacyOverlay();
            if (elements.charCount) {
                elements.charCount.textContent = charStr(0);
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
    elements.generateBtn.textContent = `⏳ ${t('generating_label') || 'Generiere...'}`;
    elements.statusText.textContent = t('generating_bg');
    
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
            
            // Add to playback history
            await addToPlaybackHistory(text, result.audio_url, null);
            
            // History aktualisieren
            loadHistory();
            
            // Textfeld leeren
            elements.textInput.value = '';
            updatePrivacyOverlay();
            if (elements.charCount) {
                elements.charCount.textContent = charStr(0);
            }
            
            showToast('Audio erfolgreich generiert!', 'success');
        }
    } catch (error) {
        showToast(`Fehler: ${error.message}`, 'error');
    } finally {
        elements.generateBtn.disabled = false;
        elements.speakBtn.disabled = false;
        elements.generateBtn.innerHTML = `<span data-i18n="generate_label">${t('generate_label')}</span>`;
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
            elements.catalogGrid.innerHTML = '<p class="muted" style="padding: 20px;">No entries found</p>';
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

// Language-tag mapping (globally available)
const langNames = {
    'de': 'german', 'en': 'english', 'es': 'spanish', 'fr': 'french',
    'it': 'italian', 'pt': 'portuguese', 'pl': 'polish', 'tr': 'turkish',
    'ru': 'russian', 'nl': 'dutch', 'ja': 'japanese', 'zh-cn': 'chinese'
};

// All language tags as set for fast lookup
const allLangTags = new Set(Object.values(langNames));

// Checks whether an entry matches the current language (or has no language tag)
function matchesLanguageFilter(item, currentLangTag) {
    const itemTags = item.tags || [];
    const hasAnyLangTag = itemTags.some(tag => allLangTags.has(tag));
    
    // Zeige an wenn: kein Sprach-Tag vorhanden ODER das aktuelle Sprach-Tag vorhanden
    return !hasAnyLangTag || itemTags.includes(currentLangTag);
}

async function loadCatalogPreview() {
    try {
        // Load entries for preview
        const params = new URLSearchParams();
        params.set('order_by', 'play_count');
        params.set('limit', '100');  // Mehr laden, da wir im Frontend filtern
        
        let messages = await api(`/api/catalog?${params}`);
        
        // Im Frontend nach Sprache filtern
        const currentLang = elements.languageSelect.value;
        const langTag = langNames[currentLang] || currentLang;
        
        console.log(`\n=== Katalog-Vorschau Filter ===`);
        console.log(`Aktuelle Sprache: ${currentLang} → Tag: "${langTag}"`);
        console.log(`Entries from backend: ${messages.length}`);
        
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
        
        console.log(`Displayed entries: ${messages.length}`);
        messages.slice(0, 5).forEach(msg => {
            const tags = msg.tags || [];
            console.log(`  ✓ "${msg.text.substring(0, 30)}..." | Tags: [${tags.join(', ')}]`);
        });
        if (messages.length > 5) console.log(`  ... und ${messages.length - 5} weitere`);
        
        if (messages.length === 0) {
            const noResultsText = globalSearchTerms.length > 0 ? 'No results' : 'No entries in the catalog';
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
                    <button class="btn btn-small add-quick-btn" title="Zum Schnellzugriff">➕</button>
                </div>
            `;
            item.querySelector('.add-quick-btn').onclick = () => addToQuickAccess(msg);
            item.onclick = (e) => { if (!e.target.closest('button')) playCatalogAudio(msg.id, msg.text); };
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
                <div class="history-actions">
                    <button class="btn btn-small add-quick-btn" title="Zum Schnellzugriff">➕</button>
                    <button class="btn btn-small save-btn" title="Speichern">💾</button>
                    ${!item.in_catalog ? '<button class="btn btn-small catalog-btn" title="Zum Katalog">📁</button>' : ''}
                </div>
            `;
            div.onclick = (e) => { if (!e.target.closest('button')) playHistoryAudio(item.audio_url, item.text, item.catalog_id); };
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
    // Play audio via backend on selected device
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
    
    // Add to playback history
    await addToPlaybackHistory(text, audioUrl, catalogId);
    loadHistory();
}

async function saveHistoryAudio(audioUrl, text) {
    try {
        // Audio herunterladen und speichern
        const response = await fetch(`${window.API_URL}${audioUrl}`);
        const blob = await response.blob();
        
        // Create filename from text (first 30 characters)
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
            const noResultsText = globalSearchTerms.length > 0 ? 'No results' : 'No favourites for this Sprache';
            elements.favoritesList.innerHTML = `<p class="muted">${noResultsText}</p>`;
            return;
        }
        
        elements.favoritesList.innerHTML = '';
        favorites.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            
            div.innerHTML = `
                <span class="history-text">${escapeHtml(item.text.substring(0, 40))}${item.text.length > 40 ? '...' : ''}</span>
                <div class="history-actions">
                    <button class="btn btn-small add-quick-btn" title="Zum Schnellzugriff">➕</button>
                    <button class="btn btn-small unfav-btn" title="Entfernen">⭐</button>
                </div>
            `;
            div.querySelector('.add-quick-btn').onclick = () => addToQuickAccess(item);
            div.querySelector('.unfav-btn').onclick = () => toggleFavorite(item.id, false);
            div.onclick = (e) => { if (!e.target.closest('button')) playCatalogItem(item); };
            elements.favoritesList.appendChild(div);
        });
    } catch (error) {
        console.error('Failed to load favorites:', error);
    }
}

async function playCatalogItem(item) {
    if (item.audio_url) {
        // Play audio via backend on selected device
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
        
        // Increment play count
        await api(`/api/catalog/${item.id}/play`, { method: 'POST' });
        loadFavorites();
        loadCatalogPreview();
    }
}

// === Quick Access ===

// Schnellzugriff-Liste wird im localStorage gespeichert
let quickAccessItems = [];
let miniSetPickerMode = false;

function loadQuickAccessFromStorage() {
    try {
        const stored = localStorage.getItem('quickAccessItems');
        if (stored) {
            // Discard temporary items on load
            quickAccessItems = JSON.parse(stored).filter(q => !q._temporary);
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
    // Check if already present
    const exists = quickAccessItems.some(q => q.id === item.id);
    if (exists) {
        showToast(t('toast_already_in_qa'), 'info');
        return;
    }
    
    // Add at end (incl. tags for search filter)
    quickAccessItems.push({
        id: item.id,
        text: item.text,
        audio_url: item.audio_url,
        is_favorite: item.is_favorite,
        tags: item.tags || [],
        _temporary: item._temporary || false
    });
    
    // Max 20 Items
    if (quickAccessItems.length > 26) {
        quickAccessItems = quickAccessItems.slice(0, 26);
    }
    
    saveQuickAccessToStorage();
    renderQuickAccess();
    showToast('Added to quick access', 'success');
}

function removeFromQuickAccess(itemId) {
    quickAccessItems = quickAccessItems.filter(q => q.id !== itemId);
    saveQuickAccessToStorage();
    renderQuickAccess();
}

let clearQuickAccessPending = false;

function clearQuickAccess() {
    if (quickAccessItems.length === 0) return;
    
    // Double-click to confirm
    if (!clearQuickAccessPending) {
        clearQuickAccessPending = true;
        showToast('Click again to confirm', 'info');
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

// === Quick Access Sets ===

function getQuickAccessSets() {
    try {
        const stored = localStorage.getItem('quickAccessSets');
        return stored ? JSON.parse(stored) : {};
    } catch (e) {
        return {};
    }
}

function saveQuickAccessSets(sets) {
    localStorage.setItem('quickAccessSets', JSON.stringify(sets));
}

let currentQuickAccessSetName = null;

function renderQuickAccessSetSelect() {
    updateSetBtn();
}

function updateSetBtn() {
    if (!elements.quickAccessSetBtn) return;
    elements.quickAccessSetBtn.textContent = currentQuickAccessSetName ? `📂 ${currentQuickAccessSetName}` : '📂 Sets';
}

function openSetPickerPopup() {
    const popup = elements.setPickerPopup;
    const list = elements.setPickerList;
    if (!popup || !list) return;
    const sets = getQuickAccessSets();
    const names = Object.keys(sets).sort();
    list.innerHTML = '';
    if (names.length === 0) {
        list.innerHTML = '<p class="muted" style="font-size:0.875rem;padding:4px 8px;">Keine Sets vorhanden</p>';
    } else {
        names.forEach(name => {
            const btn = document.createElement('button');
            btn.className = 'set-picker-btn' + (name === currentQuickAccessSetName ? ' active' : '');
            btn.textContent = `${name} (${sets[name].length})`;
            btn.onclick = () => { loadQuickAccessSet(name); closeSetPickerPopup(); };
            list.appendChild(btn);
        });
    }
    // Position unterhalb des Buttons
    const rect = elements.quickAccessSetBtn.getBoundingClientRect();
    popup.style.top = (rect.bottom + 4) + 'px';
    popup.style.right = (window.innerWidth - rect.right) + 'px';
    popup.style.display = 'flex';
}

function closeSetPickerPopup() {
    if (elements.setPickerPopup) elements.setPickerPopup.style.display = 'none';
}

function saveQuickAccessSet() {
    if (quickAccessItems.length === 0) {
        showToast(t('toast_qa_empty'), 'info');
        return;
    }
    const selected = currentQuickAccessSetName;
    
    if (selected && selected !== '__new__') {
        // Overwrite existing set
        const sets = getQuickAccessSets();
        sets[selected] = JSON.parse(JSON.stringify(quickAccessItems));
        saveQuickAccessSets(sets);
        showToast(`Set "${selected}" aktualisiert`, 'success');
        return;
    }
    
    // Neues Set: Inline-Input im Header
    const header = document.querySelector('.quick-access-header-actions');
    if (header.querySelector('.set-name-input')) return;
    
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'set-name-input';
    input.placeholder = 'Set-Name...';
    input.style.cssText = 'font-size:0.75rem;padding:2px 6px;height:28px;width:100px;border:1px solid var(--color-primary);border-radius:4px;background:var(--color-bg);color:var(--color-text);';
    header.prepend(input);
    input.focus();
    
    const doSave = () => {
        const name = input.value.trim();
        input.remove();
        if (!name) return;
        const sets = getQuickAccessSets();
        sets[name] = JSON.parse(JSON.stringify(quickAccessItems));
        saveQuickAccessSets(sets);
        currentQuickAccessSetName = name;
        renderQuickAccessSetSelect();
        showToast(`Set "${name}" gespeichert`, 'success');
    };
    
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); doSave(); }
        if (e.key === 'Escape') input.remove();
    });
    input.addEventListener('blur', doSave);
}

function loadQuickAccessSet(name) {
    if (!name || name === '__new__') return;
    const sets = getQuickAccessSets();
    if (!sets[name]) return;
    quickAccessItems = JSON.parse(JSON.stringify(sets[name]));
    currentQuickAccessSetName = name;
    updateSetBtn();
    saveQuickAccessToStorage();
    renderQuickAccess();
    showToast(`Set "${name}" geladen`, 'success');
}

// Set-Manager in Settings
function renderSetManager() {
    const container = elements.setManager;
    if (!container) return;
    const sets = getQuickAccessSets();
    const names = Object.keys(sets).sort();
    
    if (names.length === 0) {
        container.innerHTML = '<p class="muted" style="font-size:0.8rem;">Keine Sets gespeichert</p>';
        return;
    }
    
    container.innerHTML = '';
    names.forEach(name => {
        const row = document.createElement('div');
        row.style.cssText = 'display:flex;align-items:center;gap:6px;margin-bottom:4px;';
        
        const label = document.createElement('span');
        label.textContent = name;
        label.style.cssText = 'flex:1;font-size:0.85rem;';
        
        const count = document.createElement('span');
        count.textContent = `(${sets[name].length})`;
        count.style.cssText = 'font-size:0.75rem;color:var(--color-text-muted);';
        
        const renameBtn = document.createElement('button');
        renameBtn.className = 'btn btn-small btn-secondary';
        renameBtn.textContent = '✏️';
        renameBtn.title = 'Umbenennen';
        renameBtn.onclick = () => renameQuickAccessSet(name);
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-small btn-danger';
        deleteBtn.textContent = '✕';
        deleteBtn.title = 'Delete';
        deleteBtn.onclick = () => deleteQuickAccessSet(name);
        
        row.appendChild(label);
        row.appendChild(count);
        row.appendChild(renameBtn);
        row.appendChild(deleteBtn);
        container.appendChild(row);
    });
}

function renameQuickAccessSet(oldName) {
    const container = elements.setManager;
    // Finde die Zeile mit dem alten Namen
    const rows = container.children;
    for (const row of rows) {
        if (row.querySelector('span')?.textContent === oldName) {
            const label = row.querySelector('span');
            const input = document.createElement('input');
            input.type = 'text';
            input.value = oldName;
            input.style.cssText = 'flex:1;font-size:0.85rem;padding:2px 6px;border:1px solid var(--color-primary);border-radius:4px;background:var(--color-bg);color:var(--color-text);';
            label.replaceWith(input);
            input.focus();
            input.select();
            
            const doRename = () => {
                const newName = input.value.trim();
                if (!newName || newName === oldName) {
                    renderSetManager();
                    return;
                }
                const sets = getQuickAccessSets();
                if (sets[newName]) {
                    showToast(t('toast_name_exists'), 'info');
                    return;
                }
                sets[newName] = sets[oldName];
                delete sets[oldName];
                saveQuickAccessSets(sets);
                renderQuickAccessSetSelect();
                renderSetManager();
                showToast(`"${oldName}" → "${newName}"`, 'success');
            };
            
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') doRename();
                if (e.key === 'Escape') renderSetManager();
            });
            input.addEventListener('blur', doRename);
            break;
        }
    }
}

function deleteQuickAccessSet(name) {
    const sets = getQuickAccessSets();
    delete sets[name];
    saveQuickAccessSets(sets);
    renderQuickAccessSetSelect();
    renderSetManager();
    showToast(`Set "${name}" deleted`, 'success');
}

function renderQuickAccess() {
    if (!elements.quickAccessList) return;
    
    // Globale Suche anwenden
    const filteredItems = quickAccessItems.filter(item => matchesGlobalSearch(item));
    
    if (filteredItems.length === 0) {
        const emptyText = globalSearchTerms.length > 0 ? 'No results' : 'Add messages here with them ➕ Button';
        elements.quickAccessList.innerHTML = `<p class="muted">${emptyText}</p>`;
        if (window.electronAPI?.updateQuickAccessWindow) {
            window.electronAPI.updateQuickAccessWindow(quickAccessItems.slice(0, QUICK_ACCESS_KEYS.length));
        }
        return;
    }
    
    elements.quickAccessList.innerHTML = '';
    filteredItems.forEach((item, idx) => {
        const div = document.createElement('div');
        div.className = 'quick-access-item';
        
        const textPreview = item.text.substring(0, 50) + (item.text.length > 50 ? '...' : '');
        const badge = idx < QUICK_ACCESS_KEYS.length ? `<span class="quick-shortcut-badge${item._temporary ? ' temporary' : ''}">${QUICK_ACCESS_KEYS[idx]}</span>` : '';
        
        div.innerHTML = `
            ${badge}
            <span class="quick-text" title="${escapeHtml(item.text)}">${escapeHtml(textPreview)}</span>
            <div class="quick-actions">
                <button class="btn btn-secondary btn-small use-btn" title="Use text">📝</button>
                <button class="btn btn-danger btn-small remove-btn" title="Entfernen">✕</button>
            </div>
        `;
        
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

    // Mini-Fenster aktualisieren falls offen
    if (window.electronAPI?.updateQuickAccessWindow) {
        const miniItems = quickAccessItems.slice(0, QUICK_ACCESS_KEYS.length);
        window.electronAPI.updateQuickAccessWindow(miniItems);
    }
}

async function playQuickAccessItem(item) {
    const volume = elements.volumeSlider.value / 100;

    // Hilfsfunktion: Audio neu generieren und abspielen
    async function regenerateAndPlay() {
        showToast('Audio neu generieren...', 'info');
        try {
            const result = await api('/api/tts/speak', {
                method: 'POST',
                body: JSON.stringify({
                    text: item.text,
                    language: elements.languageSelect?.value || 'de'
                })
            });
            if (result.success) {
                // Gespeicherte URL aktualisieren
                const idx = quickAccessItems.findIndex(q => q.id === item.id);
                if (idx !== -1) {
                    quickAccessItems[idx].audio_url = result.audio_url;
                    item.audio_url = result.audio_url;
                    saveQuickAccessToStorage();
                }
                await api('/api/tts/play-audio', {
                    method: 'POST',
                    body: JSON.stringify({ audio_url: result.audio_url, volume: volume })
                });
                // Also remove temporary items after regeneration
                if (item._temporary) {
                    removeFromQuickAccess(item.id);
                }
            }
        } catch (err) {
            console.error('Regenerierung fehlgeschlagen:', err);
            showToast('Fehler beim Abspielen', 'error');
        }
    }

    if (item.audio_url) {
        // Play audio via backend on selected device
        try {
            await api('/api/tts/play-audio', {
                method: 'POST',
                body: JSON.stringify({ audio_url: item.audio_url, volume: volume })
            });
            // Increment play count (nur Katalog-Items)
            try { await api(`/api/catalog/${item.id}/play`, { method: 'POST' }); } catch (_) {}
            // Remove temporary items after playback
            if (item._temporary) {
                removeFromQuickAccess(item.id);
            }
        } catch (error) {
            console.warn('Audio nicht gefunden, generiere neu:', error);
            await regenerateAndPlay();
        }
    } else {
        // Keine audio_url gespeichert → direkt neu generieren
        await regenerateAndPlay();
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
        // AND: all terms must match
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
    
    // Auto-scaling: font size as large as possible without scrolling
    requestAnimationFrame(() => fitTagCloud(tagElements));
}

function fitTagCloud(tagElements) {
    if (!tagElements.length) return;
    const container = elements.tagCloud;
    const containerH = container.clientHeight;
    if (containerH <= 0) return;
    
    // Base font sizes: min and max in px
    const MIN_BASE = 0.7;
    const MAX_BASE = 3.0;
    let lo = MIN_BASE, hi = MAX_BASE;
    
    // Binary search for optimal base size
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
        // Weighted size: small tags = 60% of base, large = 100%
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
    loadTagBrowserMessages(); // loads messages and updates tag cloud
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
    elements.tagBrowserMessagesList.innerHTML = '<p class="muted">Select a tag to display messages</p>';
    elements.tagBrowserCount.textContent = '';
}

async function loadTagBrowserMessages() {
    if (tagBrowserSelectedTags.length === 0) {
        elements.tagBrowserMessagesList.innerHTML = '<p class="muted">Select a tag to display messages</p>';
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
        
        elements.tagBrowserCount.textContent = `${messages.length} entries`;
        
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
                    <button class="btn btn-small" title="Copy to text field">📝</button>
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
                showToast('Added to quick access', 'success');
            };
            item.querySelectorAll('.tag-browser-msg-actions .btn')[2].onclick = (e) => {
                e.stopPropagation();
                elements.textInput.value = msg.text;
                if (elements.charCount) elements.charCount.textContent = `${msg.text.length} ${t('chars')}`;
                showToast('Text copied', 'info');
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
    
    // Play audio via backend on selected device
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
    
    // Add to playback history
    await addToPlaybackHistory(text, audioUrl, id);
    loadHistory();
}

async function deleteCatalogMessage(id) {
    if (!confirm('Really delete this message?')) return;
    
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
        showToast('Added to catalog!', 'success');
        
        loadCatalogTags();
        loadFavorites();
        loadCatalogPreview();
    } catch (error) {
        showToast(`Fehler: ${error.message}`, 'error');
    }
}

async function generateAutoTags() {
    if (!currentText) return;
    
    const apiKey = localStorage.getItem('claudeApiKey') || '';
    if (!apiKey) {
        showToast(t('toast_no_api_key'), 'error');
        return;
    }
    
    elements.autoTagsBtn.disabled = true;
    elements.autoTagsBtn.textContent = '⏳ Generiere...';
    
    try {
        const result = await api('/api/tags/generate', {
            method: 'POST',
            headers: { 'X-API-Key': apiKey },
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
        alert('Please select an audio file (MP3, WAV, OGG, M4A)');
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
    
    const apiKey = localStorage.getItem('claudeApiKey') || '';
    if (!apiKey) {
        showToast(t('toast_no_api_key'), 'error');
        return;
    }
    
    elements.importAutoTagsBtn.disabled = true;
    elements.importAutoTagsBtn.textContent = '⏳';
    
    try {
        const response = await api('/api/tags/generate', {
            method: 'POST',
            headers: { 'X-API-Key': apiKey },
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
        alert('Please select an audio file.');
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

// === Settings ===

async function loadAudioDevices() {
    try {
        const [outputData, micData] = await Promise.all([
            api('/api/audio-devices'),
            api('/api/mic-devices').catch(() => ({ devices: [] }))
        ]);
        const select = elements.audioDeviceSelect;
        const micSelect = elements.micDeviceSelect;
        
        // Clear the list and add default
        select.innerHTML = '<option value="-1">Standard</option>';
        micSelect.innerHTML = '<option value="-1">Nicht konfiguriert</option>';
        
        // Speaker dropdown – output devices only
        outputData.devices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.index;
            option.textContent = device.name;
            select.appendChild(option);
        });
        
        // Mic routing dropdown – all devices from dedicated endpoint
        // Deduplicate by name, preferring output (can actually be played to)
        const seen = new Map();
        micData.devices.forEach(device => {
            const key = device.name;
            if (!seen.has(key) || device.type === 'output') {
                seen.set(key, device);
            }
        });
        seen.forEach(device => {
            const micOption = document.createElement('option');
            micOption.value = device.index;
            const typeLabel = device.type === 'input' ? ' 🎤' : '';
            micOption.textContent = device.name + typeLabel;
            micSelect.appendChild(micOption);
        });
        
        // Select current speaker device
        if (outputData.current !== null && outputData.current !== undefined) {
            select.value = outputData.current;
        } else {
            select.value = '-1';
        }
        
        // Load microphone device
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
            console.log('Microphone device could not be loaded');
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
        
elements.temperatureSlider?.value != null && (elements.temperatureSlider.value = settings.temperature || 0.3);
        if (elements.temperatureValue) elements.temperatureValue.textContent = settings.temperature || 0.3;

        elements.repetitionSlider?.value != null && (elements.repetitionSlider.value = settings.repetition_penalty || 5.0);
        if (elements.repetitionValue) elements.repetitionValue.textContent = settings.repetition_penalty || 5.0;
        
        // API Key und Modell aus localStorage laden
        const savedApiKey = localStorage.getItem('claudeApiKey') || '';
        elements.apiKeyInput.value = savedApiKey;
        const savedModel = localStorage.getItem('claudeModel') || 'claude-haiku-4-5-20251001';
        elements.aiModelSelect.value = savedModel;

        // Theme laden
        const savedTheme = localStorage.getItem('theme') || 'dark';
        elements.themeSelect.value = savedTheme;

        // UI-Sprache laden
        if (elements.uiLangSelect && window.i18n) {
            elements.uiLangSelect.value = window.i18n.currentLang;
        }

        // Privacy: letztes Wort anzeigen laden
        privacyShowWord = localStorage.getItem('privacyShowWordDefault') === 'true';
        if (elements.privacyShowWordDefault) elements.privacyShowWordDefault.checked = privacyShowWord;

        // Load confirmation before playback (default: true)
        const confirmStored = localStorage.getItem('confirmSendDefault');
        confirmSend = confirmStored === null ? true : confirmStored === 'true';
        if (elements.confirmSendDefault) elements.confirmSendDefault.checked = confirmSend;
        if (elements.privacyIndicator) {
            elements.privacyIndicator.classList.toggle('show-word', privacyShowWord);
            elements.privacyIndicator.title = privacyShowWord ? 'Letztes Wort ausblenden' : 'Letztes Wort anzeigen';
        }
        
        // ElevenLabs Provider & Settings laden
        const provider = settings.tts_provider || 'pyttsx3';
        elements.ttsProviderSelect.value = provider;
        updateProviderUI(provider);

        if (provider === 'pyttsx3') {
            await loadPyttsx3Voices(settings.pyttsx3_voice_id || '');
            if (elements.pyttsx3GenderSelect) {
                elements.pyttsx3GenderSelect.value = settings.pyttsx3_gender || '';
            }
        }
        
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
            // Fallback: set temporary option when no API key is present
            const opt = document.createElement('option');
            opt.value = settings.elevenlabs_voice_id;
            opt.textContent = settings.elevenlabs_voice_id;
            opt.selected = true;
            elements.elevenlabsVoiceSelect.appendChild(opt);
        }
        
        // Load audio devices
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
                temperature: elements.temperatureSlider ? parseFloat(elements.temperatureSlider.value) : 0.3,
                repetition_penalty: elements.repetitionSlider ? parseFloat(elements.repetitionSlider.value) : 5.0,
                pyttsx3_voice_id: elements.pyttsx3VoiceSelect?.value || null,
                pyttsx3_gender: elements.pyttsx3GenderSelect?.value || null
            })
        });
        
        // Save audio device
        await setAudioDevice(elements.audioDeviceSelect.value);
        
        // Save microphone device
        const micIndex = parseInt(elements.micDeviceSelect.value);
        await api('/api/mic-device', {
            method: 'PUT',
            body: JSON.stringify({ index: micIndex })
        });
        localStorage.setItem('micDevice', micIndex.toString());
        updateMicToggleUI(undefined, micIndex !== -1 ? micIndex : null);
        
        // API Key und Modell lokal speichern (nicht an Server senden)
        const apiKey = elements.apiKeyInput.value.trim();
        if (apiKey) {
            localStorage.setItem('claudeApiKey', apiKey);
        } else {
            localStorage.removeItem('claudeApiKey');
        }
        localStorage.setItem('claudeModel', elements.aiModelSelect.value);

        // Theme speichern und anwenden
        const theme = elements.themeSelect.value;
        localStorage.setItem('theme', theme);
        document.documentElement.setAttribute('data-theme', theme);

        // UI-Sprache speichern und anwenden
        if (elements.uiLangSelect && window.i18n) {
            window.i18n.setLang(elements.uiLangSelect.value);
        }

        // Privacy-Default speichern
        const showWordDefault = elements.privacyShowWordDefault?.checked || false;
        localStorage.setItem('privacyShowWordDefault', showWordDefault.toString());
        privacyShowWord = showWordDefault;

        // Save confirmation default
        const confirmDefault = elements.confirmSendDefault?.checked || false;
        localStorage.setItem('confirmSendDefault', confirmDefault.toString());
        confirmSend = confirmDefault;
        if (elements.privacyIndicator) {
            elements.privacyIndicator.classList.toggle('show-word', privacyShowWord);
            elements.privacyIndicator.title = privacyShowWord ? 'Letztes Wort ausblenden' : 'Letztes Wort anzeigen';
        }
        updatePrivacyOverlay();
        
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
        localStorage.setItem('ttsProvider', provider);
        
        // Hauptansicht aktualisieren
        updateProviderUI(provider);
        if (provider === 'elevenlabs') {
            await loadElevenLabsVoices();
        }
        
        closeSettingsModal();
        showToast('Einstellungen gespeichert', 'success');
    } catch (error) {
        alert(`Fehler: ${error.message}`);
    }
}

// === ElevenLabs Functions ===

function updateProviderUI(provider) {
    currentProvider = provider;
    if (provider === 'elevenlabs') {
        if (elements.elevenlabsSettings) elements.elevenlabsSettings.classList.remove('hidden');
        if (elements.pyttsx3Settings) elements.pyttsx3Settings.classList.add('hidden');
        if (elements.currentVoice) elements.currentVoice.style.display = 'none';
        if (elements.elevenlabsVoiceQuick) elements.elevenlabsVoiceQuick.style.display = '';
    } else {
        if (elements.elevenlabsSettings) elements.elevenlabsSettings.classList.add('hidden');
        if (elements.pyttsx3Settings) elements.pyttsx3Settings.classList.remove('hidden');
        if (elements.currentVoice) elements.currentVoice.style.display = 'none';
        if (elements.elevenlabsVoiceQuick) elements.elevenlabsVoiceQuick.style.display = 'none';
    }
}

async function loadPyttsx3Voices(selectedId = '') {
    if (!elements.pyttsx3VoiceSelect) return;
    try {
        const voices = await api('/api/pyttsx3/voices');
        elements.pyttsx3VoiceSelect.innerHTML = '<option value="">Automatisch (nach Sprache)</option>';
        voices.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.id;
            opt.textContent = v.name;
            if (v.id === selectedId) opt.selected = true;
            elements.pyttsx3VoiceSelect.appendChild(opt);
        });
    } catch (e) {
        console.error('pyttsx3 Stimmen konnten nicht geladen werden:', e);
    }
}

async function loadElevenLabsVoices() {
    try {
        // Erst API Key ans Backend senden, falls noch nicht gespeichert
        const apiKey = elements.elevenlabsApiKeyInput?.value?.trim();
        if (apiKey) {
            await api('/api/elevenlabs/config', {
                method: 'POST',
                body: JSON.stringify({ api_key: apiKey })
            });
        }
        
        const result = await api('/api/elevenlabs/voices');
        const currentVoiceId = result.current_voice_id;
        
        // Populate settings dropdown
        elements.elevenlabsVoiceSelect.innerHTML = '<option value="">Select voice...</option>';
        // Populate quick dropdown in main view
        if (elements.elevenlabsVoiceQuickSelect) {
            elements.elevenlabsVoiceQuickSelect.innerHTML = '<option value="">Select voice...</option>';
        }
        
        for (const voice of result.voices) {
            const option = document.createElement('option');
            option.value = voice.voice_id;
            option.textContent = `${voice.name} (${voice.category})`;
            if (voice.voice_id === currentVoiceId) {
                option.selected = true;
            }
            elements.elevenlabsVoiceSelect.appendChild(option);
            
            // Auch ins Quick-Dropdown
            if (elements.elevenlabsVoiceQuickSelect) {
                const opt2 = option.cloneNode(true);
                if (voice.voice_id === currentVoiceId) opt2.selected = true;
                elements.elevenlabsVoiceQuickSelect.appendChild(opt2);
            }
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

// Returns a Promise that resolves when the user confirms (true) or cancels (false).
// Visualises the pending state on the speak button – no popup needed.
function showConfirmSend(text) {
    return new Promise((resolve) => {
        const btn = elements.speakBtn;
        const originalHTML = btn.innerHTML;

        btn.classList.add('confirm-pending');
        btn.innerHTML = document.body.classList.contains('mini-mode') ? '↵' : '↵ Confirm?';

        function cleanup(result) {
            btn.classList.remove('confirm-pending');
            btn.innerHTML = originalHTML;
            btn.removeEventListener('click', onConfirm);
            document.removeEventListener('keydown', onKey, true);
            resolve(result);
        }
        function onConfirm() { cleanup(true); }
        function onKey(e) {
            if (e.key === 'Enter' && !e.ctrlKey && !e.shiftKey) {
                e.preventDefault(); e.stopPropagation(); cleanup(true);
            } else {
                e.stopPropagation(); cleanup(false);
            }
        }
        btn.addEventListener('click', onConfirm);
        document.addEventListener('keydown', onKey, true);
    });
}

function openSettingsModal() {
    loadSettings();
    renderSetManager();
    elements.settingsModal.classList.add('active');
}

function closeSettingsModal() {
    elements.settingsModal.classList.remove('active');
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
            // Halbtransparent wenn Textfeld nicht fokussiert
            if (document.activeElement !== elements.textInput) {
                window.electronAPI.setOpacity(0.4);
            }
        } else {
            document.body.classList.remove('mini-mode', 'mini-top', 'mini-bottom');
            window.electronAPI.setOpacity(1);
            hideMiniQuickDropdown();
            renderQuickAccess();
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
        showToast(t('toast_no_last_msg'), 'info');
        return;
    }
    
    elements.miniRepeatBtn.disabled = true;
    
    try {
        // Extract audio URL (relative path for backend)
        const audioPath = currentAudioUrl.replace(window.API_URL, '');
        
        // Play audio via backend on selected device
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

// === Typing sound (HTML5 Audio) ===
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
        // Choose random start point
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
    if (typingSoundInterval) return; // Already running
    
    // Sicherstellen dass Sound geladen ist
    if (!typingSoundReady) {
        preloadTypingSound();
    }
    
    typingSoundInterval = setInterval(playTypingClick, TYPING_SOUND_INTERVAL_MS);
    
    // Also play via mic device if active
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
    // Reset timeout
    if (typingSoundTimeout) {
        clearTimeout(typingSoundTimeout);
    }
    // Start sound if not already running
    startTypingSound();
    // Sound stoppen nach Pause
    typingSoundTimeout = setTimeout(() => {
        stopTypingSound();
        typingSoundTimeout = null;
    }, TYPING_STOP_DELAY_MS);
}

// === Microphone output (for phone calls) ===
let micOutputEnabled = false;

function updateMicToggleUI(enabled, device) {
    if (enabled !== undefined) {
        micOutputEnabled = enabled;
    }
    
    const btn = elements.micToggleBtn;
    if (!btn) return;
    
    const hasDevice = device !== null && device !== undefined && device !== -1;
    
    // MIC Badge aktualisieren
    const micBadge = document.getElementById('micBadge');
    
    if (micOutputEnabled && hasDevice) {
        btn.classList.add('mic-active');
        btn.title = 'Mikrofon-Ausgabe aktiv (Klick zum Deaktivieren)';
        btn.innerHTML = '🎙️';
        if (micBadge) micBadge.classList.add('active');
    } else if (hasDevice) {
        btn.classList.remove('mic-active');
        btn.title = 'Enable microphone output (for phone calls)';
        btn.innerHTML = '🎤';
        if (micBadge) micBadge.classList.remove('active');
    } else {
        btn.classList.remove('mic-active');
        btn.title = 'No microphone device configured (set in settings)';
        btn.innerHTML = '🎤';
        btn.style.opacity = '0.4';
        if (micBadge) micBadge.classList.remove('active');
        return;
    }
    btn.style.opacity = '1';
}

async function toggleMicOutput() {
    try {
        // Check whether a mic device is configured
        const micData = await api('/api/mic-device');
        if (micData.device === null || micData.device === undefined) {
            showToast('Please configure a microphone device in settings first (e.g. VB-Cable)', 'error');
            openSettingsModal();
            return;
        }
        
        const result = await api('/api/mic-device/toggle', {
            method: 'PUT',
            body: JSON.stringify({})
        });
        
        updateMicToggleUI(result.enabled, result.device);
        localStorage.setItem('micEnabled', result.enabled.toString());
        
        if (result.enabled) {
            showToast('🎙️ Microphone output enabled – speech will also be sent via the virtual microphone', 'success');
        } else {
            showToast('🎤 Mikrofon-Ausgabe deaktiviert', 'info');
        }
    } catch (error) {
        console.error('Mikrofon-Toggle Fehler:', error);
        showToast('Fehler beim Umschalten der Mikrofon-Ausgabe', 'error');
    }
}

// Echo test for microphone output
async function micEchoTest() {
    const btn = document.getElementById('micEchoTestBtn');
    if (!btn) return;
    
    const micIndex = parseInt(elements.micDeviceSelect.value);
    if (micIndex === -1) {
        showToast('Please select a microphone device first', 'error');
        return;
    }
    
    // Erst Mic-Device setzen (falls noch nicht gespeichert)
    await api('/api/mic-device', {
        method: 'PUT',
        body: JSON.stringify({ index: micIndex })
    });
    
    btn.disabled = true;
    btn.textContent = '⏳ Test...';
    showToast('🔊 Playing test tone on mic device...', 'info');
    
    try {
        const result = await api('/api/mic-device/echo-test', {
            method: 'POST'
        });
        showToast('✅ Test tone played – if you hear it in the phone app, the connection works!', 'success');
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
        playTone(1100, now + 0.15, 0.2); // Second tone (higher)
        
        // Close AudioContext after playback
        setTimeout(() => audioContext.close(), 500);
    } catch (error) {
        console.error('Fehler beim Abspielen des Signaltons:', error);
    }
}

// === Privacy Mode ===
// === Suggestions ===
async function fetchSuggestions(query) {
    try {
        const res = await fetch(`${window.API_URL}/api/history/suggest?query=${encodeURIComponent(query)}&limit=3`);
        if (!res.ok) return;
        _suggestions = await res.json();
        _suggestIndex = -1;
        renderSuggestions();
    } catch (e) {
        // Netzwerkfehler ignorieren
    }
}

function renderSuggestions() {
    const dd = elements.suggestionsDropdown;
    if (!_suggestions.length) {
        hideSuggestions();
        return;
    }
    dd.innerHTML = '<div class="suggestion-hint"><span>Tab ↹ switch · Enter ↵ apply · Esc close</span></div>' +
        _suggestions.map((s, i) =>
            `<div class="suggestion-item${i === _suggestIndex ? ' active' : ''}" data-index="${i}">${escapeHtml(s.text)}</div>`
        ).join('');
    dd.classList.add('visible');

    dd.querySelectorAll('.suggestion-item').forEach(el => {
        el.addEventListener('mousedown', (e) => {
            e.preventDefault();
            const idx = parseInt(el.dataset.index);
            elements.textInput.value = _suggestions[idx].text;
            hideSuggestions();
            if (elements.charCount) {
                elements.charCount.textContent = `${elements.textInput.value.length} ${t('chars')}`;
            }
            updatePrivacyOverlay();
            elements.textInput.focus();
        });
    });
}

function hideSuggestions() {
    _suggestions = [];
    _suggestIndex = -1;
    elements.suggestionsDropdown.classList.remove('visible');
    elements.suggestionsDropdown.innerHTML = '';
}

// === Mini-Modus Schnellzugriff-Fenster ===
const QUICK_ACCESS_KEYS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'];

function showMiniQuickDropdown() {
    const items = quickAccessItems.slice(0, QUICK_ACCESS_KEYS.length);
    if (items.length === 0) return;
    window.electronAPI.showQuickAccessWindow(items);
}

function hideMiniQuickDropdown() {
    window.electronAPI.hideQuickAccessWindow();
}

async function showMiniSetPicker() {
    const sets = await getQuickAccessSets();
    const setNames = Object.keys(sets);
    if (setNames.length === 0) {
        showToast('Keine Sets vorhanden', 'info');
        return;
    }
    const setList = setNames.slice(0, QUICK_ACCESS_KEYS.length).map(name => ({
        name,
        count: sets[name] ? sets[name].length : 0
    }));
    await window.electronAPI.showSetPicker(setList);
    miniSetPickerMode = true;
}

function hideMiniSetPicker() {
    miniSetPickerMode = false;
    // Return to normal item view
    showMiniQuickDropdown();
}

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
    if (!privacyMode || !privacyShowWord) {
        elements.privacyLastWord.textContent = '';
        elements.privacyLastWord.classList.remove('has-word');
        return;
    }
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
        // If we are at the top, open keyboard below and vice versa
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
            elements.charCount.textContent = `${elements.textInput.value.length} ${t('chars')}`;
        }
        // Play typing sound
        onTypingActivity();
    });
    
    // Tastatur starten bei Fokus
    elements.textInput.addEventListener('focus', () => {
        startKeyboard();
    });
    
    // Tastatur stoppen bei Fokusverlust
    elements.textInput.addEventListener('blur', () => {
        stopKeyboard();
        stopTypingSound(); // Stop typing sound immediately
    });
    
    // Enter key to speak, Ctrl+Enter for AI completion
    elements.textInput.addEventListener('keydown', async (e) => {
        // Suggestions-Navigation
        if (_suggestions.length > 0 && elements.suggestionsDropdown.classList.contains('visible')) {
            if (e.key === 'Tab') {
                e.preventDefault();
                _suggestIndex = (_suggestIndex + 1) % _suggestions.length;
                renderSuggestions();
                return;
            }
            if (e.key === 'Enter' && !e.ctrlKey && !e.shiftKey && _suggestIndex >= 0) {
                e.preventDefault();
                elements.textInput.value = _suggestions[_suggestIndex].text;
                hideSuggestions();
                if (elements.charCount) {
                    elements.charCount.textContent = `${elements.textInput.value.length} ${t('chars')}`;
                }
                updatePrivacyOverlay();
                return;
            }
            if (e.key === 'Escape') {
                hideSuggestions();
                return;
            }
        }

        if (e.key === 'Escape' && miniSetPickerMode) {
            hideMiniSetPicker();
            return;
        }

        if (e.key === 'Enter' && e.ctrlKey && e.shiftKey) {
            // Strg+Shift+Enter = KI-Auto-Korrektur togglen
            e.preventDefault();
            kiAutoCorrect = !kiAutoCorrect;
            const badge = document.getElementById('kiBadge');
            if (badge) badge.classList.toggle('active', kiAutoCorrect);
            showToast(kiAutoCorrect ? 'KI-Korrektur aktiviert' : 'KI-Korrektur deaktiviert', kiAutoCorrect ? 'success' : 'info');
            return;
        }

        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            const text = elements.textInput.value.trim();
            if (!text) {
                // Leeres Feld: KI-Auto-Korrektur togglen
                kiAutoCorrect = !kiAutoCorrect;
                const badge = document.getElementById('kiBadge');
                if (badge) badge.classList.toggle('active', kiAutoCorrect);
                showToast(kiAutoCorrect ? 'KI-Korrektur aktiviert' : 'KI-Korrektur deaktiviert', kiAutoCorrect ? 'success' : 'info');
                return;
            }
            // Ctrl+Enter with text = AI completion
            elements.statusText.textContent = 'AI completing...';
            const completed = await completeWithAI(text);
            if (completed) {
                elements.textInput.value = completed;
                if (elements.charCount) {
                    elements.charCount.textContent = `${completed.length} ${t('chars')}`;
                }
                elements.statusText.textContent = 'AI text applied – press Enter to speak';
                elements.textInput.focus();
            }
        } else if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const text = elements.textInput.value.trim();
            // Set-Picker Modus: Buchstabe = Set laden
            if (miniSetPickerMode && text.length === 1) {
                const keyIdx = QUICK_ACCESS_KEYS.indexOf(text.toUpperCase());
                if (keyIdx >= 0) {
                    elements.textInput.value = '';
                    if (elements.charCount) elements.charCount.textContent = charStr(0);
                    const sets = await getQuickAccessSets();
                    const setNames = Object.keys(sets).slice(0, QUICK_ACCESS_KEYS.length);
                    if (keyIdx < setNames.length) {
                        await loadQuickAccessSet(setNames[keyIdx]);
                        showToast(`Set geladen: ${setNames[keyIdx]}`, 'success');
                    }
                    hideMiniSetPicker();
                }
                return;
            }
            // Einzelner Buchstabe = Schnellzugriff
            if (text.length === 1) {
                const keyIdx = QUICK_ACCESS_KEYS.indexOf(text.toUpperCase());
                if (keyIdx >= 0 && keyIdx < quickAccessItems.length) {
                    elements.textInput.value = '';
                    if (elements.charCount) elements.charCount.textContent = charStr(0);
                    playQuickAccessItem(quickAccessItems[keyIdx]);
                    return;
                }
            }
            if (text) {
                if (confirmSend) {
                    const confirmed = await showConfirmSend(text);
                    if (!confirmed) return;
                }
                if (kiAutoCorrect) {
                    // KI-Korrektur + Sprechen
                    elements.statusText.textContent = 'KI korrigiert...';
                    const corrected = await completeWithAI(text);
                    if (corrected) {
                        elements.textInput.value = corrected;
                        if (elements.charCount) elements.charCount.textContent = `${corrected.length} ${t('chars')}`;
                    }
                    speak();
                } else {
                    speak();
                }
            } else if (currentAudioUrl) {
                // Leeres Textfeld + Enter = letzte Nachricht wiederholen
                repeatLastMessage();
            }
        } else if (e.key === 's' && e.ctrlKey) {
            // Ctrl+S = generate + add to quick access (temporary)
            // Bei leerem Textfeld im Mini-Modus: Set-Picker anzeigen
            // With empty text field otherwise: make all temporary entries permanent
            e.preventDefault();
            const text = elements.textInput.value.trim();
            if (!text) {
                if (document.body.classList.contains('mini-mode')) {
                    if (miniSetPickerMode) {
                        hideMiniSetPicker();
                    } else {
                        await showMiniSetPicker();
                    }
                    return;
                }
                const tempItems = quickAccessItems.filter(q => q._temporary);
                if (tempItems.length === 0) return;
                tempItems.forEach(q => { delete q._temporary; });
                saveQuickAccessToStorage();
                renderQuickAccess();
                showToast(`${tempItems.length} Eintrag${tempItems.length > 1 ? 'e' : ''} dauerhaft gespeichert`, 'success');
                return;
            }
            elements.generateBtn && (elements.generateBtn.disabled = true);
            elements.speakBtn && (elements.speakBtn.disabled = true);
            elements.statusText.textContent = t('generating_audio');
            try {
                const result = await api('/api/tts/speak', {
                    method: 'POST',
                    body: JSON.stringify({ text: text, language: elements.languageSelect.value })
                });
                if (result.success) {
                    const tempId = `temp_${Date.now()}`;
                    addToQuickAccess({
                        id: tempId,
                        text: text,
                        audio_url: result.audio_url,
                        is_favorite: false,
                        _temporary: true
                    });
                    await addToPlaybackHistory(text, result.audio_url, null);
                    loadHistory();
                    elements.textInput.value = '';
                    updatePrivacyOverlay();
                    if (elements.charCount) elements.charCount.textContent = charStr(0);
                    elements.statusText.textContent = 'Bereit';
                    showToast('Generated & added to quick access', 'success');
                }
            } catch (error) {
                showToast(`Fehler: ${error.message}`, 'error');
            } finally {
                elements.generateBtn && (elements.generateBtn.disabled = false);
                elements.speakBtn && (elements.speakBtn.disabled = false);
                checkStatus();
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
        } else if (e.key === 'd' && e.ctrlKey && !e.shiftKey) {
            // Strg+D = Signalton
            e.preventDefault();
            playSignalTone();
        } else if (e.key === 'D' && e.ctrlKey && e.shiftKey) {
            // Strg+Shift+D = Vor-Signal Modus togglen
            e.preventDefault();
            signalBeforeSpeak = !signalBeforeSpeak;
            const badge = document.getElementById('bellBadge');
            if (badge) badge.classList.toggle('active', signalBeforeSpeak);
            showToast(signalBeforeSpeak ? '🔔 Vor-Signal aktiviert' : '🔕 Vor-Signal deaktiviert', signalBeforeSpeak ? 'success' : 'info');
        } else if (e.key === 'p' && e.ctrlKey) {
            // Strg+P = Privacy-Modus
            e.preventDefault();
            togglePrivacyMode();
        }
    });

    // Privacy overlay bei Texteingabe aktualisieren
    elements.textInput.addEventListener('input', updatePrivacyOverlay);

    // Klick auf 🔒 = letztes Wort ein/ausblenden
    if (elements.privacyIndicator) {
        elements.privacyIndicator.addEventListener('click', () => {
            privacyShowWord = !privacyShowWord;
            elements.privacyIndicator.classList.toggle('show-word', privacyShowWord);
            elements.privacyIndicator.title = privacyShowWord ? 'Letztes Wort ausblenden' : 'Letztes Wort anzeigen';
            updatePrivacyOverlay();
        });
        elements.privacyIndicator.title = 'Letztes Wort anzeigen';
    }

    // Suggestions bei Texteingabe laden
    elements.textInput.addEventListener('input', () => {
        clearTimeout(_suggestTimer);
        const text = elements.textInput.value.trim();
        if (text.length < 3) {
            hideSuggestions();
            return;
        }
        _suggestTimer = setTimeout(() => fetchSuggestions(text), 300);
    });

    // Hide suggestions on blur (with delay for click events)
    elements.textInput.addEventListener('blur', () => {
        setTimeout(() => hideSuggestions(), 150);
    });

    // Mini-Modus Transparenz: fokussiert = opak, unfokussiert = halbtransparent
    // + Schnellzugriff-Dropdown ein-/ausblenden
    elements.textInput.addEventListener('focus', () => {
        if (document.body.classList.contains('mini-mode')) {
            window.electronAPI.setOpacity(1);
            showMiniQuickDropdown();
        }
    });
    elements.textInput.addEventListener('blur', () => {
        if (document.body.classList.contains('mini-mode')) {
            window.electronAPI.setOpacity(0.5);
            setTimeout(() => {
                hideMiniQuickDropdown();
                miniSetPickerMode = false;
            }, 150);
        }
    });

    // Schnellzugriff-Popup: Play-Request vom separaten Fenster
    window.electronAPI.onQuickAccessPlay((index) => {
        if (index >= 0 && index < quickAccessItems.length) {
            playQuickAccessItem(quickAccessItems[index]);
        }
    });

    // Set-Picker: Set-Auswahl via Klick im Popup-Fenster
    window.electronAPI.onSetPickerSelected(async (name) => {
        await loadQuickAccessSet(name);
        showToast(`Set geladen: ${name}`, 'success');
        hideMiniSetPicker();
    });
    
    // Context input - live save to localStorage
    elements.aiContextInput.value = localStorage.getItem('aiContext') || '';

    // Theme live-Wechsel
    elements.themeSelect.addEventListener('change', () => {
        const theme = elements.themeSelect.value;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    });

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
            if (e.target.value === 'pyttsx3') loadPyttsx3Voices();
        });
    }
    
    // ElevenLabs Voices refresh
    if (elements.refreshElevenVoicesBtn) {
        elements.refreshElevenVoicesBtn.addEventListener('click', loadElevenLabsVoices);
    }
    
    // ElevenLabs Quick Voice Select (Hauptansicht)
    if (elements.elevenlabsVoiceQuickSelect) {
        elements.elevenlabsVoiceQuickSelect.addEventListener('change', async (e) => {
            const voiceId = e.target.value;
            // Settings-Dropdown synchronisieren
            if (elements.elevenlabsVoiceSelect) elements.elevenlabsVoiceSelect.value = voiceId;
            // Voice ans Backend senden
            try {
                await api('/api/elevenlabs/config', {
                    method: 'POST',
                    body: JSON.stringify({ voice_id: voiceId })
                });
                const selectedText = e.target.options[e.target.selectedIndex]?.text || '';
                showToast(`Stimme: ${selectedText}`, 'success');
            } catch (err) {
                console.error('ElevenLabs voice change error:', err);
            }
        });
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

    // Settings Tabs
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.settings-tab-panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab).classList.add('active');
        });
    });
    
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
    if (elements.temperatureSlider) {
        elements.temperatureSlider.addEventListener('input', (e) => {
            if (elements.temperatureValue) elements.temperatureValue.textContent = e.target.value;
        });
    }
    if (elements.repetitionSlider) {
        elements.repetitionSlider.addEventListener('input', (e) => {
            if (elements.repetitionValue) elements.repetitionValue.textContent = e.target.value;
        });
    }
    
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
    if (elements.newQuickAccessSetBtn) {
        elements.newQuickAccessSetBtn.addEventListener('click', () => {
            currentQuickAccessSetName = null;
            quickAccessItems = [];
            saveQuickAccessToStorage();
            renderQuickAccess();
            renderQuickAccessSetSelect();
            showToast(t('toast_new_set'), 'info');
        });
    }
    if (elements.clearQuickAccessBtn) {
        elements.clearQuickAccessBtn.addEventListener('click', clearQuickAccess);
    }
    if (elements.saveQuickAccessSetBtn) {
        elements.saveQuickAccessSetBtn.addEventListener('click', saveQuickAccessSet);
    }
    if (elements.quickAccessSetBtn) {
        elements.quickAccessSetBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (elements.setPickerPopup?.style.display !== 'none') { closeSetPickerPopup(); } else { openSetPickerPopup(); }
        });
    }
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#setPickerPopup') && !e.target.closest('#quickAccessSetBtn')) closeSetPickerPopup();
    });
    
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
        
        // Ctrl+M to toggle microphone output
        if (e.ctrlKey && e.key === 'm') {
            e.preventDefault();
            toggleMicOutput();
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
    
    // Apply i18n translations
    if (window.i18n) window.i18n.apply();
    
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
    
    // Pre-load typing sound in background with delay
    setTimeout(() => {
        try { preloadTypingSound(); } catch(e) { console.error('[Typing] Init-Fehler:', e); }
    }, 2000);
    
    if (connected) {
        // Catalog and history can be loaded immediately
        await loadCatalogTags();
        loadCatalogPreview();
        loadHistory();
        loadFavorites();
        
        // Quick Access aus localStorage laden
        loadQuickAccessFromStorage();
        renderQuickAccess();
        renderQuickAccessSetSelect();
        
        // Mikrofon-Ausgabe: gespeicherte Einstellungen wiederherstellen
        try {
            const savedMicDevice = localStorage.getItem('micDevice');
            const savedMicEnabled = localStorage.getItem('micEnabled');
            if (savedMicDevice !== null && savedMicDevice !== '-1') {
                await api('/api/mic-device', {
                    method: 'PUT',
                    body: JSON.stringify({ index: parseInt(savedMicDevice), enabled: savedMicEnabled === 'true' })
                });
            }
            const micData = await api('/api/mic-device');
            updateMicToggleUI(micData.enabled, micData.device);
        } catch (e) {
            console.log('Mikrofon-Status konnte nicht geladen werden');
        }
        
        // Gespeicherte Ansicht wiederherstellen
        if (localStorage.getItem('viewMode') === 'tags') {
            toggleView();
        }
        
        // Update provider-dependent UI in main view
        // localStorage nutzen da Backend beim Start tts noch nicht geladen hat
        const savedProvider = localStorage.getItem('ttsProvider') || 'pyttsx3';
        updateProviderUI(savedProvider);
        if (savedProvider === 'elevenlabs') {
            const savedKey = localStorage.getItem('elevenlabsApiKey') || '';
            if (savedKey && elements.elevenlabsApiKeyInput) elements.elevenlabsApiKeyInput.value = savedKey;
            await loadElevenLabsVoices();
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
            // Check provider from backend (TTS is now loaded)
            try {
                const settings = await api('/api/settings');
                const backendProvider = settings.tts_provider || 'pyttsx3';
                if (backendProvider !== currentProvider) {
                    localStorage.setItem('ttsProvider', backendProvider);
                    updateProviderUI(backendProvider);
                    if (backendProvider === 'elevenlabs') {
                        const savedKey = localStorage.getItem('elevenlabsApiKey') || '';
                        if (savedKey && elements.elevenlabsApiKeyInput) elements.elevenlabsApiKeyInput.value = savedKey;
                        await loadElevenLabsVoices();
                    }
                }
            } catch (e) {
                console.log('Provider-Check nach TTS-Load fehlgeschlagen');
            }
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
            updateStatus('Ready', 'connected');
        } else {
            updateStatus('Modellwechsel fehlgeschlagen', 'error');
            // Reset dropdown
            if (elements.ttsModelSelect) {
                elements.ttsModelSelect.value = currentTTSModel;
            }
        }
    } catch (error) {
        console.error('Fehler beim Modellwechsel:', error);
        updateStatus('Fehler beim Modellwechsel', 'error');
        // Reset dropdown
        if (elements.ttsModelSelect) {
            elements.ttsModelSelect.value = currentTTSModel;
        }
    }
}

// Start
document.addEventListener('DOMContentLoaded', init);

