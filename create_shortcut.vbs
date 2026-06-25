Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oShortcut = WshShell.CreateShortcut(strDesktop & "\IRE-AGI-v7.lnk")
oShortcut.TargetPath = "C:\Users\Administrator\Desktop\IRE-AGI\start_v7.bat"
oShortcut.WorkingDirectory = "C:\Users\Administrator\Desktop\IRE-AGI"
oShortcut.Description = "IRE-AGI v7.0"
oShortcut.IconLocation = "shell32.dll,13"
oShortcut.Save
MsgBox "Desktop shortcut created: IRE-AGI-v7.lnk", vbInformation, "Done"
