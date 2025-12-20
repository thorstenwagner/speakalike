$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\SpeakAlike.lnk")
$Shortcut.TargetPath = "C:\Users\twagner\Projekte\fastspeak\start_electron.bat"
$Shortcut.WorkingDirectory = "C:\Users\twagner\Projekte\fastspeak"
$Shortcut.Description = "SpeakAlike - Voice Cloning TTS"
$Shortcut.Save()
Write-Host "Desktop-Verknuepfung 'SpeakAlike.lnk' wurde erstellt!"
