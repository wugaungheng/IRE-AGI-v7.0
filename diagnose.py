"""
IRE-AGI v7.0 诊断脚本 - 逐步检测每个组件
运行这个来找出是什么导致闪退
"""

import sys
import os
import traceback

log_lines = []

def log(msg):
    log_lines.append(msg)
    print(msg)
    # 同时写入文件
    try:
        with open("diag_log.txt", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except:
        pass

log("=" * 60)
log("IRE-AGI v7.0 诊断脚本")
log(f"Python: {sys.version}")
log(f"平台: {sys.platform}")
log(f"工作目录: {os.getcwd()}")
log("")

# Step 1: 基础导入
try:
    log("[步骤1] 导入标准库...")
    import math, json, time, datetime
    log("  ✓ 标准库 OK")
except Exception as e:
    log(f"  ✗ 标准库失败: {e}")
    sys.exit(1)

# Step 2: NumPy
try:
    log("[步骤2] 导入 NumPy...")
    import numpy as np
    log(f"  ✓ NumPy {np.__version__} OK")
except Exception as e:
    log(f"  ✗ NumPy 失败: {e}")
    sys.exit(1)

# Step 3: PyTorch
try:
    log("[步骤3] 导入 PyTorch...")
    import torch
    log(f"  ✓ PyTorch {torch.__version__} OK")
    log(f"  CUDA: {torch.cuda.is_available()}")
except Exception as e:
    log(f"  ✗ PyTorch 失败: {e}")
    sys.exit(1)

# Step 4: tkinter
try:
    log("[步骤4] 导入 tkinter...")
    import tkinter as tk
    from tkinter import ttk
    log("  ✓ tkinter OK")
except Exception as e:
    log(f"  ✗ tkinter 失败: {e}")
    sys.exit(1)

# Step 5: 测试 tkinter 窗口
try:
    log("[步骤5] 创建测试窗口...")
    root = tk.Tk()
    root.title("IRE-AGI v7.0 诊断")
    root.geometry("600x400")
    
    text = tk.Text(root, wrap=tk.WORD)
    text.pack(fill=tk.BOTH, expand=True)
    text.insert(tk.END, "\n".join(log_lines))
    text.insert(tk.END, "\n\n✓ 所有组件正常！主程序应该能启动。")
    
    log("  ✓ 窗口创建成功！")
    log("")
    log("如果看到此窗口，说明所有依赖都正常。")
    log("问题可能在主程序的某个特定部分。")
    
    root.mainloop()
    
except Exception as e:
    log(f"  ✗ 窗口失败: {e}")
    traceback.print_exc()
    input("按回车退出...")
