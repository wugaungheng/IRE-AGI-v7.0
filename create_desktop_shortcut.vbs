Set WshShell = CreateObject("WScript.Shell")
DesktopPath = WshShell.SpecialFolders("Desktop")

' 创建快捷方式
Set shortcut = WshShell.CreateShortcut(DesktopPath & "\IRE-AGI-v7.lnk")
shortcut.TargetPath = "C:\Users\Administrator\Desktop\IRE-AGI\start_v7.bat"
shortcut.WorkingDirectory = "C:\Users\Administrator\Desktop\IRE-AGI"
shortcut.Description = "IRE-AGI v7.0 高级意识熵"
shortcut.Save

MsgBox "桌面快捷方式已创建！" & vbCrLf & vbCrLf & "请在桌面找 ""IRE-AGI-v7.lnk""", vbInformation, "完成"
