' IRE-AGI v7.0 启动脚本
' 解决闪退问题：捕获所有错误并显示

Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Priority 1: Conda environment with all dependencies
Dim condaPython
condaPython = "C:\ProgramData\miniconda3\envs\distill\python.exe"
Dim pythonExe
If fso.FileExists(condaPython) Then
    pythonExe = condaPython
Else
    pythonExe = "python"
End If

logFile = scriptDir & "\error_log.txt"

' 删除旧日志
If fso.FileExists(logFile) Then fso.DeleteFile logFile

' 运行 Python，捕获输出
Set exec = ws.Exec("""" & pythonExe & """ """ & scriptDir & "\ire_agi_v7.py"" 2>&1")

' 等待程序完成或超时（最多等60秒看是否立即崩溃）
finished = False
For i = 1 To 60
    If exec.Status <> 0 Then
        finished = True
        Exit For
    End If
    WScript.Sleep 1000
Next

' 如果进程已经结束（闪退），读取错误信息
If finished Then
    output = exec.StdOut.ReadAll()
    errOutput = exec.StdErr.ReadAll()
    
    ' 写入日志文件
    Set logStream = fso.CreateTextFile(logFile, True)
    logStream.WriteLine "========== IRE-AGI v7.0 错误日志 =========="
    logStream.WriteLine "时间: " & Now()
    logStream.WriteLine ""
    If output <> "" Then
        logStream.WriteLine "--- 标准输出 ---"
        logStream.WriteLine output
    End If
    If errOutput <> "" Then
        logStream.WriteLine "--- 错误输出 ---"
        logStream.WriteLine errOutput
    End If
    If output = "" And errOutput = "" Then
        logStream.WriteLine "(无输出 - 可能是无声崩溃)"
    End If
    logStream.Close
    
    ' 显示错误
    errMsg = "IRE-AGI v7.0 启动失败！" & vbCrLf & vbCrLf
    If errOutput <> "" Then
        errMsg = errMsg & "错误信息：" & vbCrLf & Left(errOutput, 2000)
    ElseIf output <> "" Then
        errMsg = errMsg & "输出信息：" & vbCrLf & Left(output, 2000)
    Else
        errMsg = errMsg & "程序已退出，但没有产生任何输出。" & vbCrLf & _
                    "请查看 error_log.txt 获取详细信息。"
    End If
    errMsg = errMsg & vbCrLf & vbCrLf & "日志文件: " & logFile
    
    MsgBox errMsg, vbCritical, "IRE-AGI v7.0 启动错误"
End If
