"""
SpeakAlike Katalog - Speicherung und Verwaltung von Sprachnachrichten
"""
import os
import sqlite3
import json
import numpy as np
from datetime import datetime
from typing import List, Optional, Tuple
import shutil


class MessageCatalog:
    """Verwaltet den Katalog gespeicherter Sprachnachrichten."""
    
    def __init__(self, db_path: str = None, audio_dir: str = None):
        """
        Initialisiert den Katalog.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank (Standard: catalog.db im App-Verzeichnis)
            audio_dir: directory for audio files (default: catalog_audio/)
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.db_path = db_path or os.path.join(base_dir, "catalog.db")
        self.audio_dir = audio_dir or os.path.join(base_dir, "catalog_audio")
        
        # Audio-Verzeichnis erstellen
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Datenbank initialisieren
        self._init_db()
    
    def _init_db(self):
        """Erstellt die Datenbank-Tabellen falls nicht vorhanden."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main table for messages
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    audio_path TEXT NOT NULL,
                    voice_model TEXT,
                    duration_seconds REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    play_count INTEGER DEFAULT 0,
                    last_played_at TIMESTAMP,
                    is_favorite INTEGER DEFAULT 0
                )
            ''')
            
            # Tags-Tabelle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')
            
            # Junction table Message <-> Tags
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_tags (
                    message_id INTEGER,
                    tag_id INTEGER,
                    PRIMARY KEY (message_id, tag_id),
                    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )
            ''')
            
            # Volltextsuche-Index
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts 
                USING fts5(text, content='messages', content_rowid='id')
            ''')
            
            # Trigger for full-text search sync
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                    INSERT INTO messages_fts(rowid, text) VALUES (new.id, new.text);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
                    INSERT INTO messages_fts(messages_fts, rowid, text) VALUES('delete', old.id, old.text);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
                    INSERT INTO messages_fts(messages_fts, rowid, text) VALUES('delete', old.id, old.text);
                    INSERT INTO messages_fts(rowid, text) VALUES (new.id, new.text);
                END
            ''')
            
            # Wiedergabe-Verlauf Tabelle (speichert jeden Wiedergabe-Vorgang)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playback_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    audio_url TEXT NOT NULL,
                    catalog_id INTEGER,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    embedding BLOB,
                    FOREIGN KEY (catalog_id) REFERENCES messages(id) ON DELETE SET NULL
                )
            ''')
            
            # Migration: add embedding column if not present
            cursor.execute("PRAGMA table_info(playback_history)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'embedding' not in columns:
                cursor.execute('ALTER TABLE playback_history ADD COLUMN embedding BLOB')
            
            conn.commit()
    
    def add_message(self, text: str, source_audio_path: str, 
                    tags: List[str] = None, voice_model: str = None,
                    duration_seconds: float = None) -> int:
        """
        Adds a new message to the catalog.
        
        Args:
            text: Der gesprochene Text
            source_audio_path: Pfad zur Audio-Datei (wird in Katalog kopiert)
            tags: Liste von Schlagworten
            voice_model: Name des verwendeten Voice-Modells
            duration_seconds: length of the audio file in seconds
            
        Returns:
            ID der neuen Nachricht
        """
        # Audio-Datei in Katalog-Verzeichnis kopieren
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"msg_{timestamp}.wav"
        dest_path = os.path.join(self.audio_dir, filename)
        shutil.copy2(source_audio_path, dest_path)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert message
            cursor.execute('''
                INSERT INTO messages (text, audio_path, voice_model, duration_seconds)
                VALUES (?, ?, ?, ?)
            ''', (text, dest_path, voice_model, duration_seconds))
            
            message_id = cursor.lastrowid
            
            # Add tags
            if tags:
                for tag in tags:
                    tag = tag.strip().lower()
                    if tag:
                        # Tag erstellen falls nicht vorhanden
                        cursor.execute(
                            'INSERT OR IGNORE INTO tags (name) VALUES (?)', 
                            (tag,)
                        )
                        cursor.execute('SELECT id FROM tags WHERE name = ?', (tag,))
                        tag_id = cursor.fetchone()[0]
                        
                        # Create association
                        cursor.execute(
                            'INSERT OR IGNORE INTO message_tags (message_id, tag_id) VALUES (?, ?)',
                            (message_id, tag_id)
                        )
            
            conn.commit()
            return message_id
    
    def search(self, query: str = None, tags: List[str] = None,
               tag_mode: str = "and",
               favorites_only: bool = False, 
               order_by: str = "created_at",
               limit: int = 50) -> List[dict]:
        """
        Durchsucht den Katalog.
        
        Args:
            query: Suchtext (durchsucht den Text)
            tags: Filtere nach diesen Tags
            tag_mode: "and" = all tags must be present, "or" = at least one tag
            favorites_only: Nur Favoriten anzeigen
            order_by: Sortierung (created_at, play_count, last_played_at)
            limit: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste von Nachrichten als Dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Basis-Query
            if query and query.strip():
                # Bereinige Suchbegriff von FTS-Sonderzeichen
                clean_query = ''.join(c for c in query if c.isalnum() or c.isspace())
                clean_query = clean_query.strip()
                
                if clean_query:
                    # Volltextsuche mit Prefix im Text ODER Suche in Tags
                    sql = '''
                        SELECT m.*, GROUP_CONCAT(t.name) as tags_str
                        FROM messages m
                        LEFT JOIN message_tags mt ON m.id = mt.message_id
                        LEFT JOIN tags t ON mt.tag_id = t.id
                        WHERE (
                            m.id IN (
                                SELECT rowid FROM messages_fts WHERE messages_fts MATCH ?
                            )
                            OR m.id IN (
                                SELECT mt3.message_id FROM message_tags mt3
                                JOIN tags t3 ON mt3.tag_id = t3.id
                                WHERE t3.name LIKE ?
                            )
                        )
                    '''
                    params = [clean_query + '*', f'%{clean_query}%']  # Prefix-Suche im Text, LIKE in Tags
                else:
                    # Fallback to LIKE when no valid characters remain
                    sql = '''
                        SELECT m.*, GROUP_CONCAT(t.name) as tags_str
                        FROM messages m
                        LEFT JOIN message_tags mt ON m.id = mt.message_id
                        LEFT JOIN tags t ON mt.tag_id = t.id
                        WHERE (m.text LIKE ? OR m.id IN (
                            SELECT mt3.message_id FROM message_tags mt3
                            JOIN tags t3 ON mt3.tag_id = t3.id
                            WHERE t3.name LIKE ?
                        ))
                    '''
                    params = [f'%{query}%', f'%{query}%']
            else:
                sql = '''
                    SELECT m.*, GROUP_CONCAT(t.name) as tags_str
                    FROM messages m
                    LEFT JOIN message_tags mt ON m.id = mt.message_id
                    LEFT JOIN tags t ON mt.tag_id = t.id
                    WHERE 1=1
                '''
                params = []
            
            # Filter: Favoriten
            if favorites_only:
                sql += ' AND m.is_favorite = 1'
            
            # Filter: tags with AND or OR logic
            if tags:
                if tag_mode == "or":
                    # OR logic: at least one tag must be present
                    placeholders = ','.join(['?' for _ in tags])
                    sql += f'''
                        AND m.id IN (
                            SELECT mt2.message_id FROM message_tags mt2
                            JOIN tags t2 ON mt2.tag_id = t2.id
                            WHERE t2.name IN ({placeholders})
                        )
                    '''
                    params.extend([tag.strip().lower() for tag in tags])
                else:
                    # AND logic: all tags must be present
                    for tag in tags:
                        sql += '''
                            AND m.id IN (
                                SELECT mt2.message_id FROM message_tags mt2
                                JOIN tags t2 ON mt2.tag_id = t2.id
                                WHERE t2.name = ?
                            )
                        '''
                        params.append(tag.strip().lower())
            
            # Gruppierung und Sortierung
            sql += f' GROUP BY m.id ORDER BY m.{order_by} DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # In Dictionaries umwandeln
            results = []
            for row in rows:
                msg = dict(row)
                msg['tags'] = msg['tags_str'].split(',') if msg['tags_str'] else []
                del msg['tags_str']
                results.append(msg)
            
            return results
    
    def get_message(self, message_id: int) -> Optional[dict]:
        """Holt eine einzelne Nachricht."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.*, GROUP_CONCAT(t.name) as tags_str
                FROM messages m
                LEFT JOIN message_tags mt ON m.id = mt.message_id
                LEFT JOIN tags t ON mt.tag_id = t.id
                WHERE m.id = ?
                GROUP BY m.id
            ''', (message_id,))
            
            row = cursor.fetchone()
            if row:
                msg = dict(row)
                msg['tags'] = msg['tags_str'].split(',') if msg['tags_str'] else []
                del msg['tags_str']
                return msg
            return None
    
    def update_play_count(self, message_id: int):
        """Increments the play counter and sets last_played_at."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE messages 
                SET play_count = play_count + 1, last_played_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (message_id,))
            conn.commit()
    
    def toggle_favorite(self, message_id: int) -> bool:
        """Toggles favourite status. Returns new status."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE messages SET is_favorite = 1 - is_favorite WHERE id = ?',
                (message_id,)
            )
            cursor.execute('SELECT is_favorite FROM messages WHERE id = ?', (message_id,))
            result = cursor.fetchone()
            conn.commit()
            return bool(result[0]) if result else False
    
    def set_favorite(self, message_id: int, is_favorite: bool):
        """Setzt den Favoriten-Status direkt."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE messages SET is_favorite = ? WHERE id = ?',
                (1 if is_favorite else 0, message_id)
            )
            conn.commit()
    
    def update_tags(self, message_id: int, tags: List[str]):
        """Aktualisiert die Tags einer Nachricht."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Alte Tags entfernen
            cursor.execute('DELETE FROM message_tags WHERE message_id = ?', (message_id,))
            
            # Add new tags
            for tag in tags:
                tag = tag.strip().lower()
                if tag:
                    cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag,))
                    cursor.execute('SELECT id FROM tags WHERE name = ?', (tag,))
                    tag_id = cursor.fetchone()[0]
                    cursor.execute(
                        'INSERT INTO message_tags (message_id, tag_id) VALUES (?, ?)',
                        (message_id, tag_id)
                    )
            
            conn.commit()
    
    def delete_message(self, message_id: int):
        """Deletes a message and its audio file."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Audio-Pfad holen
            cursor.execute('SELECT audio_path FROM messages WHERE id = ?', (message_id,))
            result = cursor.fetchone()
            
            if result:
                audio_path = result[0]
                # Delete audio file
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                
                # Delete database entries (CASCADE also deletes message_tags)
                cursor.execute('DELETE FROM messages WHERE id = ?', (message_id,))
                conn.commit()
    
    def get_all_tags(self) -> List[Tuple[str, int]]:
        """
        Holt alle Tags mit Anzahl der Verwendungen.
        
        Returns:
            Liste von (tag_name, count) Tupeln
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.name, COUNT(mt.message_id) as count
                FROM tags t
                LEFT JOIN message_tags mt ON t.id = mt.tag_id
                GROUP BY t.id
                ORDER BY count DESC, t.name ASC
            ''')
            return cursor.fetchall()
    
    def get_recent_messages(self, limit: int = 10) -> List[dict]:
        """Holt die zuletzt erstellten Nachrichten."""
        return self.search(order_by="created_at", limit=limit)
    
    def get_frequent_messages(self, limit: int = 10) -> List[dict]:
        """Returns the most frequently played messages."""
        return self.search(order_by="play_count", limit=limit)
    
    def get_played_messages(self, limit: int = 10) -> List[dict]:
        """Holt die zuletzt abgespielten Nachrichten (nur die, die auch abgespielt wurden)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT m.*, GROUP_CONCAT(t.name) as tags_str
                FROM messages m
                LEFT JOIN message_tags mt ON m.id = mt.message_id
                LEFT JOIN tags t ON mt.tag_id = t.id
                WHERE m.play_count > 0
                GROUP BY m.id
                ORDER BY m.last_played_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            results = []
            for row in rows:
                msg = dict(row)
                msg['tags'] = msg['tags_str'].split(',') if msg['tags_str'] else []
                del msg['tags_str']
                results.append(msg)
            
            return results
    
    def add_to_playback_history(self, text: str, audio_url: str, catalog_id: int = None, embedding: np.ndarray = None):
        """
        Adds an entry to the playback history.
        
        Args:
            text: Der abgespielte Text
            audio_url: URL zur Audio-Datei
            catalog_id: Optional - ID der Katalog-Nachricht falls vorhanden
            embedding: Optional - vorberechnetes Embedding
        """
        emb_blob = embedding.astype(np.float32).tobytes() if embedding is not None else None
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO playback_history (text, audio_url, catalog_id, embedding)
                VALUES (?, ?, ?, ?)
            ''', (text, audio_url, catalog_id, emb_blob))
            conn.commit()
    
    def get_playback_history(self, limit: int = 10) -> List[dict]:
        """
        Holt den Wiedergabe-Verlauf.
        
        Returns:
            Liste der zuletzt abgespielten Nachrichten
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, text, audio_url, catalog_id, played_at
                FROM playback_history
                ORDER BY played_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_history_without_embeddings(self) -> List[dict]:
        """Returns all history entries without an embedding."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, text FROM playback_history
                WHERE embedding IS NULL
                ORDER BY id ASC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def update_embedding(self, history_id: int, embedding: np.ndarray):
        """Saves an embedding for a history entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE playback_history SET embedding = ? WHERE id = ?',
                (embedding.astype(np.float32).tobytes(), history_id)
            )
            conn.commit()
    
    def update_embeddings_batch(self, entries: List[Tuple[int, np.ndarray]]):
        """Saves embeddings for multiple entries at once."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                'UPDATE playback_history SET embedding = ? WHERE id = ?',
                [(emb.astype(np.float32).tobytes(), hid) for hid, emb in entries]
            )
            conn.commit()

    def search_similar(self, query_embedding: np.ndarray, limit: int = 3, min_similarity: float = 0.3) -> List[dict]:
        """Searches for semantically similar history entries using cosine similarity."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, text, embedding FROM playback_history
                WHERE embedding IS NOT NULL
            ''')
            
            q_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
            results = []
            seen_texts = set()
            
            for row in cursor:
                emb = np.frombuffer(row['embedding'], dtype=np.float32)
                similarity = float(np.dot(q_norm, emb / (np.linalg.norm(emb) + 1e-10)))
                text = row['text']
                if similarity >= min_similarity and text not in seen_texts and len(text.split()) > 3:
                    seen_texts.add(text)
                    results.append({'text': text, 'similarity': similarity})
            
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]

    def get_stats(self) -> dict:
        """Returns statistics about the catalog."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM messages')
            total_messages = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM tags')
            total_tags = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(play_count) FROM messages')
            total_plays = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT SUM(duration_seconds) FROM messages')
            total_duration = cursor.fetchone()[0] or 0
            
            return {
                'total_messages': total_messages,
                'total_tags': total_tags,
                'total_plays': total_plays,
                'total_duration_seconds': total_duration
            }


# Test
if __name__ == "__main__":
    catalog = MessageCatalog()
    
    print("Katalog initialisiert!")
    print(f"Datenbank: {catalog.db_path}")
    print(f"Audio-Ordner: {catalog.audio_dir}")
    print(f"Stats: {catalog.get_stats()}")
