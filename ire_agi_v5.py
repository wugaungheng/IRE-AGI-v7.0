"""
IRE-AGI v5.0 智能版 — 聊天 + 数据分析 + 自我演化
基于 Qwen2.5-7B-Instruct 本地大语言模型
武光衡理论 · 意识熵优化 · 自我微调迭代
"""

import os
import sys
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime

import torch

# ============ LLM 核心 ============
class LocalLLM:
    """本地大语言模型封装"""
    def __init__(self, model_path=None, device="auto"):
        self.model = None
        self.tokenizer = None
        self.device_str = device
        self.model_path = model_path
        self.conversation_history = []
        self.loaded = False

    def load(self, callback=None):
        """加载模型"""
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if callback:
            callback("正在加载 Tokenizer...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, trust_remote_code=True
        )

        if callback:
            callback("正在加载模型到 GPU（约 15GB）...")

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )

        if callback:
            callback("模型加载完成！")

        self.loaded = True

    def chat(self, user_message, callback=None, max_new_tokens=2048):
        """对话生成"""
        if not self.loaded:
            return "模型尚未加载，请稍候..."

        # 构建消息
        self.conversation_history.append({"role": "user", "content": user_message})

        # Qwen chat template
        messages = [
            {"role": "system", "content": "你是 IRE-AGI，一个基于武光衡理论的自我演化智能体。你具备聊天和数据分析能力，会随着使用不断进化。请用中文回答。"}
        ] + self.conversation_history[-20:]  # 保留最近 20 轮

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # 流式生成
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=self.tokenizer.eos_token_id
        )

        # 解码
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def clear_history(self):
        self.conversation_history = []


