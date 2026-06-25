' IRE-AGI v7.0 - Launcher (Single Window, No Console)
' Uses pythonw.exe from the correct Python environment with CUDA + transformers + bitsandbytes.
' Named Mutex in Python handles single-instance detection.

Option Explicit
On Error Resume Next

Dim fso, ws
Set fso = CreateObject("Scripting.FileSystemObject")
Set ws = CreateObject("WScript.Shell")

' Get the folder this VBS is in
Dim scriptDir
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' === PREFERRED Python: conda environment with CUDA + transformers + bitsandbytes ===
Dim pythonw
pythonw = ""

' Priority 1: Conda distill environment (has all dependencies including bitsandbytes)
Dim condaPythonw
condaPythonw = "C:\ProgramData\miniconda3\envs\distill\pythonw.exe"
If fso.FileExists(condaPythonw) Then
    pythonw = condaPythonw
End If

' Priority 2: Managed Python 3.13 (has CUDA torch + transformers, but may lack bitsandbytes)
If pythonw = "" Then
    Dim managedPythonw
    managedPythonw = "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\pythonw.exe"
    If fso.FileExists(managedPythonw) Then
        pythonw = managedPythonw
    End If
End If

' Priority 3: System Python paths (may lack CUDA/transformers)
If pythonw = "" Then
    Dim tryPaths(5)
    tryPaths(0) = "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\pythonw.exe"
    tryPaths(1) = "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\pythonw.exe"
    tryPaths(2) = "C:\Users\Administrator\AppData\Local\Programs\Python\Python311\pythonw.exe"
    tryPaths(3) = "C:\Python312\pythonw.exe"
    tryPaths(4) = "C:\Python313\pythonw.exe"

    Dim i
    For i = 0 To 4
        If fso.FileExists(tryPaths(i)) Then
            pythonw = tryPaths(i)
            Exit For
        End If
    Next
End If

' Build command
Dim cmd
If pythonw <> "" Then
    cmd = """" & pythonw & """ -u """ & scriptDir & "\ire_agi_v7.py"""
Else
    cmd = "pythonw -u """ & scriptDir & "\ire_agi_v7.py"""
End If

' Launch: 0 = hidden window, False = don't wait
ws.Run cmd, 0, False

WScript.Quit
