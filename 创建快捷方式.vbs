Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

desktop = ws.SpecialFolders("Desktop")
Set lnk = ws.CreateShortcut(desktop & "\IRE-AGI.lnk")
lnk.TargetPath = "wscript.exe"
lnk.Arguments = """" & fso.GetParentFolderName(WScript.ScriptFullName) & "\启动IRE-AGI.vbs"""
lnk.WorkingDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
lnk.Description = "IRE-AGI v4.0 自我演化引擎"
lnk.Save
