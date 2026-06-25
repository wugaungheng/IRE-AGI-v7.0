"""
IRE-AGI v5.1 智能版 — 聊天 + 数据分析 + 自我演化
基于 Qwen2.5-7B-Instruct 本地大语言模型

v5.1 新增:
- 复制按钮 (每条AI回复旁一键复制)
- 右键菜单 (复制/粘贴/全选)
- 导出对话 (保存为TXT/Markdown)
- 对话历史管理
- 快捷键优化
- UI 美化
"""

import os
import sys
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, Menu
from datetime import datetime
from pathlib import Path

import torch


# ============ LLM 核心 ============
class LocalLLM:
    """Local LLM wrapper"""

    def __init__(self, model_path=None, device="auto"):
        self.model = None
        self.tokenizer = None
        self.device_str = device
        self.model_path = model_path or os.path.join(
            os.path.expanduser("~"), ".workbuddy", "models", "Qwen2.5-7B-Instruct"
        )
        self.conversation_history = []
        self.loaded = False
        self.stop_flag = False

    def load(self, callback=None):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if callback:
            callback("Loading Tokenizer...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, trust_remote_code=True
        )

        if callback:
            callback("Loading model to GPU (~15GB)...")

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )

        if callback:
            callback("Model loaded!")

        self.loaded = True

    def chat(self, user_message, max_new_tokens=2048):
        if not self.loaded:
            return "Model not loaded yet..."

        self.conversation_history.append({"role": "user", "content": user_message})

        messages = [
            {"role": "system", "content": "You are IRE-AGI, a self-evolving AI based on consciousness theory. You can chat and analyze data, and you evolve through interaction. Respond in Chinese."}
        ] + self.conversation_history[-20:]

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=self.tokenizer.eos_token_id
        )

        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def clear_history(self):
        self.conversation_history = []


# ============ Self-Evolution Engine v2 ============
class SelfEvolutionEngineV2:
    """Lightweight evolution: track conversation quality, accumulate training data"""

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
            f"Chats: {s['total_conversations']} | "
            f"Tokens: {s['total_tokens_generated']:,} | "
            f"Good: {acc:.0f}% | "
            f"Lv.{s['evolution_level']}"
        )


