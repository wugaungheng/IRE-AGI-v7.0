' Create desktop shortcut for IRE-AGI v7.0
Option Explicit

Dim ws, fso, desktop, shortcut
Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Dim scriptDir
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

desktop = ws.SpecialFolders("Desktop")
Set shortcut = ws.CreateShortcut(desktop & "\IRE-AGI v7.0.lnk")
shortcut.TargetPath = "wscript.exe"
shortcut.Arguments = """" & scriptDir & "\fix_and_start.vbs"""
shortcut.WorkingDirectory = scriptDir
shortcut.Description = "IRE-AGI v7.0 - Advanced Consciousness Entropy 2.0"
shortcut.IconLocation = "C:\Windows\System32\shell32.dll,13"
shortcut.WindowStyle = 1
shortcut.Save

MsgBox "Shortcut created on Desktop: IRE-AGI v7.0.lnk" & vbCrLf & vbCrLf & "Double-click it to launch IRE-AGI v7.0!", vbInformation, "Done"
