"""
武光衡理论 IRE-AGI v4.0 - 完整可运行桌面版
修复说明：
  - sklearn MiniBatchKMeans 需先 partial_fit 才能访问 cluster_centers_
  - output_head 输出维度改为 1（匹配 y 的标量标签）
  - 所有 cent er/centers 拼写错误已修正
  - ConsciousnessEntropyOptimizer.__init__ 参数顺序已修正
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import json
import os
import time
from collections import deque
from sklearn.cluster import MiniBatchKMeans

# ============ 超参数 ============
BETA  = 1.4427
GAMMA = 0.4427
ETA   = 0.1
MU    = 0.01
CREATIVITY_TEMP = 0.5


# ============ 正则库 ============
class MultiAgentRegularityLibrary:
    def __init__(self, max_patterns=64, feature_dim=256, similarity_threshold=0.85):
        self.max_patterns = max_patterns
        self.feature_dim = feature_dim
        self.similarity_threshold = similarity_threshold
        self.prototype_embeddings = nn.Parameter(
            torch.randn(max_patterns, feature_dim) * 0.02, requires_grad=False
        )
        self.importance  = torch.ones(max_patterns) / max_patterns
        self.usage_count = torch.zeros(max_patterns)
        # 三个 KMeans 实例
        nc = max(2, int(max_patterns * 0.8))
        self.kmeans_opt = MiniBatchKMeans(n_clusters=nc, random_state=42)
        self.kmeans_ske = MiniBatchKMeans(n_clusters=max(2, int(max_patterns * 1.2)), random_state=42)
        self.kmeans_met = MiniBatchKMeans(n_clusters=max(2, max_patterns), random_state=42)
        self.buffer = deque(maxlen=500)
        self._kmeans_fitted = False

    def update(self, features: torch.Tensor):
        with torch.no_grad():
            feats_np = features.detach().cpu().numpy()
            self.buffer.extend(feats_np)

            if len(self.buffer) >= 50 and len(self.buffer) % 50 == 0:
                buf = np.array(list(self.buffer))
                try:
                    self.kmeans_opt.partial_fit(buf)
                    self.kmeans_ske.partial_fit(buf)
                    self.kmeans_met.partial_fit(buf)
                    self._kmeans_fitted = True
                except Exception:
                    return

                if not self._kmeans_fitted:
                    return

                # 取三个聚类的中心（sklearn 属性名：cluster_centers_）
                device = self.prototype_embeddings.device
                try:
                    c_opt = torch.tensor(self.kmeans_opt.cluster_centers_, dtype=torch.float32, device=device)
                    c_ske = torch.tensor(self.kmeans_ske.cluster_centers_, dtype=torch.float32, device=device)
                    c_met = torch.tensor(self.kmeans_met.cluster_centers_, dtype=torch.float32, device=device)
                except Exception:
                    return

                all_centers = torch.cat([c_opt, c_ske, c_met], dim=0)

                # 共识筛选
                consensus = []
                for c in all_centers:
                    sims = F.cosine_similarity(c.unsqueeze(0), all_centers, dim=1)
                    if (sims > self.similarity_threshold).sum().item() >= 2:
                        consensus.append(c)

                if len(consensus) == 0:
                    consensus = [all_centers[0]]

                new_centers = torch.stack(consensus[:self.max_patterns])

                for nc in new_centers:
                    sim = F.cosine_similarity(
                        nc.unsqueeze(0), self.prototype_embeddings, dim=1
                    )
                    if sim.max() < self.similarity_threshold:
                        idx = torch.argmin(self.importance)
                        self.prototype_embeddings.data[idx] = nc
                        self.importance.data[idx] = 0.5
                        self.usage_count.data[idx] = 0

    def _sync_device(self, ref_tensor):
        """把所有内部张量同步到 ref_tensor 所在的设备"""
        device = ref_tensor.device
        if self.prototype_embeddings.device != device:
            self.prototype_embeddings.data = self.prototype_embeddings.data.to(device)
        if self.importance.device != device:
            self.importance = self.importance.to(device)
        if self.usage_count.device != device:
            self.usage_count = self.usage_count.to(device)

    def compute_applicability(self, features: torch.Tensor) -> torch.Tensor:
        self._sync_device(features)
        sim = F.cosine_similarity(
            features.unsqueeze(1),
            self.prototype_embeddings.unsqueeze(0),
            dim=2
        )
        return sim * self.importance.unsqueeze(0)

    def get_regularity_probs(self, applicability: torch.Tensor, temperature=1.0) -> torch.Tensor:
        return F.softmax(applicability / max(temperature, 1e-6), dim=-1)


# ============ 意识熵优化器 ============
class ConsciousnessEntropyOptimizer:
    def __init__(self, optimizer, entropy_target=0.5, safe_deviation=0.1):
        self.optimizer = optimizer
        self.entropy_target = entropy_target
        self.safe_deviation = safe_deviation
        self.entropy_history = []

    def calculate(self, probs: torch.Tensor, hidden_states: torch.Tensor) -> torch.Tensor:
        eps = 1e-10
        term1 = -torch.sum(probs * torch.log(probs + eps), dim=-1).mean()
        term2 = BETA * torch.var(hidden_states, unbiased=False).mean()
        # 用 softmax 得到合法概率分布（避免 normalize 负值导致 log(NaN)）
        h_prob = F.softmax(hidden_states, dim=-1)
        H = -(h_prob * torch.log(h_prob + eps)).sum(dim=-1).mean()
        D = torch.norm(hidden_states, p=2, dim=-1).mean()
        term3 = GAMMA * H * D
        return term1 + term2 + term3

    def step(self, probs, hidden_states, task_loss):
        entropy = self.calculate(probs, hidden_states)
        self.entropy_history.append(entropy.item())
        entropy_loss = F.mse_loss(
            entropy,
            torch.tensor(self.entropy_target, device=entropy.device, dtype=entropy.dtype)
        )
        total_loss = task_loss + self.safe_deviation * entropy_loss
        self.optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.optimizer.param_groups[0]['params'], 1.0)
        self.optimizer.step()
        return {
            'total_loss': total_loss.item(),
            'task_loss':  task_loss.item(),
            'entropy':     entropy.item(),
        }


# ============ 主模型 ============
class IRE_AGI(nn.Module):
    def __init__(self, input_dim=64, hidden_dim=256, num_patterns=64):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.regularity_lib = MultiAgentRegularityLibrary(
            max_patterns=num_patterns, feature_dim=hidden_dim
        )
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=hidden_dim, nhead=8, batch_first=True),
            num_layers=4,
        )
        self.output_head = nn.Linear(hidden_dim, 1)  # 输出标量

    def forward(self, x):
        batch, seq, dim = x.shape
        h = self.encoder(x)
        current_feat = h[:, -1, :]

        self.regularity_lib.update(current_feat)

        applicability = self.regularity_lib.compute_applicability(current_feat)
        probs = self.regularity_lib.get_regularity_probs(
            applicability, temperature=CREATIVITY_TEMP
        )

        pattern_emb = self.regularity_lib.prototype_embeddings[torch.argmax(probs, dim=1)]
        h_combined = h + pattern_emb.unsqueeze(1)
        h_out = self.transformer(h_combined)
        pred = self.output_head(h_out[:, -1, :]).squeeze(-1)  # (B,)
        return pred, probs, h_out


# ============ 矛盾环境 ============
class ContradictoryEnv:
    def __init__(self, input_dim=64, seq_len=16):
        self.input_dim = input_dim
        self.seq_len  = seq_len
        self.phase    = 0

    def generate_batch(self, batch_size):
        data, labels = [], []
        for _ in range(batch_size):
            t = torch.linspace(0, 4 * 3.14159, self.seq_len)
            if self.phase % 2 == 0:
                signal = torch.sin(t).unsqueeze(1) + 0.1 * torch.randn(self.seq_len, 1)
            else:
                signal = torch.sign(torch.sin(t)).unsqueeze(1) + 0.1 * torch.randn(self.seq_len, 1)
            x = signal.repeat(1, self.input_dim)
            data.append(x)
            labels.append(torch.sin(t[-1]).unsqueeze(0))
        self.phase += 1
        return torch.stack(data), torch.stack(labels)


# ============ 验证 ============
@torch.no_grad()
def validate(model, test_env, device, steps=20):
    model.eval()
    total_loss, total_entropy = 0.0, 0.0
    for _ in range(steps):
        x, y = test_env.generate_batch(4)
        x, y = x.to(device), y.to(device)
        pred, probs, h = model(x)
        loss = F.mse_loss(pred, y.squeeze(-1))
        entropy = -(probs * torch.log(probs + 1e-10)).sum(dim=-1).mean()
        total_loss    += loss.item()
        total_entropy += entropy.item()
    model.train()
    return total_loss / steps, total_entropy / steps


# ============ 自我演化引擎 ============
class SelfEvolutionEngine:
    def __init__(self, model, env, optimizer, entropy_opt, device,
                 batch_size=4, save_path='best_model.pt',
                 patterns_path='best_patterns.npy'):
        self.model        = model
        self.env          = env
        self.optimizer   = optimizer
        self.entropy_opt = entropy_opt
        self.device      = device
        self.batch_size  = batch_size
        self.save_path    = save_path
        self.patterns_path = patterns_path
        self.best_loss   = float('inf')
        self.cur_epoch   = 0
        self.running     = False
        self.pause_flag  = False
        self.log         = []

    def _reset_collapsed_patterns(self):
        imp = self.model.regularity_lib.importance
        k = max(1, len(imp) // 10)
        _, worst_idx = torch.topk(imp, k, largest=False)
        device = self.model.regularity_lib.prototype_embeddings.device
        with torch.no_grad():
            for idx in worst_idx:
                self.model.regularity_lib.prototype_embeddings.data[idx] = \
                    torch.randn(self.model.hidden_dim, device=device) * 0.02
                self.model.regularity_lib.importance.data[idx] = 0.1

    def run_epochs(self, num_epochs, callback=None):
        self.running = True
        self.pause_flag = False
        for epoch in range(self.cur_epoch, self.cur_epoch + num_epochs):
            if not self.running:
                break
            while self.pause_flag and self.running:
                time.sleep(0.2)

            epoch_loss, epoch_entropy = 0.0, 0.0
            epoch_start = time.time()

            for step in range(50):
                if not self.running:
                    break
                x, y = self.env.generate_batch(self.batch_size)
                x, y = x.to(self.device), y.to(self.device)
                pred, probs, h = self.model(x)
                task_loss = F.mse_loss(pred, y.squeeze(-1))
                metrics = self.entropy_opt.step(probs, h, task_loss)
                epoch_loss    += metrics['total_loss']
                epoch_entropy += metrics['entropy']

            avg_loss    = epoch_loss / 50
            avg_entropy = epoch_entropy / 50
            epoch_time  = time.time() - epoch_start

            if avg_entropy < 0.05:
                self._reset_collapsed_patterns()
                self.log.append(f"  [演化] 熵过低({avg_entropy:.4f})，已重置部分原型")

            if avg_loss < self.best_loss:
                self.best_loss = avg_loss
                try:
                    torch.save(self.model.state_dict(), self.save_path)
                except Exception as e:
                    self.log.append(f"  [警告] 保存模型失败: {e}")
                try:
                    np.save(
                        self.patterns_path,
                        self.model.regularity_lib.prototype_embeddings.detach().cpu().numpy()
                    )
                except Exception as e:
                    self.log.append(f"  [警告] 保存原型失败: {e}")
                self.log.append(f"  [演化] 新最佳模型！loss={avg_loss:.6f}")

            self.cur_epoch += 1
            msg = (f"Epoch {self.cur_epoch}: "
                   f"loss={avg_loss:.6f}, entropy={avg_entropy:.6f}, "
                   f"time={epoch_time:.1f}s, best={self.best_loss:.6f}")
            self.log.append(msg)

            if callback:
                should_continue = callback(epoch, {
                    'epoch':       self.cur_epoch,
                    'loss':        avg_loss,
                    'entropy':     avg_entropy,
                    'best_loss':   self.best_loss,
                    'log':         msg,
                    'is_running':  self.running,
                })
                if should_continue is False:
                    break
        self.running = False

    def stop(self):
        self.running = False

    def pause(self):
        self.pause_flag = True

    def resume(self):
        self.pause_flag = False


# ============ 桌面 GUI ============
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox

    class IREAGIApp:
        def __init__(self, root):
            self.root = root
            self.root.title("IRE-AGI v4.0 — 武光衡理论 · 自我演化 AGI")
            self.root.geometry("920x680")
            self.root.configure(bg="#1a1a2e")
            self.root.protocol("WM_DELETE_WINDOW", self._on_quit)

            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model      = None
            self.env        = None
            self.optimizer  = None
            self.entropy_opt = None
            self.engine     = None
            self._init_model()
            self._build_ui()
            self._log(f"设备: {self.device}")
            self._log(f"模型参数: {sum(p.numel() for p in self.model.parameters()):,}")
            self._log("就绪。点击「开始演化」启动自我迭代。")

        def _init_model(self):
            import tempfile
            tmpdir = tempfile.gettempdir()
            self.model = IRE_AGI(input_dim=64, hidden_dim=256, num_patterns=32).to(self.device)
            self.env   = ContradictoryEnv(input_dim=64, seq_len=16)
            self.optimizer  = torch.optim.AdamW(self.model.parameters(), lr=1e-4)
            self.entropy_opt = ConsciousnessEntropyOptimizer(self.optimizer, entropy_target=0.5)
            self.engine = SelfEvolutionEngine(
                self.model, self.env, self.optimizer,
                self.entropy_opt, self.device,
                batch_size=4,
                save_path=os.path.join(tmpdir, 'ire_agi_best_model.pt'),
                patterns_path=os.path.join(tmpdir, 'ire_agi_best_patterns.npy'),
            )

        def _build_ui(self):
            # 标题
            tk.Label(
                self.root, text="🧠  IRE-AGI v4.0 　自我演化引擎",
                font=("Microsoft YaHei", 15, "bold"),
                fg="#e94560", bg="#1a1a2e"
            ).pack(pady=8)

            # 说明
            tk.Label(
                self.root,
                text="武光衡理论 · 意识熵优化 · 三维正则库 · 自我迭代演化",
                font=("Microsoft YaHei", 9), fg="#8888aa", bg="#1a1a2e"
            ).pack()

            # 控制区
            ctrl = tk.Frame(self.root, bg="#1a1a2e")
            ctrl.pack(pady=6)

            self.btn_start = tk.Button(
                ctrl, text="▶  开始演化", font=("Microsoft YaHei", 10),
                bg="#0f3460", fg="white", width=13,
                command=self._on_start
            )
            self.btn_start.pack(side=tk.LEFT, padx=4)

            self.btn_pause = tk.Button(
                ctrl, text="⏸  暂停", font=("Microsoft YaHei", 10),
                bg="#533483", fg="white", width=13, state=tk.DISABLED,
                command=self._on_pause
            )
            self.btn_pause.pack(side=tk.LEFT, padx=4)

            self.btn_stop = tk.Button(
                ctrl, text="■  停止", font=("Microsoft YaHei", 10),
                bg="#e94560", fg="white", width=13, state=tk.DISABLED,
                command=self._on_stop
            )
            self.btn_stop.pack(side=tk.LEFT, padx=4)

            # Epoch 输入
            tk.Label(ctrl, text="演化轮数:", font=("Microsoft YaHei", 9),
                     fg="#e0e0e0", bg="#1a1a2e").pack(side=tk.LEFT, padx=(12, 2))
            self.epoch_var = tk.StringVar(value="20")
            tk.Entry(ctrl, textvariable=self.epoch_var, width=5,
                     font=("Microsoft YaHei", 9), bg="#0a0a1a", fg="white",
                     insertbackground="white").pack(side=tk.LEFT)

            # 状态栏
            stat = tk.Frame(self.root, bg="#16213e", height=28)
            stat.pack(fill=tk.X, padx=10, pady=(8, 0))
            self.status_var = tk.StringVar(value="就绪")
            tk.Label(
                stat, textvariable=self.status_var,
                font=("Microsoft YaHei", 9), fg="#00d2ff", bg="#16213e", anchor=tk.W
            ).pack(fill=tk.X, padx=8, pady=4)

            # 日志区
            self.log_box = scrolledtext.ScrolledText(
                self.root, font=("Consolas", 9),
                bg="#0a0a1a", fg="#00ff88",
                insertbackground="white", wrap=tk.WORD,
                height=28
            )
            self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 8))

            # 底部指标
            mframe = tk.Frame(self.root, bg="#1a1a2e")
            mframe.pack(fill=tk.X, padx=10, pady=(0, 8))
            self.loss_var = tk.StringVar(value="Loss: —")
            self.ent_var  = tk.StringVar(value="Entropy: —")
            self.best_var = tk.StringVar(value="Best: —")
            for var, fg in [(self.loss_var, "#ff6b6b"),
                           (self.ent_var,  "#ffd93d"),
                           (self.best_var, "#6bcb77")]:
                tk.Label(
                    mframe, textvariable=var,
                    font=("Microsoft YaHei", 9), fg=fg, bg="#1a1a2e"
                ).pack(side=tk.LEFT, padx=14)

        def _log(self, text):
            self.log_box.insert(tk.END, text + "\n")
            self.log_box.see(tk.END)

        def _on_start(self):
            try:
                n_epochs = int(self.epoch_var.get())
            except ValueError:
                n_epochs = 20

            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.NORMAL)
            self.status_var.set(f"演化中... (目标 {n_epochs} 轮)")

            import threading
            def _worker():
                self.engine.run_epochs(n_epochs, callback=self._on_epoch_done)
                self.root.after(0, self._on_finished)
            t = threading.Thread(target=_worker, daemon=True)
            t.start()

        def _on_epoch_done(self, epoch, metrics):
            def _update():
                self.status_var.set(f"Epoch {metrics['epoch']} 完成")
                self.loss_var.set(f"Loss: {metrics['loss']:.6f}")
                self.ent_var.set( f"Entropy: {metrics['entropy']:.6f}")
                self.best_var.set(f"Best: {metrics['best_loss']:.6f}")
                self._log(metrics['log'])
            self.root.after(0, _update)
            return True

        def _on_finished(self):
            self.btn_start.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.DISABLED)
            self.status_var.set("演化完成 ✓")
            self._log(f"✅  最佳 Loss: {self.engine.best_loss:.6f}")
            self._log(f"   模型已保存 → best_model.pt / best_patterns.npy")

        def _on_pause(self):
            self.engine.pause()
            self.btn_pause.config(text="▶  继续", command=self._on_resume)
            self.status_var.set("已暂停")

        def _on_resume(self):
            self.engine.resume()
            self.btn_pause.config(text="⏸  暂停", command=self._on_pause)
            self.status_var.set("继续演化中...")

        def _on_stop(self):
            self.engine.stop()
            self.status_var.set("停止中...")

        def _on_quit(self):
            self.engine.stop()
            self.root.destroy()

    def launch_gui():
        root = tk.Tk()
        app = IREAGIApp(root)
        root.mainloop()

except ImportError:
    launch_gui = None


# ============ 命令行入口 ============
def main():
    import argparse
    parser = argparse.ArgumentParser(description="IRE-AGI v4.0 武光衡理论")
    parser.add_argument('--epochs',       type=int,   default=10)
    parser.add_argument('--batch-size',   type=int,   default=4)
    parser.add_argument('--hidden-dim',   type=int,   default=256)
    parser.add_argument('--num-patterns', type=int,   default=32)
    parser.add_argument('--save-checkpoint', type=str, default='best_model.pt')
    parser.add_argument('--save-patterns',  type=str, default='best_patterns.npy')
    parser.add_argument('--validate',     action='store_true')
    parser.add_argument('--config',       type=str,   default='config.json')
    parser.add_argument('--gui',          action='store_true', help='启动桌面 GUI')
    args = parser.parse_args()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"设备: {device}")

    if os.path.exists(args.config):
        with open(args.config) as f:
            cfg = json.load(f)
            args.batch_size   = cfg.get('batch_size',   args.batch_size)
            args.hidden_dim   = cfg.get('hidden_dim',   args.hidden_dim)
            args.num_patterns = cfg.get('num_patterns', args.num_patterns)

    model = IRE_AGI(
        input_dim=64, hidden_dim=args.hidden_dim, num_patterns=args.num_patterns
    ).to(device)
    env = ContradictoryEnv(input_dim=64, seq_len=16)
    optimizer   = torch.optim.AdamW(model.parameters(), lr=1e-4)
    entropy_opt = ConsciousnessEntropyOptimizer(optimizer, entropy_target=0.5)

    if args.save_checkpoint and os.path.exists(args.save_checkpoint):
        model.load_state_dict(torch.load(args.save_checkpoint, map_location=device))
        print(f"已加载检查点: {args.save_checkpoint}")

    if args.gui and launch_gui is not None:
        print("启动桌面 GUI...")
        launch_gui()
        return

    engine = SelfEvolutionEngine(
        model, env, optimizer, entropy_opt, device,
        batch_size=args.batch_size,
        save_path=args.save_checkpoint,
        patterns_path=args.save_patterns,
    )
    engine.run_epochs(args.epochs, callback=lambda e, m: (print(m['log']), True))

    if args.validate:
        test_env = ContradictoryEnv(input_dim=64, seq_len=16)
        val_loss, val_entropy = validate(model, test_env, device)
        print(f"验证: loss={val_loss:.6f}, entropy={val_entropy:.6f}")


if __name__ == "__main__":
    main()
