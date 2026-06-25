"""
IRE-AGI v5.2 Multimodal Edition
- Chat + Data Analysis + Self-Evolution + Image Generation
- Based on Qwen2.5-7B-Instruct (LLM) + SDXL-Turbo (Image Gen)
- Consciousness Entropy Optimization / Self-Evolution Engine

v5.2 New Features:
- Text-to-Image generation (SDXL-Turbo, 1-step fast)
- Image display in chat + save to disk
- Smart model swapping (LLM <-> Image Gen, managed VRAM)
- Right-click menus (Copy/Paste/Select All)
- Export chat (Markdown/TXT/JSON)
- Per-message copy button
"""

import os
import sys
import json
import time
import threading
import tempfile
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, Menu
from datetime import datetime
from pathlib import Path

import torch
from PIL import Image, ImageTk


# ============ LLM Core ============
class LocalLLM:
    """Local LLM wrapper (Qwen2.5-7B-Instruct)"""

    def __init__(self, model_path=None):
        self.model = None
        self.tokenizer = None
        self.model_path = model_path or os.path.join(
            os.path.expanduser("~"), ".workbuddy", "models", "Qwen2.5-7B-Instruct"
        )
        self.conversation_history = []
        self.loaded = False

    def load(self, callback=None):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if callback:
            callback("Loading Tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, trust_remote_code=True
        )
        if callback:
            callback("Loading LLM to GPU (~15GB)...")
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path, torch_dtype=torch.float16,
            device_map="auto", trust_remote_code=True
        )
        if callback:
            callback("LLM loaded!")
        self.loaded = True

    def unload(self):
        """Release GPU memory"""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        self.loaded = False
        torch.cuda.empty_cache()
        import gc
        gc.collect()

    def chat(self, user_message, max_new_tokens=2048):
        if not self.loaded:
            return "Model not loaded yet."
        self.conversation_history.append({"role": "user", "content": user_message})
        messages = [
            {"role": "system", "content": "You are IRE-AGI, a self-evolving AI. You can chat, analyze data, and generate images. Respond in Chinese."}
        ] + self.conversation_history[-20:]
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs, max_new_tokens=max_new_tokens,
            do_sample=True, temperature=0.7, top_p=0.9,
            repetition_penalty=1.1, pad_token_id=self.tokenizer.eos_token_id
        )
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def clear_history(self):
        self.conversation_history = []


# ============ Image Generator ============
class ImageGenerator:
    """SDXL-Turbo based image generator"""

    def __init__(self, model_path=None):
        self.pipe = None
        self.model_path = model_path or os.path.join(
            os.path.expanduser("~"), ".workbuddy", "models", "sdxl-turbo"
        )
        self.loaded = False

    def load(self, callback=None):
        from diffusers import StableDiffusionXLPipeline

        if callback:
            callback("Loading Image Generator...")
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            self.model_path, torch_dtype=torch.float16,
            use_safetensors=True
        )
        self.pipe.to("cuda")
        if callback:
            callback("Image Generator loaded!")
        self.loaded = True

    def unload(self):
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
        self.loaded = False
        torch.cuda.empty_cache()
        import gc
        gc.collect()

    def generate(self, prompt, negative_prompt="", num_inference_steps=4,
                 guidance_scale=0.0, width=512, height=512, seed=None):
        if not self.loaded:
            return None
        generator = None
        if seed is not None:
            generator = torch.Generator("cuda").manual_seed(seed)
        image = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt or None,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            width=width, height=height,
            generator=generator
        ).images[0]
        return image


# ============ Model Manager (VRAM Smart Swap) ============
class ModelManager:
    """Manages LLM and Image Gen models, smart swap to fit in 24GB VRAM"""

    def __init__(self, llm, img_gen):
        self.llm = llm
        self.img_gen = img_gen
        self.active_model = None  # "llm" or "img_gen"
        self._loading = False

    def ensure_llm(self, status_callback=None):
        """Make sure LLM is loaded (unload image gen if needed)"""
        if self.llm.loaded:
            return
        if self._loading:
            return
        self._loading = True
        if self.img_gen.loaded:
            if status_callback:
                status_callback("Swapping: Image Gen -> LLM...")
            self.img_gen.unload()
        self.llm.load(callback=status_callback)
        self.active_model = "llm"
        self._loading = False

    def ensure_img_gen(self, status_callback=None):
        """Make sure image gen is loaded (unload LLM if needed)"""
        if self.img_gen.loaded:
            return
        if self._loading:
            return
        self._loading = True
        if self.llm.loaded:
            if status_callback:
                status_callback("Swapping: LLM -> Image Gen...")
            self.llm.unload()
        self.img_gen.load(callback=status_callback)
        self.active_model = "img_gen"
        self._loading = False


