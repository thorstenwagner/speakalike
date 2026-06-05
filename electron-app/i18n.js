// i18n.js – SpeakAlike UI translations (de / en)
(function () {
    const translations = {
        de: {
            // Header
            status_connecting: 'Verbinde...',
            toggle_input_title: 'Texteingabe oben/unten',
            mini_mode_title: 'Mini-Modus',
            settings_title: 'Einstellungen',
            ui_lang_title: 'Switch to English',

            // Main area
            language_label: '🌍 Sprache:',
            context_placeholder: 'Gesprächskontext (z.B. Arztbesuch, Einkauf...)',
            clear_context_title: 'Kontext löschen',
            select_voice_opt: 'Stimme wählen...',
            speak_label: 'Sprechen',
            generate_label: '💾 Generieren',
            mic_toggle_title: 'Mikrofon-Ausgabe (für Telefonie)',
            repeat_title: 'Letzte Nachricht wiederholen',
            position_title: 'Position wechseln (oben/unten)',
            exit_mini_title: 'Mini-Modus beenden',

            // Search bar
            search_all_placeholder: '🔍 Suche in allen Spalten (Begriffe mit Leerzeichen trennen)...',
            search_or: 'ODER',
            search_and: 'UND',
            clear_search_title: 'Suche leeren',
            toggle_view_btn: '🏷️ Tag-Browser',

            // Section headings
            history_heading: '🕐 Verlauf',
            history_empty: 'Noch keine Nachrichten',
            favorites_heading: '⭐ Favoriten',
            favorites_empty: 'Noch keine Favoriten',
            catalog_heading: '📚 Katalog',
            catalog_open_btn: 'Öffnen',
            catalog_empty: 'Noch keine Einträge',
            quick_access_heading: '🚀 Schnellzugriff',
            new_set_title: 'Neues Set anlegen',
            load_sets_title: 'Set laden',
            save_set_title: 'Set speichern',
            clear_qa_title: 'Liste leeren',
            quick_access_empty: 'Nachrichten hier hinzufügen mit dem ➕ Button',

            // Tag browser
            tags_heading: '🏷️ Tags',
            clear_tag_filters_title: 'Alle Filter entfernen',
            clear_tag_filters_btn: '✕ Alle',
            tags_loading: 'Lade Tags...',
            messages_heading: '📋 Nachrichten',
            tag_browser_hint: 'Wähle einen Tag um Nachrichten anzuzeigen',

            // Settings modal
            settings_modal_title: '⚙️ Einstellungen',
            tab_speech: '🔊 Sprache',
            tab_audio: '🎛️ Audio',
            tab_general: '⚙️ Allgemein',
            tts_provider_label: '🔌 TTS-Provider',
            opt_elevenlabs: '☁️ ElevenLabs (Cloud)',
            opt_pyttsx3: '💻 pyttsx3 (System-TTS)',
            elevenlabs_key_label: '🔑 ElevenLabs API Key',
            elevenlabs_voice_label: '🎤 ElevenLabs Stimme',
            refresh_voices_title: 'Stimmen laden',
            elevenlabs_model_label: '🧠 ElevenLabs Modell',
            stability_label: 'Stabilität',
            similarity_label: 'Ähnlichkeit',
            style_label: 'Stilübertreibung',
            speaker_boost_label: 'Sprachüberschreibung',
            pyttsx3_voice_label: '🗣️ Stimme',
            opt_auto_voice: 'Automatisch (nach Sprache)',
            gender_label: '⚧ Geschlecht (Automatisch)',
            opt_gender_any: 'Egal',
            opt_gender_female: 'Weiblich',
            opt_gender_male: 'Männlich',
            speed_label: 'Geschwindigkeit',
            audio_output_label: '🔊 Ausgabegerät',
            opt_device_default: 'Standard',
            refresh_devices_title: 'Geräte aktualisieren',
            mic_output_label: '🎤 Mikrofon-Ausgabe (für Telefonie)',
            mic_output_hint: 'Wähle ein virtuelles Audiokabel (z.B. VB-Cable) um Sprachnachrichten als Mikrofon-Eingang zu nutzen.',
            opt_mic_none: 'Nicht konfiguriert',
            mic_test_btn: '🔊 Test',
            claude_key_label: '🤖 Claude API Key',
            claude_key_hint: '(für KI-Korrektur)',
            ai_model_label: '🧠 KI-Modell',
            opt_haiku: 'Haiku 4.5 (schnell)',
            opt_sonnet: 'Sonnet 4.6 (besser)',
            input_section_label: '⌨️ Eingabe',
            confirm_play_label: 'Bestätigung vor dem Abspielen anzeigen',
            privacy_section_label: '🔒 Privacy-Modus',
            show_last_word_label: 'Letztes Wort standardmäßig anzeigen',
            theme_label: '🎨 Design',
            opt_dark: '🌙 Dunkel',
            opt_light: '☀️ Hell',
            qa_sets_label: '🚀 Schnellzugriff-Sets',
            no_sets: 'Keine Sets gespeichert',
            save_btn: 'Speichern',

            // New Voice Modal
            new_voice_title: '🎤 Neue Stimme erstellen',
            voice_name_label: 'Name der Stimme',
            voice_name_placeholder: 'z.B. Meine Stimme',
            audio_samples_label: 'Audio-Samples (WAV, MP3, OGG)',
            drop_files_text: '📂 Dateien hierher ziehen oder klicken zum Auswählen',
            sample_hint: '5-30 Sekunden pro Sample empfohlen',
            cancel_btn: 'Abbrechen',
            create_voice_btn: 'Stimme erstellen',

            // Catalog Modal
            catalog_modal_title: '📚 Nachrichtenkatalog',
            catalog_search_placeholder: '🔍 Suchen...',
            tag_filter_placeholder: 'Tags filtern...',
            tag_search_placeholder: 'Tag suchen...',
            tag_mode_and: 'UND',
            tag_mode_or: 'ODER',
            favorites_only_label: '⭐ Nur Favoriten',
            import_mp3_btn: '📥 MP3 importieren',

            // Save to Catalog
            save_catalog_title: '📁 Zum Katalog hinzufügen',
            text_label: 'Text',
            keywords_label: 'Schlagworte',
            auto_tags_btn: '🤖 Auto-Tags',
            tag_input_placeholder: 'Tag eingeben...',
            existing_tags_label: 'Vorhandene Tags:',
            save_catalog_btn: '💾 Speichern',

            // Edit Tags
            edit_tags_title: '🏷️ Tags bearbeiten',

            // Import MP3
            import_mp3_title: '📥 MP3 importieren',
            audio_file_label: 'Audio-Datei (MP3, WAV, OGG)',
            drop_file_text: '📂 Datei hierher ziehen oder klicken',
            play_title: 'Abspielen',
            transcribe_title: 'Text erkennen',
            transcribe_btn: '🎤 Erkennen',
            import_text_label: 'Text (Inhalt der Nachricht)',
            import_text_placeholder: 'Was wird in der Audio gesagt?',
            import_keywords_label: 'Schlagworte',
            auto_gen_tags_title: 'Tags automatisch generieren',
            existing_tags_muted: 'Vorhandene Tags:',
            import_btn: '📥 Importieren',

            // AI Confirm
            ai_confirm_title: '🤖 KI-Vervollständigung',
            ai_original_label: 'Original:',
            ai_completed_label: 'Vervollständigt (bearbeitbar):',
            ai_reject_btn: '✕ Ablehnen',
            ai_accept_btn: '✓ Übernehmen & Sprechen',

            // Dynamic (JS)
            chars: 'Zeichen',
            not_connected: 'Nicht verbunden',
            loading_model: (name) => `Lade ${name}...`,
            deleting_voice: (name) => `Lösche ${name}...`,
            voice_deleted: (name) => `Stimme "${name}" gelöscht`,
            generating_audio: 'Generiere Audio...',
            generating_bg: 'Generiere Audio im Hintergrund...',

            // Toasts
            toast_no_text: 'Bitte Text eingeben.',
            toast_no_api_key: 'Bitte Claude API Key in den Einstellungen hinterlegen.',
            toast_no_last_msg: 'Keine letzte Nachricht vorhanden.',
            toast_qa_empty: 'Schnellzugriff ist leer',
            toast_new_set: 'Neues Set – Liste geleert',
            toast_already_in_qa: 'Bereits im Schnellzugriff',
            toast_name_exists: 'Name existiert bereits',
            toast_settings_saved: 'Einstellungen gespeichert',
            toast_copied: 'Kopiert',
            toast_saved_catalog: 'Im Katalog gespeichert',
            toast_deleted: 'Gelöscht',
            toast_backend_not_ready: 'Backend noch nicht bereit.',
        },
        en: {
            // Header
            status_connecting: 'Connecting...',
            toggle_input_title: 'Move text input up/down',
            mini_mode_title: 'Mini mode',
            settings_title: 'Settings',
            ui_lang_title: 'Zu Deutsch wechseln',

            // Main area
            language_label: '🌍 Language:',
            context_placeholder: 'Conversation context (e.g. doctor visit, shopping...)',
            clear_context_title: 'Clear context',
            select_voice_opt: 'Select voice...',
            speak_label: 'Speak',
            generate_label: '💾 Generate',
            mic_toggle_title: 'Mic output (for telephony)',
            repeat_title: 'Repeat last message',
            position_title: 'Switch position (top/bottom)',
            exit_mini_title: 'Exit mini mode',

            // Search bar
            search_all_placeholder: '🔍 Search all columns (separate terms with spaces)...',
            search_or: 'OR',
            search_and: 'AND',
            clear_search_title: 'Clear search',
            toggle_view_btn: '🏷️ Tag Browser',

            // Section headings
            history_heading: '🕐 History',
            history_empty: 'No messages yet',
            favorites_heading: '⭐ Favorites',
            favorites_empty: 'No favorites yet',
            catalog_heading: '📚 Catalog',
            catalog_open_btn: 'Open',
            catalog_empty: 'No entries yet',
            quick_access_heading: '🚀 Quick Access',
            new_set_title: 'Create new set',
            load_sets_title: 'Load set',
            save_set_title: 'Save set',
            clear_qa_title: 'Clear list',
            quick_access_empty: 'Add messages here with the ➕ button',

            // Tag browser
            tags_heading: '🏷️ Tags',
            clear_tag_filters_title: 'Remove all filters',
            clear_tag_filters_btn: '✕ All',
            tags_loading: 'Loading tags...',
            messages_heading: '📋 Messages',
            tag_browser_hint: 'Select a tag to show messages',

            // Settings modal
            settings_modal_title: '⚙️ Settings',
            tab_speech: '🔊 Speech',
            tab_audio: '🎛️ Audio',
            tab_general: '⚙️ General',
            tts_provider_label: '🔌 TTS Provider',
            opt_elevenlabs: '☁️ ElevenLabs (Cloud)',
            opt_pyttsx3: '💻 pyttsx3 (System TTS)',
            elevenlabs_key_label: '🔑 ElevenLabs API Key',
            elevenlabs_voice_label: '🎤 ElevenLabs Voice',
            refresh_voices_title: 'Load voices',
            elevenlabs_model_label: '🧠 ElevenLabs Model',
            stability_label: 'Stability',
            similarity_label: 'Similarity',
            style_label: 'Style exaggeration',
            speaker_boost_label: 'Speaker boost',
            pyttsx3_voice_label: '🗣️ Voice',
            opt_auto_voice: 'Automatic (by language)',
            gender_label: '⚧ Gender (Automatic)',
            opt_gender_any: 'Any',
            opt_gender_female: 'Female',
            opt_gender_male: 'Male',
            speed_label: 'Speed',
            audio_output_label: '🔊 Output device',
            opt_device_default: 'Default',
            refresh_devices_title: 'Refresh devices',
            mic_output_label: '🎤 Mic output (for telephony)',
            mic_output_hint: 'Select a virtual audio cable (e.g. VB-Cable) to use speech messages as mic input.',
            opt_mic_none: 'Not configured',
            mic_test_btn: '🔊 Test',
            claude_key_label: '🤖 Claude API Key',
            claude_key_hint: '(for AI correction)',
            ai_model_label: '🧠 AI Model',
            opt_haiku: 'Haiku 4.5 (fast)',
            opt_sonnet: 'Sonnet 4.6 (better)',
            input_section_label: '⌨️ Input',
            confirm_play_label: 'Show confirmation before playback',
            privacy_section_label: '🔒 Privacy mode',
            show_last_word_label: 'Show last word by default',
            theme_label: '🎨 Theme',
            opt_dark: '🌙 Dark',
            opt_light: '☀️ Light',
            qa_sets_label: '🚀 Quick Access Sets',
            no_sets: 'No sets saved',
            save_btn: 'Save',

            // New Voice Modal
            new_voice_title: '🎤 Create new voice',
            voice_name_label: 'Voice name',
            voice_name_placeholder: 'e.g. My Voice',
            audio_samples_label: 'Audio samples (WAV, MP3, OGG)',
            drop_files_text: '📂 Drag files here or click to select',
            sample_hint: '5-30 seconds per sample recommended',
            cancel_btn: 'Cancel',
            create_voice_btn: 'Create voice',

            // Catalog Modal
            catalog_modal_title: '📚 Message Catalog',
            catalog_search_placeholder: '🔍 Search...',
            tag_filter_placeholder: 'Filter tags...',
            tag_search_placeholder: 'Search tag...',
            tag_mode_and: 'AND',
            tag_mode_or: 'OR',
            favorites_only_label: '⭐ Favorites only',
            import_mp3_btn: '📥 Import MP3',

            // Save to Catalog
            save_catalog_title: '📁 Add to catalog',
            text_label: 'Text',
            keywords_label: 'Keywords',
            auto_tags_btn: '🤖 Auto-Tags',
            tag_input_placeholder: 'Enter tag...',
            existing_tags_label: 'Existing tags:',
            save_catalog_btn: '💾 Save',

            // Edit Tags
            edit_tags_title: '🏷️ Edit tags',

            // Import MP3
            import_mp3_title: '📥 Import MP3',
            audio_file_label: 'Audio file (MP3, WAV, OGG)',
            drop_file_text: '📂 Drag file here or click',
            play_title: 'Play',
            transcribe_title: 'Transcribe text',
            transcribe_btn: '🎤 Transcribe',
            import_text_label: 'Text (message content)',
            import_text_placeholder: 'What is said in the audio?',
            import_keywords_label: 'Keywords',
            auto_gen_tags_title: 'Auto-generate tags',
            existing_tags_muted: 'Existing tags:',
            import_btn: '📥 Import',

            // AI Confirm
            ai_confirm_title: '🤖 AI Completion',
            ai_original_label: 'Original:',
            ai_completed_label: 'Completed (editable):',
            ai_reject_btn: '✕ Reject',
            ai_accept_btn: '✓ Accept & Speak',

            // Dynamic (JS)
            chars: 'characters',
            not_connected: 'Not connected',
            loading_model: (name) => `Loading ${name}...`,
            deleting_voice: (name) => `Deleting ${name}...`,
            voice_deleted: (name) => `Voice "${name}" deleted`,
            generating_audio: 'Generating audio...',
            generating_bg: 'Generating audio in background...',

            // Toasts
            toast_no_text: 'Please enter text.',
            toast_no_api_key: 'Please add your Claude API key in settings.',
            toast_no_last_msg: 'No last message available.',
            toast_qa_empty: 'Quick access is empty',
            toast_new_set: 'New set – list cleared',
            toast_already_in_qa: 'Already in quick access',
            toast_name_exists: 'Name already exists',
            toast_settings_saved: 'Settings saved',
            toast_copied: 'Copied',
            toast_saved_catalog: 'Saved to catalog',
            toast_deleted: 'Deleted',
            toast_backend_not_ready: 'Backend not ready yet.',
        }
    };

    const i18n = {
        currentLang: localStorage.getItem('uiLang') || 'de',

        t(key) {
            const d = translations[this.currentLang];
            const fallback = translations['de'];
            const val = (d && d[key] !== undefined) ? d[key] : (fallback[key] !== undefined ? fallback[key] : key);
            return typeof val === 'function' ? val : val;
        },

        tf(key, ...args) {
            const d = translations[this.currentLang];
            const fallback = translations['de'];
            const val = (d && d[key] !== undefined) ? d[key] : (fallback[key] !== undefined ? fallback[key] : key);
            return typeof val === 'function' ? val(...args) : val;
        },

        apply() {
            document.querySelectorAll('[data-i18n]').forEach(el => {
                el.textContent = this.t(el.getAttribute('data-i18n'));
            });
            document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
                el.placeholder = this.t(el.getAttribute('data-i18n-placeholder'));
            });
            document.querySelectorAll('[data-i18n-title]').forEach(el => {
                el.title = this.t(el.getAttribute('data-i18n-title'));
            });
            document.documentElement.lang = this.currentLang;
            const btn = document.getElementById('uiLangBtn');
            if (btn) {
                btn.textContent = this.currentLang === 'de' ? '🇬🇧' : '🇩🇪';
                btn.title = this.t('ui_lang_title');
            }
        },

        setLang(lang) {
            this.currentLang = lang;
            localStorage.setItem('uiLang', lang);
            this.apply();
        }
    };

    window.i18n = i18n;
    window.t = (key) => i18n.t(key);
    window.tf = (key, ...args) => i18n.tf(key, ...args);
})();