# ============ Enhanced GUI with Copy/Paste ============
class IREAGIAppV51:
    def __init__(self, root):
        self.root = root
        self.root.title("IRE-AGI v5.1 - Smart Chat / Data Analysis / Self-Evolution")
        self.root.geometry("1100x780")
        self.root.configure(bg="#0d1117")
        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)

        # Model path
        self.model_path = os.path.join(
            os.path.expanduser("~"), ".workbuddy", "models", "Qwen2.5-7B-Instruct"
        )

        # Core components
        self.llm = LocalLLM(model_path=self.model_path)
        self.evolution = SelfEvolutionEngineV2(
            save_dir=os.path.join(os.path.expanduser("~"), ".workbuddy", "ire-agi-data")
        )
        self.is_generating = False
        self.last_user_msg = ""
        self.last_ai_msg = ""

        # Conversation storage for export/copy
        self.messages = []  # list of {"role": "user"/"ai"/"system", "text": str}

        self._build_ui()
        self._log("System initializing, loading model...")
        self._load_model_async()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        # ===== Header =====
        header = tk.Frame(self.root, bg="#161b22", height=52)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg="#161b22")
        title_frame.pack(side=tk.LEFT, padx=16, pady=8)

        tk.Label(
            title_frame, text="IRE-AGI v5.1",
            font=("Segoe UI", 15, "bold"),
            fg="#58a6ff", bg="#161b22"
        ).pack(side=tk.LEFT)

        self.status_label = tk.Label(
            header, text="Loading model...",
            font=("Segoe UI", 9),
            fg="#f0883e", bg="#161b22"
        )
        self.status_label.pack(side=tk.LEFT, padx=12)

        # Export button in header
        export_btn = tk.Button(
            header, text="Export Chat", font=("Segoe UI", 8),
            bg="#21262d", fg="#c9d1d9", relief=tk.FLAT,
            activebackground="#30363d", command=self._export_chat
        )
        export_btn.pack(side=tk.RIGHT, padx=(0, 16))

        self.evo_label = tk.Label(
            header, text="",
            font=("Segoe UI", 9), fg="#3fb950", bg="#161b22"
        )
        self.evo_label.pack(side=tk.RIGHT, padx=8)
        self._update_evolution_display()

        # ===== Main area =====
        mid = tk.Frame(self.root, bg="#0d1117")
        mid.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar = tk.Frame(mid, bg="#161b22", width=190)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="Functions", font=("Segoe UI", 10, "bold"),
            fg="#c9d1d9", bg="#161b22"
        ).pack(pady=(18, 10))

        btn_cfgs = [
            ("Chat", self._mode_chat, "#1f6feb"),
            ("Analyze Data", self._mode_analyze, "#1f6feb"),
            ("Summarize Text", self._mode_summarize, "#1f6feb"),
            ("Clear Chat", self._clear_chat, "#da3633"),
        ]
        for text, cmd, color in btn_cfgs:
            btn = tk.Button(
                sidebar, text=text, font=("Segoe UI", 9),
                bg="#21262d", fg="#c9d1d9", width=18, anchor=tk.W,
                relief=tk.FLAT, activebackground="#30363d",
                activeforeground="white", cursor="hand2",
                command=cmd
            )
            btn.pack(padx=10, pady=4)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#30363d"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#21262d"))

        # Feedback section
        sep1 = tk.Frame(sidebar, bg="#21262d", height=1)
        sep1.pack(fill=tk.X, padx=10, pady=16)
        tk.Label(
            sidebar, text="-- Rating --", font=("Segoe UI", 8),
            fg="#484f58", bg="#161b22"
        ).pack(pady=(0, 6))

        fb_frame = tk.Frame(sidebar, bg="#161b22")
        fb_frame.pack()
        for txt, cmd, clr in [
            ("Good +", lambda: self._feedback(1), "#238636"),
            ("Bad -", lambda: self._feedback(-1), "#da3633"),
        ]:
            tk.Button(
                fb_frame, text=txt, font=("Segoe UI", 9, "bold"),
                bg=clr, fg="white", width=7, relief=tk.FLAT,
                command=cmd, cursor="hand2"
            ).pack(side=tk.LEFT, padx=3)

        # System info
        sep2 = tk.Frame(sidebar, bg="#21262d", height=1)
        sep2.pack(fill=tk.X, padx=10, pady=16)
        tk.Label(
            sidebar, text="-- System --", font=("Segoe UI", 8),
            fg="#484f58", bg="#161b22"
        ).pack(pady=(0, 6))
        try:
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)
            vram_used = round(torch.cuda.memory_allocated(0) / 1024**3, 1)
            tk.Label(
                sidebar, text=f"GPU: {gpu_name}",
                font=("Consolas", 8), fg="#8b949e", bg="#161b22"
            ).pack(anchor=tk.W, padx=10)
            tk.Label(
                sidebar, text=f"VRAM: {vram_used}/{vram_gb} GB",
                font=("Consolas", 8), fg="#8b949e", bg="#161b22"
            ).pack(anchor=tk.W, padx=10)
        except Exception:
            tk.Label(
                sidebar, text="GPU: Not detected",
                font=("Consolas", 8), fg="#8b949e", bg="#161b22"
            ).pack(anchor=tk.W, padx=10)

        # ===== Chat area =====
        chat_area = tk.Frame(mid, bg="#0d1117")
        chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Chat display with right-click menu
        self.chat_display = scrolledtext.ScrolledText(
            chat_area, font=("Segoe UI", 11),
            bg="#0d1117", fg="#c9d1d9",
            insertbackground="white", wrap=tk.WORD,
            state=tk.DISABLED, relief=tk.FLAT,
            padx=20, pady=14,
            selectbackground="#264f78"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 0))

        # Right-click context menu for chat display
        self.chat_menu = Menu(self.root, tearoff=0, bg="#21262d", fg="#c9d1d9",
                              activebackground="#388bfd", activeforeground="white",
                              font=("Segoe UI", 9))
        self.chat_menu.add_command(label="Copy Selected   Ctrl+C", command=self._copy_selected)
        self.chat_menu.add_separator()
        self.chat_menu.add_command(label="Copy AI Response", command=self._copy_last_ai)
        self.chat_menu.add_command(label="Copy All Chat", command=self._copy_all_chat)
        self.chat_menu.add_separator()
        self.chat_menu.add_command(label="Select All   Ctrl+A", command=self._select_all_chat)
        self.chat_display.bind("<Button-3>", self._show_chat_menu)

        # Tag styles
        self.chat_display.tag_configure("user", foreground="#58a6ff",
                                         font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_configure("ai", foreground="#3fb950",
                                        font=("Segoe UI", 11))
        self.chat_display.tag_configure("ai_text", foreground="#c9d1d9",
                                        font=("Segoe UI", 11))
        self.chat_display.tag_configure("system", foreground="#f0883e",
                                        font=("Segoe UI", 9))
        self.chat_display.tag_configure("divider", foreground="#21262d")
        self.chat_display.tag_configure("copy_btn", foreground="#388bfd",
                                        font=("Segoe UI", 8), underline=True)
        self.chat_display.tag_bind("copy_btn", "<Enter>",
                                   lambda e: self.chat_display.config(cursor="hand2"))
        self.chat_display.tag_bind("copy_btn", "<Leave>",
                                   lambda e: self.chat_display.config(cursor=""))

        # Track message positions for per-message copy
        self.msg_ranges = []  # list of (start_idx, end_idx, role, text)

        # Bind click on copy tag
        self.chat_display.tag_bind("copy_btn", "<Button-1>", self._on_copy_click)

        # ===== Input area =====
        input_frame = tk.Frame(self.root, bg="#161b22")
        input_frame.pack(fill=tk.X)

        # Input box with right-click menu
        self.input_box = tk.Text(
            input_frame, font=("Segoe UI", 11),
            bg="#0d1117", fg="#c9d1d9",
            insertbackground="white", wrap=tk.WORD,
            height=4, relief=tk.FLAT, padx=14, pady=10,
            selectbackground="#264f78", undo=True
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 6), pady=10)
        self.input_box.bind("<Control-Return>", lambda e: None)  # allow newline with Ctrl+Enter
        self.input_box.bind("<Return>", self._on_send_enter)
        self.input_box.bind("<Control-a>", self._select_all_input)

        # Right-click menu for input box
        self.input_menu = Menu(self.root, tearoff=0, bg="#21262d", fg="#c9d1d9",
                               activebackground="#388bfd", activeforeground="white",
                               font=("Segoe UI", 9))
        self.input_menu.add_command(label="Undo   Ctrl+Z", command=lambda: self.input_box.event_generate("<<Undo>>"))
        self.input_menu.add_separator()
        self.input_menu.add_command(label="Cut   Ctrl+X", command=self._input_cut)
        self.input_menu.add_command(label="Copy   Ctrl+C", command=self._input_copy)
        self.input_menu.add_command(label="Paste   Ctrl+V", command=self._input_paste)
        self.input_menu.add_separator()
        self.input_menu.add_command(label="Select All   Ctrl+A", command=self._select_all_input)
        self.input_box.bind("<Button-3>", self._show_input_menu)

        # Buttons
        btn_col = tk.Frame(input_frame, bg="#161b22")
        btn_col.pack(side=tk.RIGHT, padx=(4, 12), pady=10)

        self.send_btn = tk.Button(
            btn_col, text="Send", font=("Segoe UI", 11, "bold"),
            bg="#238636", fg="white", width=10, height=2,
            command=self._on_send, relief=tk.FLAT, cursor="hand2",
            activebackground="#2ea043"
        )
        self.send_btn.pack(pady=(0, 6))

        self.stop_btn = tk.Button(
            btn_col, text="Stop", font=("Segoe UI", 9),
            bg="#da3633", fg="white", width=10,
            command=self._on_stop, relief=tk.FLAT, state=tk.DISABLED, cursor="hand2"
        )
        self.stop_btn.pack()

        # Hint label
        hint = tk.Label(
            input_frame, text="Enter: Send | Ctrl+Enter: Newline | Right-click: Context Menu",
            font=("Segoe UI", 8), fg="#484f58", bg="#161b22"
        )
        hint.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(0, 6))

    # ========== Context Menus ==========

    def _show_chat_menu(self, event):
        self.chat_menu.tk_popup(event.x_root, event.y_root)

    def _show_input_menu(self, event):
        self.input_menu.tk_popup(event.x_root, event.y_root)

    # ========== Copy/Paste Operations ==========

    def _copy_selected(self):
        """Copy selected text from chat display"""
        try:
            sel = self.chat_display.selection_get()
            if sel:
                self.root.clipboard_clear()
                self.root.clipboard_append(sel)
                self._log("[Copied to clipboard]")
        except Exception:
            pass

    def _copy_last_ai(self):
        """Copy the most recent AI response"""
        for start, end, role, text in reversed(self.msg_ranges):
            if role == "ai":
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self._log(f"[Copied AI response ({len(text)} chars)]")
                return
        self._log("[No AI response to copy]")

    def _copy_all_chat(self):
        """Copy entire conversation as plain text"""
        lines = []
        for _, _, role, text in self.msg_ranges:
            prefix = "[You] " if role == "user" else ("[AI] " if role == "ai" else "")
            lines.append(prefix + text)
        full = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(full)
        self._log(f"[Copied all chat ({len(full)} chars)]")

    def _select_all_chat(self):
        """Select all text in chat display"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.tag_add(tk.SEL, "1.0", tk.END)
        self.chat_display.focus_set()
        self.chat_display.config(state=tk.DISABLED)

    def _on_copy_click(self, event):
        """Handle click on [copy] tag next to AI response"""
        # Find which message is near the click position
        idx = self.chat_display.index("@{},{}".format(event.x, event.y))
        for start, end, role, text in self.msg_ranges:
            if role == "ai" and self.chat_display.compare(start, "<=", idx) \
                    and self.chat_display.compare(idx, "<=", end):
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self._log(f"[Copied ({len(text)} chars)]")
                return

    def _input_cut(self):
        self.input_box.event_generate("<<Cut>>")

    def _input_copy(self):
        self.input_box.event_generate("<<Copy>>")

    def _input_paste(self):
        try:
            clip = self.root.clipboard_get()
            self.input_box.insert(tk.INSERT, clip)
        except Exception:
            pass

    def _select_all_input(self, event=None):
        self.input_box.tag_add(tk.SEL, "1.0", tk.END)
        return "break"

    # ========== Export ==========

    def _export_chat(self):
        """Export conversation to file"""
        if not self.msg_ranges:
            messagebox.showinfo("Info", "No conversation to export.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[
                ("Markdown", "*.md"),
                ("Text", "*.txt"),
                ("JSON", "*.json"),
            ],
            initialfile=f"ire_agi_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        if not filepath:
            return

        ext = Path(filepath).suffix.lower()
        if ext == ".json":
            data = [{"role": r, "text": t} for _, _, r, t in self.msg_ranges]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif ext == ".md":
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("# IRE-AGI Chat Export\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")
                for _, _, role, text in self.msg_ranges:
                    if role == "user":
                        f.write(f"## You\n\n{text}\n\n")
                    elif role == "ai":
                        f.write(f"## IRE-AGI\n\n{text}\n\n")
                    else:
                        f.write(f"> *{text}*\n\n")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                for _, _, role, text in self.msg_ranges:
                    prefix = "[You] " if role == "user" else ("[AI] " if role == "ai" else "")
                    f.write(prefix + text + "\n\n")

        self._log(f"[Chat exported to {os.path.basename(filepath)}]")

    # ========== Logging & Messages ==========

    def _log(self, text):
        self.chat_display.config(state=tk.NORMAL)
        start = self.chat_display.index(tk.END + "-1c")
        self.chat_display.insert(tk.END, f"[System] {text}\n", "system")
        end = self.chat_display.index(tk.END + "-1c")
        self.msg_ranges.append((start, end, "system", text))
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.messages.append({"role": "system", "text": text})

    def _add_message(self, role, text):
        self.chat_display.config(state=tk.NORMAL)

        # Record range start
        start_idx = self.chat_display.index(tk.END)

        if role == "user":
            self.chat_display.insert(tk.END, f"\nYou:\n", "user")
            self.chat_display.insert(tk.END, f"{text}\n", "user")
        else:
            self.chat_display.insert(tk.END, f"\nIRE-AGI:", "ai")
            # Inline copy button
            copy_start = self.chat_display.index(tk.END)
            self.chat_display.insert(tk.END, "  [Copy] ", "copy_btn")
            self.chat_display.insert(tk.END, "\n", "ai")
            self.chat_display.insert(tk.END, f"{text}\n", "ai_text")

        self.chat_display.insert(tk.END, "-" * 60 + "\n", "divider")

        end_idx = self.chat_display.index(tk.END)
        self.msg_ranges.append((start_idx, end_idx, role, text))
        self.messages.append({"role": role, "text": text})

        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _update_evolution_display(self):
        self.evo_label.config(text=self.evolution.get_summary())

    # ========== Model Loading ==========

    def _load_model_async(self):
        def _worker():
            try:
                self.llm.load(callback=lambda msg: self.root.after(0, lambda m=msg: self._log(m)))
                self.root.after(0, self._on_model_loaded)
            except Exception as e:
                self.root.after(0, lambda err=str(e): self._on_model_load_error(err))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _on_model_loaded(self):
        self.status_label.config(text="Ready", fg="#3fb950")
        self._log("Model loaded! Ready to chat.")
        welcome = (
            "Hello! I'm IRE-AGI v5.1, a self-evolving AI.\n\n"
            "What I can do:\n"
            "- **Chat** - Ask me anything\n"
            "- **Analyze** - Paste your data and I'll analyze it\n"
            "- **Summarize** - Long text -> Short summary\n"
            "- **Evolve** - Rate my answers (+/-)\n\n"
            "Try saying hi!"
        )
        self._add_message("ai", welcome)

    def _on_model_load_error(self, error):
        self.status_label.config(text="Load Error", fg="#da3633")
        self._log(f"Model load failed: {error}")
        self._log("Check that the model files exist.")

    # ========== Send / Receive ==========

    def _on_send_enter(self, event):
        self._on_send()
        return "break"

    def _on_send(self, event=None):
        if self.is_generating:
            return

        text = self.input_box.get("1.0", tk.END).strip()
        if not text:
            return
        if not self.llm.loaded:
            self._log("Model still loading...")
            return

        self.input_box.delete("1.0", tk.END)
        self._add_message("user", text)
        self.last_user_msg = text

        self.is_generating = True
        self.send_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Thinking...", fg="#f0883e")

        def _worker():
            try:
                response = self.llm.chat(text)
                self.root.after(0, lambda r=response: self._on_response(r))
            except Exception as e:
                self.root.after(0, lambda err=str(e): self._on_response_error(err))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _on_response(self, response):
        self.last_ai_msg = response
        self._add_message("ai", response)
        self.is_generating = False
        self.send_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Ready", fg="#3fb950")

        try:
            self.evolution.record_conversation(len(response))
            self._update_evolution_display()
        except Exception:
            pass

    def _on_response_error(self, error):
        self._add_message("ai", f"[Error]: {error}")
        self.is_generating = False
        self.send_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Error", fg="#da3633")

    def _on_stop(self):
        self.is_generating = False
        self.status_label.config(text="Stopped", fg="#f0883e")

    # ========== Mode Switching ==========

    def _feedback(self, rating):
        if not hasattr(self, "last_user_msg") or not self.llm.conversation_history:
            return
        last_ai = self.llm.conversation_history[-1]["content"] if self.llm.conversation_history else ""
        self.evolution.record_feedback(self.last_user_msg, last_ai, rating)
        self._update_evolution_display()
        icon = "+ Good!" if rating > 0 else "- Bad, I'll improve."
        self._log(icon)

    def _mode_chat(self):
        self._log("Mode: Chat")
        self.input_box.delete("1.0", tk.END)

    def _mode_analyze(self):
        self._add_message("ai",
            "Data Analysis mode ON!\n\n"
            "Paste your data below. I can analyze:\n"
            "- Trends and patterns\n"
            "- Distribution features\n"
            "- Outliers/anomalies\n"
            "- Statistical summary"
        )
        self._log("Mode: Analyze Data")

    def _mode_summarize(self):
        self._add_message("ai",
            "Text Summary mode ON!\n\n"
            "Paste the long text you want summarized."
        )
        self._log("Mode: Summarize")

    def _clear_chat(self):
        self.llm.clear_history()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.msg_ranges.clear()
        self.messages.clear()
        self._log("Chat cleared")

    def _on_quit(self):
        self.root.destroy()


# ============ Entry Point ============
def main():
    root = tk.Tk()
    app = IREAGIAppV51(root)
    root.mainloop()


if __name__ == "__main__":
    main()
