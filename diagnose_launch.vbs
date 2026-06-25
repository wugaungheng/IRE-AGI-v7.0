' IRE-AGI v7.0 - Diagnostic Launcher
' Shows console output and captures errors
' Run THIS file to see exactly what goes wrong when launching

Option Explicit
On Error Resume Next

Dim ws, fso, exec, output, errOutput, logFile, logStream, errMsg, finished, i
Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

Dim scriptDir
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Log file path
logFile = scriptDir & "\diagnose_log.txt"

' Delete old log
If fso.FileExists(logFile) Then fso.DeleteFile logFile

' Find Python executable
Dim pythonExe, candidates(10), j
pythonExe = ""
candidates(0) = "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
candidates(1) = "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
candidates(2) = "C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"
candidates(3) = "C:\Python312\python.exe"
candidates(4) = "C:\Python313\python.exe"
candidates(5) = "C:\Python311\python.exe"

For j = 0 To 5
    If fso.FileExists(candidates(j)) Then
        pythonExe = candidates(j)
        Exit For
    End If
Next
If pythonExe = "" Then pythonExe = "python"

' Show what we found
Set logStream = fso.CreateTextFile(logFile, True)
logStream.WriteLine "=== IRE-AGI v7.0 Diagnostic Launch ==="
logStream.WriteLine "Time: " & Now()
logStream.WriteLine "Python used: " & pythonExe
logStream.WriteLine "Script dir: " & scriptDir
logStream.WriteLine ""

' Check if main script exists
If Not fso.FileExists(scriptDir & "\ire_agi_v7.py") Then
    logStream.WriteLine "ERROR: ire_agi_v7.py not found in " & scriptDir
    logStream.Close
    MsgBox "ERROR: ire_agi_v7.py not found in:" & vbCrLf & scriptDir, vbCritical, "Missing File"
    WScript.Quit
End If
logStream.WriteLine "ire_agi_v7.py: OK"
logStream.Close

' Launch Python WITH visible console (use Exec, not Run)
Err.Clear
Set exec = ws.Exec("""" & pythonExe & """ -u """ & scriptDir & "\ire_agi_v7.py""")
If Err.Number <> 0 Then
    errMsg = "Failed to launch Python!" & vbCrLf & _
             "Error: " & Err.Description & vbCrLf & vbCrLf & _
             "Tried: " & pythonExe & vbCrLf & vbCrLf & _
             "Please check that Python is installed correctly."
    MsgBox errMsg, vbCritical, "Launch Failed"
    WScript.Quit
End If

' Wait for process to start (up to 5 minutes for LLM loading)
finished = False
For i = 1 To 300
    If exec.Status <> 0 Then
        finished = True
        Exit For
    End If
    WScript.Sleep 1000
Next

' Read all output
output = exec.StdOut.ReadAll()
errOutput = exec.StdErr.ReadAll()

' Append to log
Set logStream = fso.OpenTextFile(logFile, 8, True)
If output <> "" Then
    logStream.WriteLine "--- STDOUT ---"
    logStream.WriteLine output
End If
If errOutput <> "" Then
    logStream.WriteLine "--- STDERR ---"
    logStream.WriteLine errOutput
End If
If output = "" And errOutput <> "" And Not finished Then
    logStream.WriteLine "(Still running after 5min - may be waiting for input)"
End If
logStream.WriteLine ""
logStream.WriteLine "Process status at end: " & CStr(finished)
logStream.WriteLine "Exit code: " & CStr(exec.ExitCode)
logStream.Close

' Build message for user
errMsg = "=== Diagnostic Result ===" & vbCrLf & vbCrLf
errMsg = errMsg & "Log file: " & logFile & vbCrLf & vbCrLf
errMsg = errMsg & "Python: " & pythonExe & vbCrLf

If output <> "" Then
    errMsg = errMsg & vbCrLf & "--- Output ---" & vbCrLf & Left(output, 2000) & vbCrLf
Else
    errMsg = errMsg & vbCrLf & "(No stdout)" & vbCrLf
End If

If errOutput <> "" Then
    errMsg = errMsg & vbCrLf & "--- Errors ---" & vbCrLf & Left(errOutput, 3000) & vbCrLf
Else
    errMsg = errMsg & vbCrLf & "(No stderr)" & vbCrLf
End If

If finished Then
    errMsg = errMsg & vbCrLf & "Process exited (code=" & CStr(exec.ExitCode) & ")"
Else
    errMsg = errMsg & vbCrLf & "Process still running after 5 min timeout."
End If

MsgBox errMsg, vbInformation, "IRE-AGI v7.0 Diagnostic Result"