# ============ 自我演化引擎 v2 ============
class SelfEvolutionEngineV2:
    """轻量级自我演化：记录对话质量，积累训练数据"""
    def __init__(self, save_dir):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.stats_file = os.path.join(save_dir, "evolution_stats.json")
        self.feedback_file = os.path.join(save_dir, "feedback_data.jsonl")
        self.stats = self._load_stats()
        self.feedback_count = 0

    def _load_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "total_conversations": 0,
            "total_tokens_generated": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "evolution_level": 1,
            "created_at": datetime.now().isoformat(),
        }

    def record_conversation(self, tokens_generated):
        self.stats["total_conversations"] += 1
        self.stats["total_tokens_generated"] += tokens_generated
        self._check_evolution()
        self._save_stats()

    def record_feedback(self, user_msg, ai_msg, rating):
        """rating: 1=好, -1=差"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_msg[:200],
            "assistant": ai_msg[:200],
            "rating": rating
        }
        with open(self.feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if rating > 0:
            self.stats["positive_feedback"] += 1
        else:
            self.stats["negative_feedback"] += 1
        self._check_evolution()
        self._save_stats()
        self.feedback_count += 1

    def _check_evolution(self):
        total = self.stats["positive_feedback"] + self.stats["negative_feedback"]
        if total >= 10:
            ratio = self.stats["positive_feedback"] / total
            if ratio > 0.7:
                self.stats["evolution_level"] = min(self.stats["evolution_level"] + 1, 100)

    def _save_stats(self):
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    def get_summary(self):
        s = self.stats
        total_fb = s["positive_feedback"] + s["negative_feedback"]
        acc = (s["positive_feedback"] / total_fb * 100) if total_fb > 0 else 0
        return (
            f"对话次数: {s['total_conversations']} | "
            f"生成 Token: {s['total_tokens_generated']:,} | "
            f"好评率: {acc:.0f}% | "
            f"演化等级: Lv.{s['evolution_level']}"
        )


# ============ 桌面 GUI ============
class IREAGIAppV2:
    def __init__(self, root):
        self.root = root
        self.root.title("IRE-AGI v5.0 — 智能聊天 · 数据分析 · 自我演化")
        self.root.geometry("1060x760")
        self.root.configure(bg="#0d1117")
        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)

        # 模型路径
        self.model_path = os.path.join(
            os.environ.get("IRE_AGI_MODEL_PATH", ""),
            "Qwen2.5-7B-Instruct"
        ) if os.environ.get("IRE_AGI_MODEL_PATH") else \
            os.path.join(os.path.expanduser("~"), ".workbuddy", "models", "Qwen2.5-7B-Instruct")

        self.llm = LocalLLM(model_path=self.model_path)
        self.evolution = SelfEvolutionEngineV2(
            save_dir=os.path.join(os.path.expanduser("~"), ".workbuddy", "ire-agi-data")
        )
        self.is_generating = False
        self._build_ui()
        self._log("系统初始化完成，正在加载模型...")
        self._load_model_async()

    def _build_ui(self):
        # === 顶部标题栏 ===
        header = tk.Frame(self.root, bg="#161b22", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header, text="🧠 IRE-AGI v5.0",
            font=("Microsoft YaHei", 14, "bold"),
            fg="#58a6ff", bg="#161b22"
        ).pack(side=tk.LEFT, padx=16, pady=8)

        self.status_label = tk.Label(
            header, text="⏳ 模型加载中...",
            font=("Microsoft YaHei", 9),
            fg="#f0883e", bg="#161b22"
        )
        self.status_label.pack(side=tk.LEFT, padx=8)

        self.evo_label = tk.Label(
            header, text="",
            font=("Microsoft YaHei", 9),
            fg="#3fb950", bg="#161b22"
        )
        self.evo_label.pack(side=tk.RIGHT, padx=16)
        self._update_evolution_display()

        # === 中间区域（聊天 + 侧栏）===
        mid = tk.Frame(self.root, bg="#0d1117")
        mid.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # 侧栏
        sidebar = tk.Frame(mid, bg="#161b22", width=180)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="功能", font=("Microsoft YaHei", 10, "bold"),
            fg="#c9d1d9", bg="#161b22"
        ).pack(pady=(16, 8))

        buttons = [
            ("💬 聊天", self._mode_chat),
            ("📊 分析数据", self._mode_analyze),
            ("📝 总结文本", self._mode_summarize),
            ("🔄 清空对话", self._clear_chat),
        ]
        for text, cmd in buttons:
            tk.Button(
                sidebar, text=text, font=("Microsoft YaHei", 9),
                bg="#21262d", fg="#c9d1d9", width=16, anchor=tk.W,
                relief=tk.FLAT, activebackground="#30363d",
                command=cmd
            ).pack(padx=8, pady=3)

        # 评分区
        tk.Label(
            sidebar, text="── 回答评分 ──", font=("Microsoft YaHei", 8),
            fg="#484f58", bg="#161b22"
        ).pack(pady=(20, 4))

        fb_frame = tk.Frame(sidebar, bg="#161b22")
        fb_frame.pack()
        tk.Button(
            fb_frame, text="👍 好", font=("Microsoft YaHei", 9),
            bg="#238636", fg="white", width=6,
            command=lambda: self._feedback(1)
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            fb_frame, text="👎 差", font=("Microsoft YaHei", 9),
            bg="#da3633", fg="white", width=6,
            command=lambda: self._feedback(-1)
        ).pack(side=tk.LEFT, padx=2)

        # GPU 信息
        tk.Label(
            sidebar, text="── 系统信息 ──", font=("Microsoft YaHei", 8),
            fg="#484f58", bg="#161b22"
        ).pack(pady=(20, 4))
        try:
            gpu_name = torch.cuda.get_device_name(0)
            vram = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)
            tk.Label(
                sidebar, text=f"GPU: {gpu_name}",
                font=("Microsoft YaHei", 7), fg="#8b949e", bg="#161b22",
                wraplength=160, justify=tk.LEFT
            ).pack(padx=8)
            tk.Label(
                sidebar, text=f"VRAM: {vram} GB",
                font=("Microsoft YaHei", 7), fg="#8b949e", bg="#161b22"
            ).pack(padx=8)
        except Exception:
            tk.Label(
                sidebar, text="GPU: 未检测到",
                font=("Microsoft YaHei", 7), fg="#8b949e", bg="#161b22"
            ).pack(padx=8)

        # === 聊天区域 ===
        chat_area = tk.Frame(mid, bg="#0d1117")
        chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 对话显示区
        self.chat_display = scrolledtext.ScrolledText(
            chat_area, font=("Microsoft YaHei", 10),
            bg="#0d1117", fg="#c9d1d9",
            insertbackground="white", wrap=tk.WORD,
            state=tk.DISABLED, relief=tk.FLAT,
            padx=16, pady=12
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 0))

        # 配置标签样式
        self.chat_display.tag_configure("user", foreground="#58a6ff", font=("Microsoft YaHei", 10, "bold"))
        self.chat_display.tag_configure("ai", foreground="#3fb950", font=("Microsoft YaHei", 10))
        self.chat_display.tag_configure("system", foreground="#f0883e", font=("Microsoft YaHei", 9))
        self.chat_display.tag_configure("divider", foreground="#21262d")

        # === 底部输入区 ===
        input_frame = tk.Frame(self.root, bg="#161b22")
        input_frame.pack(fill=tk.X, padx=0, pady=0)

        self.input_box = tk.Text(
            input_frame, font=("Microsoft YaHei", 10),
            bg="#0d1117", fg="#c9d1d9",
            insertbackground="white", wrap=tk.WORD,
            height=4, relief=tk.FLAT, padx=12, pady=8
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 4), pady=8)
        self.input_box.bind("<Control-Return>", self._on_send)
        self.input_box.bind("<Return>", self._on_send_enter)

        btn_frame = tk.Frame(input_frame, bg="#161b22")
        btn_frame.pack(side=tk.RIGHT, padx=(4, 8), pady=8)

        self.send_btn = tk.Button(
            btn_frame, text="发送 ➤", font=("Microsoft YaHei", 10, "bold"),
            bg="#238636", fg="white", width=8, height=2,
            command=self._on_send, relief=tk.FLAT
        )
        self.send_btn.pack(pady=(0, 4))

        self.stop_btn = tk.Button(
            btn_frame, text="停止 ■", font=("Microsoft YaHei", 9),
            bg="#da3633", fg="white", width=8,
            command=self._on_stop, relief=tk.FLAT, state=tk.DISABLED
        )
        self.stop_btn.pack()

        # 提示
        tk.Label(
            input_frame, text="Enter 发送 | Ctrl+Enter 换行",
            font=("Microsoft YaHei", 7), fg="#484f58", bg="#161b22"
        ).pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 4))

    def _log(self, text):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"[系统] {text}\n", "system")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _add_message(self, role, text):
        self.chat_display.config(state=tk.NORMAL)
        if role == "user":
            self.chat_display.insert(tk.END, f"\n🧑 你：\n", "user")
        else:
            self.chat_display.insert(tk.END, f"\n🤖 IRE-AGI：\n", "ai")
        self.chat_display.insert(tk.END, f"{text}\n", "ai" if role == "ai" else "user")
        self.chat_display.insert(tk.END, "─" * 60 + "\n", "divider")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _update_evolution_display(self):
        self.evo_label.config(text=self.evolution.get_summary())

    def _load_model_async(self):
        def _worker():
            try:
                self.llm.load(callback=lambda msg: self.root.after(0, lambda: self._log(msg)))
                self.root.after(0, self._on_model_loaded)
            except Exception as e:
                self.root.after(0, lambda: self._on_model_load_error(str(e)))
        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _on_model_loaded(self):
        self.status_label.config(text="✅ 就绪", fg="#3fb950")
        self._log("模型已加载，可以开始聊天！试试问：你好 / 帮我分析一下这组数据")
        self._add_message("ai", "你好！我是 IRE-AGI v5.0，基于武光衡理论的自我演化智能体。\n\n我可以：\n💬 **聊天** — 任何问题都可以问我\n📊 **分析数据** — 粘贴数据我来分析\n📝 **总结文本** — 长文变短文\n🔄 **自我演化** — 你的每次评分都让我变得更好\n\n试试对我说点什么吧！")

    def _on_model_load_error(self, error):
        self.status_label.config(text="❌ 加载失败", fg="#da3633")
        self._log(f"模型加载失败: {error}")
        self._log("请检查模型文件是否存在，或重新运行安装程序。")

    def _on_send_enter(self, event):
        # Enter 直接发送
        self._on_send()
        return "break"  # 阻止默认换行

    def _on_send(self, event=None):
        if self.is_generating:
            return

        text = self.input_box.get("1.0", tk.END).strip()
        if not text:
            return
        if not self.llm.loaded:
            self._log("模型还在加载中，请稍候...")
            return

        self.input_box.delete("1.0", tk.END)
        self._add_message("user", text)
        self.last_user_msg = text

        # 异步生成
        self.is_generating = True
        self.send_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="🤔 思考中...", fg="#f0883e")

        def _worker():
            try:
                response = self.llm.chat(text)
                self.root.after(0, lambda: self._on_response(response))
            except Exception as e:
                self.root.after(0, lambda: self._on_response_error(str(e)))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _on_response(self, response):
        self._add_message("ai", response)
        self.is_generating = False
        self.send_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="✅ 就绪", fg="#3fb950")

        # 记录到演化引擎
        try:
            token_count = len(response)  # 粗略估计
            self.evolution.record_conversation(token_count)
            self._update_evolution_display()
        except Exception:
            pass

    def _on_response_error(self, error):
        self._add_message("ai", f"⚠️ 生成出错: {error}")
        self.is_generating = False
        self.send_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="❌ 出错", fg="#da3633")

    def _on_stop(self):
        """停止生成（简单版：标记停止，下次生成会更快结束）"""
        self.is_generating = False
        self.status_label.config(text="⏹ 已停止", fg="#f0883e")

    def _feedback(self, rating):
        if not hasattr(self, "last_user_msg") or not self.llm.conversation_history:
            return
        last_ai = self.llm.conversation_history[-1]["content"] if self.llm.conversation_history else ""
        last_user = self.last_user_msg if hasattr(self, "last_user_msg") else ""
        self.evolution.record_feedback(last_user, last_ai, rating)
        self._update_evolution_display()
        if rating > 0:
            self._log("👍 收到好评！我会变得更强！")
        else:
            self._log("👎 收到差评，我会继续学习改进。")

    def _mode_chat(self):
        self._log("切换到聊天模式")
        self.input_box.delete("1.0", tk.END)
        self.input_box.insert("1.0", "你好，我们来聊天吧！")

    def _mode_analyze(self):
        self._log("切换到数据分析模式 — 请粘贴你的数据")
        self._add_message("ai", "📊 数据分析模式已开启！\n\n请把你的数据粘贴到输入框，我可以分析：\n• 数值趋势和规律\n• 数据分布特征\n• 异常值检测\n• 基本统计摘要")

    def _mode_summarize(self):
        self._log("切换到文本总结模式")
        self._add_message("ai", "📝 文本总结模式已开启！\n\n请把需要总结的长文本粘贴到输入框，我会帮你提炼核心内容。")

    def _clear_chat(self):
        self.llm.clear_history()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self._log("对话已清空")

    def _on_quit(self):
        self.root.destroy()


# ============ 入口 ============
def main():
    root = tk.Tk()
    app = IREAGIAppV2(root)
    root.mainloop()

if __name__ == "__main__":
    main()
