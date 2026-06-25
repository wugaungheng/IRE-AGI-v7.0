Set ws = CreateObject("WScript.Shell")
ws.Environment("PROCESS")("HF_ENDPOINT") = "https://hf-mirror.com"
ws.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
ws.Run """C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"" ire_agi_v5.py", 0, False
