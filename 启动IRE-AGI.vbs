Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
ws.Run """C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"" ire_agi.py --gui", 0, False
