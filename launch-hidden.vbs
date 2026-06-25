' IRE-AGI v7.0 Launcher - SINGLE INSTANCE
' This is the ONLY correct way to start IRE-AGI v7.0

Option Explicit
On Error Resume Next

Dim WshShell, fso
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Dim scriptDir
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

' === Check 1: Does window already exist? ===
If WshShell.AppActivate("IRE-AGI v7.0") Then
    WScript.Sleep 200
    MsgBox "IRE-AGI v7.0 is already running!" & vbCrLf & vbCrLf & "Only one instance is allowed.", vbInformation, "IRE-AGI v7.0"
    WScript.Quit
End If

' === Check 2: Try to delete stale lock file ===
Dim lockPath
lockPath = fso.GetSpecialFolder(2) & "\ire_agi_v7.lock"
If fso.FileExists(lockPath) Then
    On Error Resume Next
    fso.DeleteFile lockPath
    If Err.Number = 70 Then
        ' Permission denied = another instance holds the lock
        MsgBox "IRE-AGI v7.0 is already running!" & vbCrLf & "(Lock file is held by another process)", vbInformation, "IRE-AGI v7.0"
        WScript.Quit
    End If
    Err.Clear
    On Error GoTo 0
End If

' === All checks passed, launch the app ===
' Use pythonw (no console window)
WshShell.Run "pythonw -u """ & scriptDir & "\ire_agi_v7.py""", 0, False

If Err.Number <> 0 Then
    ' pythonw not found, try python
    Err.Clear
    WshShell.Run "python -u """ & scriptDir & "\ire_agi_v7.py""", 1, False
End If
