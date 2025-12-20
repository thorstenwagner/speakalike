"""
Erstellt ein Icon für SpeakAlike - Voice Cloning TTS App
Ein Mikrofon mit Schallwellen-Symbol
"""

from PIL import Image, ImageDraw
import os

def create_speakalike_icon():
    # Größen für ICO-Datei (mehrere Auflösungen)
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        # Erstelle ein neues Bild mit transparentem Hintergrund
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Skalierungsfaktor
        s = size / 256
        
        # Hintergrund: Abgerundetes Rechteck (Kreis als Basis)
        # Gradient-ähnlicher Effekt mit zwei Farben
        # Hauptfarbe: Blau-Violett (#6366F1 -> #8B5CF6)
        primary_color = (99, 102, 241)  # Indigo
        secondary_color = (139, 92, 246)  # Violett
        
        # Zeichne Hintergrundkreis
        padding = int(10 * s)
        draw.ellipse([padding, padding, size - padding, size - padding], 
                     fill=primary_color)
        
        # Mikrofon-Körper (Oval)
        mic_width = int(60 * s)
        mic_height = int(90 * s)
        mic_x = (size - mic_width) // 2
        mic_y = int(50 * s)
        
        # Mikrofon-Kopf (weißes Oval)
        draw.ellipse([mic_x, mic_y, mic_x + mic_width, mic_y + mic_height], 
                     fill='white')
        
        # Mikrofon-Ständer (Linie nach unten)
        stand_width = int(8 * s)
        stand_x = (size - stand_width) // 2
        stand_top = mic_y + mic_height - int(15 * s)
        stand_bottom = int(180 * s)
        draw.rectangle([stand_x, stand_top, stand_x + stand_width, stand_bottom], 
                       fill='white')
        
        # Mikrofon-Basis (horizontale Linie)
        base_width = int(50 * s)
        base_height = int(8 * s)
        base_x = (size - base_width) // 2
        base_y = stand_bottom - int(4 * s)
        draw.ellipse([base_x, base_y, base_x + base_width, base_y + base_height], 
                     fill='white')
        
        # Schallwellen rechts vom Mikrofon
        wave_color = (255, 255, 255, 200)  # Weiß, leicht transparent
        center_y = mic_y + mic_height // 2
        wave_x_start = mic_x + mic_width + int(15 * s)
        
        for i, offset in enumerate([0, 20, 40]):
            wave_x = wave_x_start + int(offset * s)
            wave_height = int((30 + i * 15) * s)
            line_width = max(2, int(4 * s))
            
            # Zeichne Bogen (Arc)
            bbox = [wave_x, center_y - wave_height, 
                    wave_x + int(20 * s), center_y + wave_height]
            if bbox[2] < size - padding and bbox[0] > 0:
                draw.arc(bbox, start=-60, end=60, fill='white', width=line_width)
        
        # Schallwellen links vom Mikrofon (gespiegelt)
        for i, offset in enumerate([0, 20, 40]):
            wave_x = mic_x - int(15 * s) - int(offset * s) - int(20 * s)
            wave_height = int((30 + i * 15) * s)
            line_width = max(2, int(4 * s))
            
            bbox = [wave_x, center_y - wave_height, 
                    wave_x + int(20 * s), center_y + wave_height]
            if bbox[0] > padding and bbox[2] < size:
                draw.arc(bbox, start=120, end=240, fill='white', width=line_width)
        
        images.append(img)
    
    # Speichere als ICO
    icons_dir = r'c:\Users\twagner\Projekte\fastspeak\electron-app\icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    ico_path = os.path.join(icons_dir, 'icon.ico')
    png_path = os.path.join(icons_dir, 'icon.png')
    
    # Speichere ICO mit allen Größen
    images[-1].save(ico_path, format='ICO', sizes=[(s, s) for s in sizes])
    
    # Speichere auch PNG (256x256)
    images[-1].save(png_path, format='PNG')
    
    print(f"Icon erstellt: {ico_path}")
    print(f"PNG erstellt: {png_path}")
    return ico_path

if __name__ == '__main__':
    ico_path = create_speakalike_icon()
    
    # Aktualisiere die Desktop-Verknüpfung mit dem neuen Icon
    import subprocess
    ps_script = f'''
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\\Desktop\\SpeakAlike.lnk")
    $Shortcut.IconLocation = "{ico_path},0"
    $Shortcut.Save()
    Write-Host "Verknuepfung mit Icon aktualisiert!"
    '''
    subprocess.run(['powershell', '-Command', ps_script], check=True)