# ============ Self-Evolution Engine ============
class SelfEvolutionEngineV2:
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
            "images_generated": 0,
            "created_at": datetime.now().isoformat(),
        }

    def record_conversation(self, tokens_generated):
        self.stats["total_conversations"] += 1
        self.stats["total_tokens_generated"] += tokens_generated
        self._check_evolution()
        self._save_stats()

    def record_image_gen(self):
        self.stats["images_generated"] += 1
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
            f"Chat: {s['total_conversations']} | "
            f"Img: {s.get('images_generated', 0)} | "
            f"Good: {acc:.0f}% | "
            f"Lv.{s['evolution_level']}"
        )


# ============ Main GUI Application ============
class IREAGIAppV52:
    def __init__(self, root):
        self.root = root
        self.root.title("IRE-AGI v5.2 - Multimodal AI")
        self.root.geometry("1150x800")
        self.root.configure(bg="#0d1117")
        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)

        # Core components
        self.llm = LocalLLM()
        self.img_gen = ImageGenerator()
        self.model_mgr = ModelManager(self.llm, self.img_gen)
        self.evolution = SelfEvolutionEngineV2(
            save_dir=os.path.join(os.path.expanduser("~"), ".workbuddy", "ire-agi-data")
        )
        self.is_generating = False
        self.last_user_msg = ""
        self.last_ai_msg = ""
        self.messages = []
        self.msg_ranges = []
        self.image_dir = os.path.join(os.path.expanduser("~"), ".workbuddy", "ire-agi-data", "images")
        os.makedirs(self.image_dir, exist_ok=True)
        self.current_images = []  # Track displayed images for save
        self.current_tk_images = []  # Prevent GC

        self._build_ui()
        self._log("System initializing, loading LLM...")
        self._load_llm_async()

    # ========== UI Build ==========
    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#161b22", height=52)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header, text="IRE-AGI v5.2",
            font=("Segoe UI", 15, "bold"),
            fg="#58a6ff", bg="#161b22"
        ).pack(side=tk.LEFT, padx=16, pady=8)

        self.status_label = tk.Label(
            header, text="Loading...",
            font=("Segoe UI", 9), fg="#f0883e", bg="#161b22"
        )
        self.status_label.pack(side=tk.LEFT, padx=12)

        # Active model indicator
        self.model_indicator = tk.Label(
            header, text="",
            font=("Segoe UI", 8), fg="#8b949e", bg="#161b22"
        )
        self.model_indicator.pack(side=tk.LEFT, padx=8)

        # Export button
        tk.Button(
            header, text="Export", font=("Segoe UI", 8),
            bg="#21262d", fg="#c9d1d9", relief=tk.FLAT,
            activebackground="#30363d", command=self._export_chat
        ).pack(side=tk.RIGHT, padx=(0, 16))

        self.evo_label = tk.Label(
            header, text="", font=("Segoe UI", 9),
            fg="#3fb950", bg="#161b22"
        )
        self.evo_label.pack(side=tk.RIGHT, padx=8)
        self._update_evolution_display()

        # Main area
        mid = tk.Frame(self.root, bg="#0d1117")
        mid.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar = tk.Frame(mid, bg="#161b22", width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="Functions",
            font=("Segoe UI", 11, "bold"),
            fg="#c9d1d9", bg="#161b22"
        ).pack(pady=(18, 12))

        btn_configs = [
            ("Chat", self._mode_chat, "#21262d"),
            ("Analyze Data", self._mode_analyze, "#21262d"),
            ("Summarize Text", self._mode_summarize, "#21262d"),
            ("-- sep1 --", None, None),
            ("Generate Image", self._mode_image_gen, "#1a3a5c"),
            ("-- sep2 --", None, None),
            ("Clear Chat", self._clear_chat, "#21262d"),
        ]
        for text, cmd, bg in btn_configs:
            if text.startswith("--"):
                tk.Frame(sidebar, bg="#21262d", height=1).pack(
                    fill=tk.X, padx=10, pady=10)
                continue
            btn = tk.Button(
                sidebar, text=text, font=("Segoe UI", 9),
                bg=bg, fg="#c9d1d9", width=20, anchor=tk.W,
                relief=tk.FLAT, activebackground="#30363d",
                activeforeground="white", cursor="hand2",
                command=cmd
            )
            btn.pack(padx=10, pady=3)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#30363d"))
            btn.bind("<Leave>", lambda e, b=btn, c=bg: b.config(bg=c))

        # Image Gen Options
        img_frame = tk.LabelFrame(
            sidebar, text="Image Options",
            font=("Segoe UI", 8), fg="#58a6ff", bg="#161b22",
            labelanchor="n"
        )
        img_frame.pack(fill=tk.X, padx=10, pady=(6, 4))

        # Size selector
        tk.Label(img_frame, text="Size:", font=("Segoe UI", 8),
                 fg="#8b949e", bg="#161b22").pack(anchor=tk.W, padx=4)
        self.img_size_var = tk.StringVar(value="512x512")
        size_menu = ttk.Combobox(
            img_frame, textvariable=self.img_size_var,
            values=["512x512", "768x768", "1024x1024", "512x768", "768x512"],
            state="readonly", width=14, font=("Segoe UI", 8)
        )
        size_menu.pack(padx=4, pady=2)

        # Steps slider
        tk.Label(img_frame, text="Steps (1-8):", font=("Segoe UI", 8),
                 fg="#8b949e", bg="#161b22").pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.img_steps_var = tk.IntVar(value=4)
        steps_scale = tk.Scale(
            img_frame, from_=1, to=8, orient=tk.HORIZONTAL,
            variable=self.img_steps_var, bg="#161b22", fg="#c9d1d9",
            highlightthickness=0, troughcolor="#21262d",
            font=("Segoe UI", 7), length=160
        )
        steps_scale.pack(padx=4, pady=2)

        # Seed
        tk.Label(img_frame, text="Seed (0=random):", font=("Segoe UI", 8),
                 fg="#8b949e", bg="#161b22").pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.img_seed_var = tk.StringVar(value="0")
        tk.Entry(
            img_frame, textvariable=self.img_seed_var,
            font=("Consolas", 9), bg="#0d1117", fg="#c9d1d9",
            insertbackground="white", width=14
        ).pack(padx=4, pady=2)

        # Rating section
        tk.Frame(sidebar, bg="#21262d", height=1).pack(
            fill=tk.X, padx=10, pady=10)
        tk.Label(sidebar, text="-- Rating --", font=("Segoe UI", 8),
                 fg="#484f58", bg="#161b22").pack(pady=(0, 4))
        fb_frame = tk.Frame(sidebar, bg="#161b22")
        fb_frame.pack()
        tk.Button(
            fb_frame, text="Good +", font=("Segoe UI", 9, "bold"),
            bg="#238636", fg="white", width=8, relief=tk.FLAT,
            command=lambda: self._feedback(1), cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            fb_frame, text="Bad -", font=("Segoe UI", 9, "bold"),
            bg="#da3633", fg="white", width=8, relief=tk.FLAT,
            command=lambda: self._feedback(-1), cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

        # GPU info
        tk.Frame(sidebar, bg="#21262d", height=1).pack(
            fill=tk.X, padx=10, pady=10)
        self.gpu_info_label = tk.Label(
            sidebar, text="",
            font=("Consolas", 7), fg="#8b949e", bg="#161b22",
            wraplength=170, justify=tk.LEFT
        )
        self.gpu_info_label.pack(anchor=tk.W, padx=10)
        self._update_gpu_info()

        # ===== Chat area =====
        chat_area = tk.Frame(mid, bg="#0d1117")
        chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Chat display with image support
        self.chat_display = scrolledtext.ScrolledText(
            chat_area, font=("Segoe UI", 11),
            bg="#0d1117", fg="#c9d1d9",
            insertbackground="white", wrap=tk.WORD,
            state=tk.DISABLED, relief=tk.FLAT,
            padx=20, pady=14, selectbackground="#264f78"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 0))

        # Right-click menu for chat display
        self.chat_menu = Menu(
            self.root, tearoff=0, bg="#21262d", fg="#c9d1d9",
            activebackground="#388bfd", activeforeground="white",
            font=("Segoe UI", 9)
        )
        self.chat_menu.add_command(label="Copy Selected", command=self._copy_selected)
        self.chat_menu.add_separator()
        self.chat_menu.add_command(label="Copy AI Response", command=self._copy_last_ai)
        self.chat_menu.add_command(label="Copy All Chat", command=self._copy_all_chat)
        self.chat_menu.add_separator()
        self.chat_menu.add_command(label="Select All", command=self._select_all_chat)
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
        self.chat_display.tag_configure("save_btn", foreground="#3fb950",
                                        font=("Segoe UI", 8), underline=True)
        self.chat_display.tag_bind("copy_btn", "<Enter>",
                                   lambda e: self.chat_display.config(cursor="hand2"))
        self.chat_display.tag_bind("copy_btn", "<Leave>",
                                   lambda e: self.chat_display.config(cursor=""))
        self.chat_display.tag_bind("save_btn", "<Enter>",
                                   lambda e: self.chat_display.config(cursor="hand2"))
        self.chat_display.tag_bind("save_btn", "<Leave>",
                                   lambda e: self.chat_display.config(cursor=""))
        self.chat_display.tag_bind("copy_btn", "<Button-1>", self._on_copy_click)
        self.chat_display.tag_bind("save_btn", "<Button-1>", self._on_save_img_click)

        # ===== Input area =====
        input_frame = tk.Frame(self.root, bg="#161b22")
        input_frame.pack(fill=tk.X)

        self.input_box = tk.Text(
            input_frame, font=("Segoe UI", 11),
            bg="#0d1117", fg="#c9d1d9",
            insertbackground="white", wrap=tk.WORD,
            height=4, relief=tk.FLAT, padx=14, pady=10,
            selectbackground="#264f78", undo=True
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                            padx=(10, 6), pady=10)
        self.input_box.bind("<Return>", self._on_send_enter)
        self.input_box.bind("<Control-a>", self._select_all_input)

        # Right-click for input
        self.input_menu = Menu(
            self.root, tearoff=0, bg="#21262d", fg="#c9d1d9",
            activebackground="#388bfd", activeforeground="white",
            font=("Segoe UI", 9)
        )
        self.input_menu.add_command(label="Undo", command=lambda: self.input_box.event_generate("<<Undo>>"))
        self.input_menu.add_separator()
        self.input_menu.add_command(label="Cut", command=lambda: self.input_box.event_generate("<<Cut>>"))
        self.input_menu.add_command(label="Copy", command=lambda: self.input_box.event_generate("<<Copy>>"))
        self.input_menu.add_command(label="Paste", command=self._input_paste)
        self.input_menu.add_separator()
        self.input_menu.add_command(label="Select All", command=self._select_all_input)
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
            command=self._on_stop, relief=tk.FLAT,
            state=tk.DISABLED, cursor="hand2"
        )
        self.stop_btn.pack()

        # Mode indicator
        self.mode_var = tk.StringVar(value="Chat Mode")
        tk.Label(
            input_frame, textvariable=self.mode_var,
            font=("Segoe UI", 8, "italic"), fg="#58a6ff", bg="#161b22"
        ).pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=(0, 2))

        tk.Label(
            input_frame, text="Enter: Send | Right-click: Menu",
            font=("Segoe UI", 7), fg="#484f58", bg="#161b22"
        ).pack(side=tk.BOTTOM, fill=tk.X, padx=14)

    # ========== Context Menus ==========
    def _show_chat_menu(self, event):
        self.chat_menu.tk_popup(event.x_root, event.y_root)

    def _show_input_menu(self, event):
        self.input_menu.tk_popup(event.x_root, event.y_root)

    # ========== Copy/Paste Operations ==========
    def _copy_selected(self):
        try:
            sel = self.chat_display.selection_get()
            if sel:
                self.root.clipboard_clear()
                self.root.clipboard_append(sel)
        except Exception:
            pass

    def _copy_last_ai(self):
        for _, _, role, text in reversed(self.msg_ranges):
            if role == "ai":
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                return

    def _copy_all_chat(self):
        lines = []
        for _, _, role, text in self.msg_ranges:
            prefix = "[You] " if role == "user" else ("[AI] " if role == "ai" else "")
            lines.append(prefix + text)
        full = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(full)

    def _select_all_chat(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.tag_add(tk.SEL, "1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _on_copy_click(self, event):
        idx = self.chat_display.index("@{},{}".format(event.x, event.y))
        for start, end, role, text in self.msg_ranges:
            if role == "ai" and self.chat_display.compare(start, "<=", idx) \
                    and self.chat_display.compare(idx, "<=", end):
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                return

    def _on_save_img_click(self, event):
        idx = self.chat_display.index("@{},{}".format(event.x, event.y))
        for start, end, role, text in self.msg_ranges:
            if role == "image" and self.chat_display.compare(start, "<=", idx) \
                    and self.chat_display.compare(idx, "<=", end):
                # Find the image path in the text
                for img_path in self.current_images:
                    if img_path in text or os.path.exists(img_path):
                        save_path = filedialog.asksaveasfilename(
                            defaultextension=".png",
                            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
                            initialfile=os.path.basename(img_path)
                        )
                        if save_path:
                            from PIL import Image as PILImage
                            img = PILImage.open(img_path)
                            img.save(save_path)
                            self._log(f"Image saved to {save_path}")
                        return

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
        if not self.msg_ranges:
            messagebox.showinfo("Info", "No conversation to export.")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("JSON", "*.json")],
            initialfile=f"ire_agi_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        if not filepath:
            return
        ext = Path(filepath).suffix.lower()
        try:
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
                        elif role == "image":
                            f.write(f"## Generated Image\n\n{text}\n\n")
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    for _, _, role, text in self.msg_ranges:
                        prefix = {"user": "[You]", "ai": "[AI]", "image": "[Image]", "system": "[System]"}.get(role, "")
                        f.write(f"{prefix} {text}\n\n")
            self._log(f"Exported to {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

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
        start_idx = self.chat_display.index(tk.END)
        if role == "user":
            self.chat_display.insert(tk.END, f"\nYou:\n", "user")
            self.chat_display.insert(tk.END, f"{text}\n", "user")
        elif role == "image":
            self.chat_display.insert(tk.END, f"\nGenerated Image:", "ai")
            self.chat_display.insert(tk.END, "  [Copy] ", "copy_btn")
            self.chat_display.insert(tk.END, "  [Save] ", "save_btn")
            self.chat_display.insert(tk.END, "\n", "ai")
        else:
            self.chat_display.insert(tk.END, f"\nIRE-AGI:", "ai")
            self.chat_display.insert(tk.END, "  [Copy] ", "copy_btn")
            self.chat_display.insert(tk.END, "\n", "ai")
            self.chat_display.insert(tk.END, f"{text}\n", "ai_text")

        self.chat_display.insert(tk.END, "-" * 60 + "\n", "divider")
        end_idx = self.chat_display.index(tk.END)
        self.msg_ranges.append((start_idx, end_idx, role, text))
        self.messages.append({"role": role, "text": text})
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _add_image(self, image_path):
        """Display an image in the chat area"""
        self.chat_display.config(state=tk.NORMAL)

        # Add text label
        self.chat_display.insert(tk.END, f"\n", "ai")

        # Load and resize image for display
        try:
            pil_img = Image.open(image_path)
            # Scale to fit chat width (~600px max)
            max_w = 600
            w, h = pil_img.size
            if w > max_w:
                ratio = max_w / w
                pil_img = pil_img.resize((max_w, int(h * ratio)), Image.LANCZOS)

            tk_img = ImageTk.PhotoImage(pil_img)
            self.current_tk_images.append(tk_img)  # Prevent GC

            # Insert image
            self.chat_display.image_create(tk.END, image=tk_img)
            self.chat_display.insert(tk.END, "\n", "ai")
        except Exception as e:
            self.chat_display.insert(tk.END, f"[Image display error: {e}]\n", "system")

        self.chat_display.insert(tk.END, f"  Saved: {image_path}\n", "system")
        self.chat_display.insert(tk.END, "-" * 60 + "\n", "divider")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

        # Track for save/copy
        start_idx = self.chat_display.index(tk.END + "-2 lines")
        end_idx = self.chat_display.index(tk.END + "-1c")
        self.msg_ranges.append((start_idx, end_idx, "image", image_path))
        self.current_images.append(image_path)

    def _update_evolution_display(self):
        self.evo_label.config(text=self.evolution.get_summary())

    def _update_gpu_info(self):
        try:
            gpu_name = torch.cuda.get_device_name(0)
            vram_total = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1)
            vram_used = round(torch.cuda.memory_allocated(0) / 1024**3, 1)
            info = f"GPU: {gpu_name}\nVRAM: {vram_used:.1f}/{vram_total} GB"
            self.gpu_info_label.config(text=info)
            # Update active model indicator
            if self.llm.loaded:
                self.model_indicator.config(text="[LLM Active]", fg="#3fb950")
            elif self.img_gen.loaded:
                self.model_indicator.config(text="[Image Gen Active]", fg="#58a6ff")
            else:
                self.model_indicator.config(text="[Loading...]", fg="#f0883e")
        except Exception:
            self.gpu_info_label.config(text="GPU: Not detected")

    # ========== Model Loading ==========
    def _load_llm_async(self):
        def _worker():
            try:
                self.model_mgr.ensure_llm(
                    status_callback=lambda msg: self.root.after(
                        0, lambda m=msg: self._log(m))
                )
                self.root.after(0, self._on_llm_loaded)
            except Exception as e:
                self.root.after(0, lambda err=str(e): self._on_model_error(err))
        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _on_llm_loaded(self):
        self.status_label.config(text="Ready", fg="#3fb950")
        self._update_gpu_info()
        self._log("LLM loaded! Ready to chat.")
        welcome = (
            "Hello! I'm IRE-AGI v5.2, a multimodal self-evolving AI.\n\n"
            "What I can do:\n"
            "- **Chat** -- Ask me anything\n"
            "- **Analyze** -- Paste data, I'll analyze\n"
            "- **Summarize** -- Long text -> Short summary\n"
            "- **Generate Images** -- Describe what you want to see!\n"
            "- **Evolve** -- Rate my answers, I get better\n\n"
            "Try: 'Generate a sunset over mountains' or just say hi!"
        )
        self._add_message("ai", welcome)

    def _on_model_error(self, error):
        self.status_label.config(text="Error", fg="#da3633")
        self._log(f"Model load error: {error}")

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

        self.input_box.delete("1.0", tk.END)
        self._add_message("user", text)
        self.last_user_msg = text

        mode = self.mode_var.get()

        if mode == "Image Generation Mode":
            self._generate_image(text)
        else:
            self._chat(text)

    def _chat(self, user_message):
        if not self.llm.loaded:
            self._log("Loading LLM (may take ~30s)...")
            self.is_generating = True
            self.send_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Loading LLM...", fg="#f0883e")

            def _load_and_chat():
                try:
                    self.model_mgr.ensure_llm(
                        status_callback=lambda msg: self.root.after(
                            0, lambda m=msg: self._log(m))
                    )
                    self.root.after(0, lambda: self._do_chat(user_message))
                except Exception as e:
                    self.root.after(0, lambda err=str(e): self._on_response_error(err))

            t = threading.Thread(target=_load_and_chat, daemon=True)
            t.start()
        else:
            self._do_chat(user_message)

    def _do_chat(self, user_message):
        self.is_generating = True
        self.send_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Thinking...", fg="#f0883e")
        self._update_gpu_info()

        def _worker():
            try:
                response = self.llm.chat(user_message)
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
        self._update_gpu_info()
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

    # ========== Image Generation ==========
    def _generate_image(self, prompt):
        self.is_generating = True
        self.send_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Preparing image gen...", fg="#f0883e")

        # Parse options
        size_str = self.img_size_var.get()
        try:
            w, h = size_str.split("x")
            width, height = int(w), int(h)
        except Exception:
            width, height = 512, 512

        steps = self.img_steps_var.get()
        try:
            seed = int(self.img_seed_var.get())
        except Exception:
            seed = 0

        def _worker():
            try:
                # Ensure image gen model is loaded
                if not self.img_gen.loaded:
                    self.root.after(0, lambda: self._log(
                        "Swapping to Image Generator (unloading LLM)..."))
                    self.model_mgr.ensure_img_gen(
                        status_callback=lambda msg: self.root.after(
                            0, lambda m=msg: self._log(m))
                    )
                    self.root.after(0, self._update_gpu_info)

                self.root.after(0, lambda: self.status_label.config(
                    text="Generating image...", fg="#f0883e"))
                self.root.after(0, lambda: self._log(
                    f"Generating: '{prompt}' ({width}x{height}, {steps} steps)..."))

                actual_seed = seed if seed > 0 else int(time.time()) % 2**31
                image = self.img_gen.generate(
                    prompt=prompt,
                    num_inference_steps=steps,
                    guidance_scale=0.0,
                    width=width, height=height,
                    seed=actual_seed
                )

                if image is not None:
                    # Save image
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"ire_img_{timestamp}_{actual_seed}.png"
                    img_path = os.path.join(self.image_dir, filename)
                    image.save(img_path)

                    self.root.after(0, lambda: self._on_image_generated(
                        img_path, prompt, actual_seed))
                else:
                    self.root.after(0, lambda: self._on_response_error(
                        "Image generation returned None"))

            except Exception as e:
                self.root.after(0, lambda err=str(e): self._on_response_error(err))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _on_image_generated(self, img_path, prompt, seed):
        self._add_image(img_path)
        self._log(f"Image generated (seed={seed}): {prompt}")
        self.is_generating = False
        self.send_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Ready", fg="#3fb950")
        self._update_gpu_info()
        self.evolution.record_image_gen()
        self._update_evolution_display()

        # Auto-switch back to chat mode after image gen
        self.mode_var.set("Chat Mode")

    # ========== Mode Switching ==========
    def _feedback(self, rating):
        if not hasattr(self, "last_user_msg"):
            return
        last_ai = self.llm.conversation_history[-1]["content"] if self.llm.conversation_history else ""
        self.evolution.record_feedback(self.last_user_msg, last_ai, rating)
        self._update_evolution_display()
        self._log("Good +1" if rating > 0 else "Bad, will improve")

    def _mode_chat(self):
        self.mode_var.set("Chat Mode")
        self._log("Mode: Chat")

    def _mode_analyze(self):
        self.mode_var.set("Chat Mode")
        self._log("Mode: Analyze Data")
        self._add_message("ai",
            "Data Analysis mode ON!\n\n"
            "Paste your data below. I can analyze:\n"
            "- Trends and patterns\n"
            "- Distribution features\n"
            "- Outliers/anomalies\n"
            "- Statistical summary"
        )

    def _mode_summarize(self):
        self.mode_var.set("Chat Mode")
        self._log("Mode: Summarize")
        self._add_message("ai",
            "Text Summary mode ON!\n\n"
            "Paste the long text you want summarized."
        )

    def _mode_image_gen(self):
        self.mode_var.set("Image Generation Mode")
        self._log("Mode: Image Generation")
        self._add_message("ai",
            "Image Generation mode ON!\n\n"
            "Type a description of the image you want to generate.\n\n"
            "Examples:\n"
            "- 'A sunset over mountains, oil painting style'\n"
            "- 'Cyberpunk city at night, neon lights'\n"
            "- 'Cute cat wearing a hat, digital art'\n\n"
            "Tip: Use English prompts for best results."
        )

    def _clear_chat(self):
        self.llm.clear_history()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.msg_ranges.clear()
        self.messages.clear()
        self.current_images.clear()
        self.current_tk_images.clear()
        self._log("Chat cleared")

    def _on_quit(self):
        # Cleanup
        try:
            self.llm.unload()
            self.img_gen.unload()
        except Exception:
            pass
        self.root.destroy()


# ============ Entry Point ============
def main():
    root = tk.Tk()
    app = IREAGIAppV52(root)
    root.mainloop()


if __name__ == "__main__":
    main()
