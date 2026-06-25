Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\Administrator\Desktop\IRE-AGI"
' Use conda Python with all dependencies (CUDA + transformers + bitsandbytes)
' Fallback to pythonw if conda not available
Dim fso, pythonPath
Set fso = CreateObject("Scripting.FileSystemObject")
pythonPath = "C:\ProgramData\miniconda3\envs\distill\pythonw.exe"
If Not fso.FileExists(pythonPath) Then
    pythonPath = "pythonw"
End If
WshShell.Run """" & pythonPath & """ -u ire_agi_v7.py", 0, False
