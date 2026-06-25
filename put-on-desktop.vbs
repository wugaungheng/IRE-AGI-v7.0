Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")

' Create shortcut
Set oShortcut = WshShell.CreateShortcut(strDesktop & "\IRE-AGI-v7.lnk")
oShortcut.TargetPath = "python"
oShortcut.Arguments = "-u ""C:\Users\Administrator\Desktop\IRE-AGI\ire_agi_v7.py"""
oShortcut.WorkingDirectory = "C:\Users\Administrator\Desktop\IRE-AGI"
oShortcut.Description = "IRE-AGI v7.0 - Start"
oShortcut.IconLocation = "system32\imageres.dll,1"
oShortcut.Save()

' Also create a bat on desktop
Dim fso, batFile
Set fso = CreateObject("Scripting.FileSystemObject")
batPath = strDesktop & "\start-IRE.bat"
Set batFile = fso.CreateTextFile(batPath, True)
batLine1 = "@echo off"
batLine2 = "cd /d C:\Users\Administrator\Desktop\IRE-AGI"
batLine3 = "python -u ire_agi_v7.py"
batLine4 = "pause"
batFile.WriteLine batLine1
batFile.WriteLine batLine2
batFile.WriteLine batLine3
batFile.WriteLine batLine4
batFile.Close

MsgBox "Done!" & vbCrLf & vbCrLf & _
       "Desktop files created:" & vbCrLf & _
       "  1) IRE-AGI-v7.lnk (shortcut)" & vbCrLf & _
       "  2) start-IRE.bat (batch)" & vbCrLf & vbCrLf & _
       "Double-click either one to start!", vbInformation, "IRE-AGI v7"
