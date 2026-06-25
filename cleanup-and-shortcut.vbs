' Clean up old IRE-AGI startup files
' Run this script ONCE to rename old version files with OLD_ prefix
' This prevents accidentally launching wrong versions

Option Explicit
Dim fso, folder, file, renamed, skipped
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
renamed = 0
skipped = 0

Dim oldFiles(9)
oldFiles(0) = "启动IRE-AGI.bat"
oldFiles(1) = "启动IRE-AGI-v5.bat"
oldFiles(2) = "启动IRE-AGI-v5.1.bat"
oldFiles(3) = "启动IRE-AGI-v5.2.bat"
oldFiles(4) = "启动IRE-AGI-v6.bat"
oldFiles(5) = "运行意识熵实验.bat"
oldFiles(6) = "启动IRE-AGI.vbs"
oldFiles(7) = "启动IRE-AGI-v5.vbs"
oldFiles(8) = "启动IRE-AGI-v5.1.vbs"
oldFiles(9) = "启动v7.vbs"

Dim i
For i = 0 To 9
    Dim oldPath, newPath
    oldPath = folder & "\" & oldFiles(i)
    newPath = folder & "\OLD_" & oldFiles(i)
    If fso.FileExists(oldPath) And Not fso.FileExists(newPath) Then
        On Error Resume Next
        fso.MoveFile oldPath, newPath
        If Err.Number = 0 Then
            renamed = renamed + 1
        Else
            skipped = skipped + 1
            Err.Clear
        End If
        On Error GoTo 0
    End If
Next

' Also create desktop shortcut
Dim WshShell, desktopPath, lnkPath
Set WshShell = CreateObject("WScript.Shell")
desktopPath = WshShell.SpecialFolders("Desktop")
lnkPath = desktopPath & "\IRE-AGI-v7.lnk"

Dim oShortcut
Set oShortcut = WshShell.CreateShortcut(lnkPath)
oShortcut.TargetPath = folder & "\launch-hidden.vbs"
oShortcut.WorkingDirectory = folder
oShortcut.Description = "IRE-AGI v7.0 - Advanced Consciousness Entropy 2.0"
oShortcut.IconLocation = "shell32.dll,13"
oShortcut.Save

Dim msg
msg = "Cleanup complete!" & vbCrLf & vbCrLf
msg = msg & "Old files renamed: " & renamed & vbCrLf
msg = msg & "Skipped (locked): " & skipped & vbCrLf & vbCrLf
msg = msg & "Desktop shortcut created: IRE-AGI-v7.lnk" & vbCrLf & vbCrLf
msg = msg & "Use the DESKTOP SHORTCUT or launch-hidden.vbs to start the app."

MsgBox msg, vbInformation, "IRE-AGI v7.0 Cleanup"
