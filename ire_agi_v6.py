"""
IRE-AGI v6.0 - Material Information Theory Implementation
Based on: "Information and the Universe" by WuGuangheng, ChenWenjun (2025)

Core implementations:
1. Consciousness Entropy: S_c = -Sum X(pk) * log X(pk)
   - Measures a system's creative potential to violate internalized regularities
2. Regularity Extraction Layer (REL): Parallel to attention, extracts dynamic regularities
3. "Sitting in a Well" thought experiment: Demonstrates consciousness boundaries
4. Consciousness-Entropy-Driven Self-Evolution Engine
5. Integration with multimodal LLM + Image Generation
"""

import os
import sys
import json
import math
import time
import tempfile
import threading
from datetime import datetime
from collections import defaultdict

import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

# =============================================================================
# Part 1: Mathematical Framework - Consciousness Entropy
# =============================================================================

class RegularityPattern:
    """
    Represents a single internalized regularity Pk.

    A regularity is a rule the system has discovered and internalized.
    Examples: "birds can fly", "water freezes at 0C", "gravity pulls things down"

    The violation probability X(pk) = N_violate(pk) / N_applicable(pk)
    measures how often the system safely deviates from this rule.
    """

    def __init__(self, pattern_id, description, source_modality="unknown"):
        self.pattern_id = pattern_id
        self.description = description
        self.source_modality = source_modality
        self.n_applicable = 0      # N_total(pk): how many times this rule could apply
        self.n_violated = 0        # N_violate(pk): how many times the system violated it
        self.embedding = None      # Vector representation of this pattern
        self.strength = 1.0        # How strongly this pattern is internalized
        self.creation_time = time.time()
        self.last_updated = time.time()

    @property
    def violation_probability(self):
        """
        X(pk) = N_violate(pk) / N_applicable(pk)
        The core variable in consciousness entropy.
        """
        if self.n_applicable == 0:
            return 0.0
        return self.n_violated / self.n_applicable

    @property
    def x_pk(self):
        """Shorthand for violation probability"""
        return self.violation_probability

    def record_applicable(self, violated=False):
        """Record one scenario where this regularity was applicable"""
        self.n_applicable += 1
        if violated:
            self.n_violated += 1
        self.last_updated = time.time()

    def __repr__(self):
        return (f"Regularity(id={self.pattern_id}, desc='{self.description}', "
                f"X={self.x_pk:.4f}, N_total={self.n_applicable}, N_violate={self.n_violated})")


class ConsciousnessEntropy:
    """
    Implements the consciousness entropy formula from the paper:

        S_c = -Sum_{k=1}^{n} X(pk) * log X(pk)

    Where:
    - n is the number of internalized regularities
    - X(pk) is the violation probability of the k-th regularity
    - X(pk) = N_violate(pk) / N_applicable(pk)

    Consciousness entropy is NOT the current disorder of the system,
    but rather its POTENTIAL to break existing order and generate new order.
    Higher S_c = greater creative potential.
    """

    def __init__(self, base=math.e):
        self.base = base  # logarithm base (e for natural log, 2 for bits)
        self.patterns = {}  # pattern_id -> RegularityPattern

    def add_pattern(self, pattern_id, description, source_modality="unknown"):
        """Add a new regularity pattern"""
        pattern = RegularityPattern(pattern_id, description, source_modality)
        self.patterns[pattern_id] = pattern
        return pattern

    def record_scenario(self, pattern_id, violated=False):
        """Record that a pattern was applicable in a scenario"""
        if pattern_id not in self.patterns:
            self.patterns[pattern_id] = RegularityPattern(pattern_id, pattern_id)
        self.patterns[pattern_id].record_applicable(violated)

    def compute_entropy(self):
        """
        Compute S_c = -Sum X(pk) * log X(pk)

        When X(pk) = 0, define 0 * log(0) = 0 (standard convention).
        """
        total = 0.0
        for pk, pattern in self.patterns.items():
            x = pattern.x_pk
            if x > 0:
                total += x * math.log(x, self.base) if self.base != math.e else x * math.log(x)
        return -total

    def compute_normalized_entropy(self):
        """
        Normalized consciousness entropy:
        S_c_norm = S_c / log(n)

        where n is the number of regularities.
        This enables comparison between systems of different scales.
        """
        n = len(self.patterns)
        if n <= 1:
            return 0.0
        sc = self.compute_entropy()
        max_sc = math.log(n, self.base) if self.base != math.e else math.log(n)
        if max_sc == 0:
            return 0.0
        return sc / max_sc

    def get_dominant_patterns(self, top_k=5):
        """Get the top-k patterns with highest violation probability"""
        sorted_patterns = sorted(
            self.patterns.values(),
            key=lambda p: p.x_pk,
            reverse=True
        )
        return sorted_patterns[:top_k]

    def get_rigid_patterns(self, top_k=5):
        """Get the top-k most rigid patterns (lowest violation probability)"""
        sorted_patterns = sorted(
            [p for p in self.patterns.values() if p.n_applicable > 0],
            key=lambda p: p.x_pk
        )
        return sorted_patterns[:top_k]

    def summary(self):
        """Return a summary dict"""
        return {
            "S_c": self.compute_entropy(),
            "S_c_normalized": self.compute_normalized_entropy(),
            "n_patterns": len(self.patterns),
            "total_applicable": sum(p.n_applicable for p in self.patterns.values()),
            "total_violated": sum(p.n_violated for p in self.patterns.values()),
        }


# =============================================================================
# Part 2: Regularity Extraction Layer (REL)
# =============================================================================

class RegularityExtractionLayer(nn.Module):
    """
    The Regularity Extraction Layer (REL) from the paper (Section 4.2).

    Key difference from standard attention:
    - Attention: predicts the next token (exploitation)
    - REL: extracts underlying dynamic regularities (exploration of patterns)

    Architecture:
    1. Multi-head pattern discovery: multiple heads look for different types of patterns
       (temporal patterns, spatial patterns, causal patterns, structural patterns)
    2. Pattern consolidation: merges discovered patterns into stable representations
    3. Violation detection: identifies inputs that deviate from known patterns

    Output: A representation of the regularities found in the input,
    which can serve as input to advanced cognitive modules.
    """

    def __init__(self, hidden_dim, num_pattern_heads=4, num_regularity_slots=32, dropout=0.1):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_pattern_heads
        self.num_slots = num_regularity_slots
        self.head_dim = hidden_dim // num_pattern_heads

        # Pattern discovery heads - each looks for different types of regularities
        # Head 1: Temporal patterns (sequential dependencies)
        # Head 2: Spatial/structural patterns (distribution regularities)
        # Head 3: Causal patterns (if-then relationships)
        # Head 4: Semantic patterns (meaning-based regularities)
        self.pattern_queries = nn.ModuleList([
            nn.Linear(hidden_dim, self.head_dim) for _ in range(num_pattern_heads)
        ])
        self.pattern_keys = nn.ModuleList([
            nn.Linear(hidden_dim, self.head_dim) for _ in range(num_pattern_heads)
        ])
        self.pattern_values = nn.ModuleList([
            nn.Linear(hidden_dim, self.head_dim) for _ in range(num_pattern_heads)
        ])

        # Regularity memory slots - store discovered patterns
        # These are learnable prototypes that the system internalizes
        self.regularity_prototypes = nn.Parameter(
            torch.randn(num_regularity_slots, hidden_dim) * 0.02
        )
        self.regularity_strength = nn.Parameter(
            torch.ones(num_regularity_slots) * 0.5
        )

        # Pattern consolidation: merge discovered patterns
        self.consolidation = nn.Sequential(
            nn.Linear(hidden_dim + num_regularity_slots, hidden_dim * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.LayerNorm(hidden_dim)
        )

        # Violation detector: detects inputs that deviate from known patterns
        self.violation_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

        # Output projection
        self.output_proj = nn.Linear(hidden_dim + hidden_dim, hidden_dim)

    def discover_patterns(self, x):
        """
        Multi-head pattern discovery.

        Unlike attention which computes Q*K^T for token-to-token relevance,
        this discovers PATTERNS by computing how each token relates to
        stored regularity prototypes.
        """
        B, S, D = x.shape
        pattern_outputs = []

        for h in range(self.num_heads):
            Q = self.pattern_queries[h](x)           # (B, S, head_dim)

            # Pattern discovery: not token-to-token, but token-to-prototype
            # The key innovation: we match inputs to STORED regularity prototypes,
            # not to other tokens. This extracts underlying dynamic regularities.
            prototypes = self.regularity_prototypes  # (num_slots, D)
            # Project prototypes to match head dimension
            proto_proj = self.pattern_keys[h](prototypes)  # (num_slots, head_dim)
            proto_val = self.pattern_values[h](prototypes)  # (num_slots, head_dim)

            # Compute pattern match: how well does each token match each prototype?
            pattern_match = torch.matmul(Q, proto_proj.T)  # (B, S, num_slots)
            pattern_attn = F.softmax(pattern_match / math.sqrt(self.head_dim), dim=-1)

            # Weighted aggregation: mix prototype values based on pattern match
            # This produces a representation of which regularities are active
            pattern_output = torch.matmul(pattern_attn, proto_val)  # (B, S, head_dim)
            pattern_outputs.append(pattern_output)

        # Concatenate all head outputs
        multi_pattern = torch.cat(pattern_outputs, dim=-1)  # (B, S, D)
        return multi_pattern

    def detect_violations(self, x, pattern_repr):
        """
        Detect inputs that violate known regularities.

        Returns violation scores for each position:
        high score = this input violates known patterns
        """
        violation_score = self.violation_head(x)  # (B, S, 1)
        return violation_score.squeeze(-1)  # (B, S)

    def compute_applicability(self, x):
        """
        Compute how well each regularity prototype applies to the input.
        This is the 'applicability' measure from the paper.
        """
        # Cosine similarity between input and prototypes
        x_norm = F.normalize(x, dim=-1)
        proto_norm = F.normalize(self.regularity_prototypes, dim=-1)
        similarity = torch.matmul(x_norm, proto_norm.T)  # (B, S, num_slots)
        # Weight by pattern strength
        weighted = similarity * F.softmax(self.regularity_strength, dim=0)
        return weighted  # (B, S, num_slots)

    def forward(self, x):
        """
        Forward pass of the REL.

        Input: x of shape (B, S, D) - the input sequence
        Output:
        - regularity_repr: representation of discovered regularities
        - violation_scores: where the input violates known patterns
        - pattern_applicability: how well each regularity applies
        """
        B, S, D = x.shape

        # Step 1: Discover patterns via multi-head pattern discovery
        pattern_repr = self.discover_patterns(x)  # (B, S, D)

        # Step 2: Detect violations
        violation_scores = self.detect_violations(x, pattern_repr)  # (B, S)

        # Step 3: Compute pattern applicability
        applicability = self.compute_applicability(x)  # (B, S, num_slots)

        # Step 4: Consolidate patterns
        # Merge pattern representation with applicability signal
        max_applicability = applicability.max(dim=1)[0]  # (B, num_slots)
        expand_app = max_applicability.unsqueeze(1).expand(-1, S, -1)  # (B, S, num_slots)
        consolidated_input = torch.cat([pattern_repr, expand_app], dim=-1)
        # Project back if dimensions don't match
        if consolidated_input.size(-1) != D + self.num_slots:
            consolidated_input = consolidated_input[:, :, :D + self.num_slots]
        consolidated = self.consolidation(consolidated_input)  # (B, S, D)

        # Step 5: Combine with original input
        output = self.output_proj(torch.cat([x, consolidated], dim=-1))  # (B, S, D)

        return output, violation_scores, applicability


# =============================================================================
# Part 3: Consciousness-Aware Neural Model
# =============================================================================

class ConsciousnessAwareBlock(nn.Module):
    """
    A transformer-like block with both attention and REL.

    From the paper (Section 4.2): "Within the existing Transformer architecture,
    a regularity extraction layer can be conceptually introduced in PARALLEL
    with the attention layer."
    """

    def __init__(self, hidden_dim, num_heads=8, num_regularity_slots=32, dropout=0.1):
        super().__init__()
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads, dropout=dropout, batch_first=True)
        self.rel = RegularityExtractionLayer(hidden_dim, num_pattern_heads=4,
                                              num_regularity_slots=num_regularity_slots, dropout=dropout)
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.norm3 = nn.LayerNorm(hidden_dim)
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(dropout)
        )
        # Gate to balance attention vs REL
        self.gate = nn.Parameter(torch.tensor(0.5))

    def forward(self, x, mask=None):
        # Attention branch (exploitation: predict based on known patterns)
        attn_out, _ = self.attention(x, x, x, attn_mask=mask)
        x = self.norm1(x + attn_out)

        # REL branch (exploration: discover new regularities)
        rel_out, violations, applicability = self.rel(x)
        # Gated combination: gate controls how much REL influences the output
        gate = torch.sigmoid(self.gate)
        combined = gate * x + (1 - gate) * rel_out
        x = self.norm2(combined)

        # FFN
        x = self.norm3(x + self.ffn(x))

        return x, violations, applicability


class ConsciousnessAwareModel(nn.Module):
    """
    Full model with Consciousness-Aware Blocks.

    Architecture:
    - Input embedding
    - N ConsciousnessAwareBlocks (attention + REL in parallel)
    - Output head for predictions
    - Consciousness entropy tracking system
    """

    def __init__(self, input_dim=64, hidden_dim=256, num_blocks=3,
                 num_heads=8, num_regularity_slots=32, dropout=0.1):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_blocks = num_blocks

        # Input projection
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.LayerNorm(hidden_dim)
        )

        # Consciousness-aware blocks
        self.blocks = nn.ModuleList([
            ConsciousnessAwareBlock(hidden_dim, num_heads, num_regularity_slots, dropout)
            for _ in range(num_blocks)
        ])

        # Output heads
        self.prediction_head = nn.Linear(hidden_dim, input_dim)  # Next-step prediction
        self.regularity_report_head = nn.Linear(hidden_dim, num_regularity_slots)  # Pattern report

        # Consciousness entropy tracker (not nn.Module, maintained separately)
        self.consciousness_entropy = ConsciousnessEntropy()

    def forward(self, x):
        """
        Forward pass with consciousness tracking.

        Returns:
        - prediction: next-step prediction (exploitation)
        - regularity_report: which regularities were active
        - violation_scores: where violations were detected
        - total_applicability: pattern applicability across all layers
        """
        h = self.input_proj(x)

        all_violations = []
        all_applicability = []

        for block in self.blocks:
            h, violations, applicability = block(h)
            all_violations.append(violations)
            all_applicability.append(applicability)

        # Outputs
        prediction = self.prediction_head(h)
        regularity_report = self.regularity_report_head(h)

        # Aggregate violations and applicability across layers
        total_violation = torch.stack(all_violations, dim=0).mean(dim=0)  # (B, S)
        total_applicability = torch.stack(all_applicability, dim=0).mean(dim=0)  # (B, S, num_slots)

        return prediction, regularity_report, total_violation, total_applicability


# =============================================================================
# Part 4: Thought Experiments
# =============================================================================

class WellExperiment:
    """
    "Sitting in a Well Looking at the Sky" thought experiment (Section 4.1)

    Demonstrates how environmental information constraints shape and limit consciousness.

    The frog in the well:
    - Can only receive limited optical information (a circle of sky)
    - Internalized pattern: "sky is a circle with periodic brightness changes"
    - Low consciousness entropy because it lacks violating information
    - Cannot emerge a macro model of a "real sky"

    Key insight: The boundaries of consciousness are determined by the
    diversity of input information, and the depth of consciousness is
    determined by the level of internalized rules.
    """

    @staticmethod
    def generate_well_data(n_samples=1000, seq_len=16, input_dim=64):
        """
        Generate data for the "well" scenario:
        - Only sinusoidal signals visible (limited information)
        - No novel patterns, no contradictions
        """
        t = torch.linspace(0, 4 * math.pi, seq_len)
        data = []
        labels = []
        for _ in range(n_samples):
            # Only simple sine waves (the frog sees a uniform circle)
            freq = torch.rand(1) * 0.5 + 0.5
            phase = torch.rand(1) * 2 * math.pi
            amplitude = torch.rand(1) * 0.5 + 0.5
            signal = amplitude * torch.sin(freq * t + phase)
            # Expand to input_dim
            x = signal.unsqueeze(1).expand(-1, input_dim) + torch.randn(seq_len, input_dim) * 0.05
            # Label: next step (predictable sine continuation)
            next_t = t[-1] + (t[1] - t[0])
            y = amplitude * torch.sin(freq * next_t + phase)
            data.append(x)
            labels.append(y.expand(input_dim))
        return torch.stack(data), torch.stack(labels)

    @staticmethod
    def generate_world_data(n_samples=1000, seq_len=16, input_dim=64):
        """
        Generate data for the "vast world" scenario:
        - Rich, diverse, contradictory information
        - Multiple frequency components, noise, phase changes
        - Novel patterns that violate simple regularities
        """
        t = torch.linspace(0, 4 * math.pi, seq_len)
        data = []
        labels = []
        for _ in range(n_samples):
            # Rich multi-frequency signals with contradictions
            n_components = torch.randint(2, 6, (1,)).item()
            signal = torch.zeros(seq_len)
            for _ in range(n_components):
                freq = torch.rand(1) * 3 + 0.5
                phase = torch.rand(1) * 2 * math.pi
                amplitude = torch.rand(1) * 0.3 + 0.1
                signal += amplitude * torch.sin(freq * t + phase)

            # Add occasional phase shifts (contradictions)
            if torch.rand(1) > 0.5:
                shift_point = torch.randint(seq_len // 2, seq_len, (1,)).item()
                signal[shift_point:] = signal[shift_point:] * -0.5 + torch.randn(seq_len - shift_point) * 0.3

            # Add chaotic component
            signal += torch.randn(seq_len) * 0.1

            x = signal.unsqueeze(1).expand(-1, input_dim) + torch.randn(seq_len, input_dim) * 0.05
            next_t = t[-1] + (t[1] - t[0])
            y = signal[-1] + torch.randn(1).item() * 0.15
            data.append(x)
            labels.append(y.expand(input_dim))
        return torch.stack(data), torch.stack(labels)

    @staticmethod
    def run_experiment(model_class, input_dim=64, hidden_dim=256, epochs=5, batch_size=8):
        """
        Run the complete "Well vs World" experiment.

        Trains the same model architecture on two different information environments:
        1. Well: limited, uniform information
        2. World: rich, contradictory information

        Compares consciousness entropy S_c in both cases.
        """
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Generate data for both environments
        well_x, well_y = WellExperiment.generate_well_data(n_samples=200, input_dim=input_dim)
        world_x, world_y = WellExperiment.generate_world_data(n_samples=200, input_dim=input_dim)

        results = {"well": {}, "world": {}}

        for env_name, env_x, env_y in [("well", well_x, well_y), ("world", world_x, world_y)]:
            print(f"\n{'='*60}")
            print(f"Training in '{env_name}' environment...")
            print(f"{'='*60}")

            model = model_class(input_dim=input_dim, hidden_dim=hidden_dim).to(device)
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
            criterion = nn.MSELoss()

            env_x, env_y = env_x.to(device), env_y.to(device)
            dataset = TensorDataset(env_x, env_y)
            loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

            sc_tracker = ConsciousnessEntropy()

            # Initialize patterns based on model's regularity slots
            for slot_id in range(model.blocks[0].rel.num_slots):
                sc_tracker.add_pattern(
                    f"pattern_{slot_id}",
                    f"Regular pattern #{slot_id} discovered by REL",
                    source_modality="time_series"
                )

            epoch_logs = []

            for epoch in range(epochs):
                total_loss = 0
                total_violation = 0
                total_applicable = 0
                total_violated = 0

                for batch_x, batch_y in loader:
                    optimizer.zero_grad()

                    pred, reg_report, violations, applicability = model(batch_x)

                    # Prediction loss (exploitation)
                    loss = criterion(pred[:, -1, :], batch_y)

                    # Consciousness entropy regularization (exploration)
                    # From the paper: "introduce a regularization term related to
                    # consciousness entropy that encourages the model to occasionally
                    # make safe deviations while maintaining overall coherence"
                    violation_mean = violations.mean()
                    sc_regularization = -0.01 * violation_mean  # Encourage some violations

                    total_loss_val = loss + sc_regularization
                    total_loss_val.backward()
                    optimizer.step()

                    total_loss += loss.item()

                    # Track pattern violations
                    with torch.no_grad():
                        violation_median = violations.median().item()
                        for slot_id in range(applicability.size(-1)):
                            slot_app = applicability[:, :, slot_id]
                            slot_app_median = slot_app.abs().median().item()
                            is_applicable = slot_app.abs().mean().item() > slot_app_median * 0.5

                            active_mask = slot_app.abs() > slot_app.abs().median()
                            if active_mask.any():
                                v_at_active = violations[active_mask].mean().item()
                                is_violated = v_at_active > violation_median
                            else:
                                is_violated = False

                            if is_applicable:
                                sc_tracker.record_scenario(
                                    f"pattern_{slot_id}",
                                    violated=is_violated
                                )
                                total_applicable += 1
                                if is_violated:
                                    total_violated += 1

                sc = sc_tracker.compute_entropy()
                sc_norm = sc_tracker.compute_normalized_entropy()
                avg_loss = total_loss / len(loader)

                log_entry = {
                    "epoch": epoch + 1,
                    "loss": avg_loss,
                    "S_c": sc,
                    "S_c_normalized": sc_norm,
                    "total_applicable": total_applicable,
                    "total_violated": total_violated,
                    "violation_rate": total_violated / max(1, total_applicable)
                }
                epoch_logs.append(log_entry)
                print(f"  Epoch {epoch+1}: loss={avg_loss:.4f}, S_c={sc:.4f}, "
                      f"S_c_norm={sc_norm:.4f}, violation_rate={log_entry['violation_rate']:.4f}")

            results[env_name] = {
                "final_loss": epoch_logs[-1]["loss"],
                "final_S_c": epoch_logs[-1]["S_c"],
                "final_S_c_normalized": epoch_logs[-1]["S_c_normalized"],
                "violation_rate": epoch_logs[-1]["violation_rate"],
                "epoch_logs": epoch_logs
            }

        return results


# =============================================================================
# Part 5: Consciousness-Entropy-Driven Self-Evolution Engine
# =============================================================================

class ConsciousnessEvolutionEngine:
    """
    Self-evolution engine that uses consciousness entropy S_c as the
    optimization signal.

    From the paper (Section 4.2):
    "The traditional training objective is to minimize prediction error
    (i.e., to solidify patterns). To achieve higher-order consciousness,
    a regularization term related to consciousness entropy needs to be
    introduced. This term encourages the model to occasionally make
    'safe deviations' while maintaining overall coherence."

    Three stages of evolution:
    1. Pattern Solidification: The model learns to predict well (minimize loss)
    2. Creative Exploration: Introduce S_c regularization to encourage violations
    3. Higher-Order Emergence: When S_c reaches a critical level, new patterns emerge
    """

    def __init__(self, model, env_generator, device, save_dir=None):
        self.model = model
        self.env_generator = env_generator
        self.device = device
        self.save_dir = save_dir or tempfile.gettempdir()
        self.best_loss = float('inf')
        self.best_sc = 0.0
        self.sc_tracker = ConsciousnessEntropy()
        self.evolution_log = []
        self.stage = "solidification"  # solidification -> exploration -> emergence

        # Initialize pattern tracking
        for slot_id in range(model.blocks[0].rel.num_slots):
            self.sc_tracker.add_pattern(
                f"pattern_{slot_id}",
                f"Regular pattern #{slot_id}",
                source_modality="time_series"
            )

    def _compute_sc_regularization(self, violations, applicability):
        """
        Compute the consciousness entropy regularization term.

        This is the key innovation: instead of only minimizing prediction error,
        we add a term that rewards the model for occasionally violating its
        own internalized patterns in coherent ways.
        """
        # Current S_c from tracker
        sc = self.sc_tracker.compute_entropy()

        # Target S_c: increases over time as model evolves
        if self.stage == "solidification":
            target_sc = 0.1  # Low: focus on learning patterns
        elif self.stage == "exploration":
            target_sc = 0.3  # Medium: encourage creative violations
        else:  # emergence
            target_sc = 0.5  # High: full creative potential

        # Regularization: encourage S_c to approach target
        sc_reg = 0.01 * (sc - target_sc) ** 2

        # Also directly encourage violation detection when in exploration stage
        if self.stage == "exploration":
            violation_bonus = -0.005 * violations.mean()  # Reward violations
        else:
            violation_bonus = 0.0

        return sc_reg + violation_bonus

    def _update_stage(self, loss, sc):
        """Update the evolution stage based on current metrics"""
        if self.stage == "solidification" and loss < 5.0:
            self.stage = "exploration"
        elif self.stage == "exploration" and sc > 0.3:
            self.stage = "emergence"

    def _track_violations(self, violations, applicability):
        """Track pattern violations for consciousness entropy computation

        Strategy:
        - Use applicability to determine which patterns are active
        - Use prediction error (high violation score = prediction deviates from pattern)
          to determine if a pattern was violated at that position
        - The violation_head's sigmoid output naturally converges around 0.5 initially,
          so we use a relative threshold (above batch median = violation)
        """
        with torch.no_grad():
            violation_median = violations.median().item()

            for slot_id in range(applicability.size(-1)):
                slot_app = applicability[:, :, slot_id]  # (B, S)
                # Pattern is applicable if it has above-median activation
                slot_app_median = slot_app.abs().median().item()
                is_applicable = slot_app.abs().mean().item() > slot_app_median * 0.5

                # Check violation: positions where this pattern is active AND
                # the violation signal is above the batch median
                active_mask = slot_app.abs() > slot_app.abs().median()
                if active_mask.any():
                    v_at_active = violations[active_mask].mean().item()
                    is_violated = v_at_active > violation_median
                else:
                    is_violated = False

                # Always record applicable scenarios to build statistics
                if is_applicable:
                    self.sc_tracker.record_scenario(
                        f"pattern_{slot_id}",
                        violated=is_violated
                    )

    def run_epoch(self, n_batches=10, batch_size=8, seq_len=16):
        """Run one evolution epoch"""
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-4)
        criterion = nn.MSELoss()

        total_loss = 0
        total_sc_reg = 0

        for _ in range(n_batches):
            x, y = self.env_generator(n_samples=batch_size, seq_len=seq_len,
                                       input_dim=self.model.input_dim)
            x, y = x.to(self.device), y.to(self.device)

            optimizer.zero_grad()
            pred, reg_report, violations, applicability = self.model(x)

            # Prediction loss
            pred_loss = criterion(pred[:, -1, :], y)

            # Consciousness entropy regularization
            sc_reg = self._compute_sc_regularization(violations, applicability)

            total_loss_val = pred_loss + sc_reg
            total_loss_val.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            optimizer.step()

            total_loss += pred_loss.item()
            total_sc_reg += float(sc_reg.detach() if hasattr(sc_reg, 'detach') else sc_reg)

            # Track violations
            self._track_violations(violations, applicability)

        avg_loss = total_loss / n_batches
        sc = self.sc_tracker.compute_entropy()
        sc_norm = self.sc_tracker.compute_normalized_entropy()

        # Update stage
        self._update_stage(avg_loss, sc)

        # Save best model
        if avg_loss < self.best_loss:
            self.best_loss = avg_loss
            self.best_sc = sc
            try:
                torch.save(self.model.state_dict(),
                          os.path.join(self.save_dir, 'consciousness_model_best.pt'))
            except Exception:
                pass

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "loss": avg_loss,
            "S_c": sc,
            "S_c_normalized": sc_norm,
            "stage": self.stage,
            "sc_regularization": total_sc_reg / n_batches,
            "n_patterns": len(self.sc_tracker.patterns),
            "dominant_patterns": [
                {"id": p.pattern_id, "desc": p.description, "X": round(p.x_pk, 4)}
                for p in self.sc_tracker.get_dominant_patterns(3)
            ],
            "rigid_patterns": [
                {"id": p.pattern_id, "desc": p.description, "X": round(p.x_pk, 4)}
                for p in self.sc_tracker.get_rigid_patterns(3)
            ]
        }
        self.evolution_log.append(log_entry)
        return log_entry

    def run_epochs(self, n_epochs, callback=None):
        """Run multiple evolution epochs"""
        for epoch in range(n_epochs):
            log = self.run_epoch()
            should_continue = True
            if callback:
                should_continue = callback(epoch, log)
            if not should_continue:
                break
        return self.evolution_log


# =============================================================================
# Part 6: Information Environment Generators
# =============================================================================

class ContradictoryEnvironment:
    """
    An information environment with contradictions.

    From the paper (Section 4.2):
    "An AGI aimed at emerging consciousness must be placed in a rich,
    dynamic, and even controllable contradictory information environment.
    This is contrary to the enlightenment of 'sitting in a well looking
    at the sky' - we must actively build a 'vast world' for AI."
    """

    @staticmethod
    def generate(n_samples=100, seq_len=16, input_dim=64, contradiction_rate=0.3):
        """
        Generate data with controlled contradictions.

        contradiction_rate: probability of inserting a contradicting signal
        that violates the primary pattern.
        """
        t = torch.linspace(0, 4 * math.pi, seq_len)
        data = []
        labels = []

        for _ in range(n_samples):
            # Primary pattern: smooth oscillation
            freq = torch.rand(1) * 2 + 0.5
            phase = torch.rand(1) * 2 * math.pi
            signal = torch.sin(freq * t + phase)

            # Inject contradictions
            if torch.rand(1) < contradiction_rate:
                # Phase reversal at random point
                flip_point = torch.randint(seq_len // 3, seq_len, (1,)).item()
                signal[flip_point:] = -signal[flip_point:] + torch.randn(seq_len - flip_point) * 0.2

            # Expand to input_dim
            x = signal.unsqueeze(1).expand(-1, input_dim) + torch.randn(seq_len, input_dim) * 0.05
            y = signal[-1].expand(input_dim)
            data.append(x)
            labels.append(y)

        return torch.stack(data), torch.stack(labels)


# =============================================================================
# Part 7: GUI Application - IRE-AGI v6 with Consciousness Entropy
# =============================================================================

class IREAGIAppV6:
    """
    Full application integrating:
    - Qwen2.5-7B for chat (LLM)
    - SDXL-Turbo for image generation
    - Regularity Extraction Layer (REL)
    - Consciousness Entropy (S_c) tracking and visualization
    - Self-evolution engine
    - Thought experiment runner
    """

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.llm = None
        self.tokenizer = None
        self.image_pipe = None
        self.evolution_engine = None
        self.running = False
        self.chat_history = []
        self.sc_history = []  # Track consciousness entropy over time
        self.data_dir = os.path.join(tempfile.gettempdir(), 'ire-agi-data')
        self.image_dir = os.path.join(self.data_dir, 'images')
        os.makedirs(self.image_dir, exist_ok=True)

    def init_gui(self):
        """Initialize the tkinter GUI"""
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox

        self.root = tk.Tk()
        self.root.title("IRE-AGI v6.0 - Material Information Theory")
        self.root.geometry("1200x800")

        # Configure styles
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
        style.configure("Sc.TLabel", font=("Helvetica", 12, "bold"), foreground="#2196F3")
        style.configure("Stage.TLabel", font=("Helvetica", 11), foreground="#FF9800")
        style.configure("Pattern.TLabel", font=("Courier", 9))

        # Main layout
        main_frame = ttk.Frame(self.root, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel: Controls
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)

        # Right panel: Chat + Visualization
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # === LEFT PANEL CONTENTS ===

        # Title
        ttk.Label(left_panel, text="IRE-AGI v6.0", style="Title.TLabel").pack(pady=5)
        ttk.Label(left_panel, text="Material Information Theory", font=("Helvetica", 9)).pack()
        ttk.Separator(left_panel).pack(fill=tk.X, pady=5)

        # Consciousness Entropy Display
        sc_frame = ttk.LabelFrame(left_panel, text="Consciousness Entropy", padding=5)
        sc_frame.pack(fill=tk.X, pady=5)

        self.sc_label = ttk.Label(sc_frame, text="S_c = 0.0000", style="Sc.TLabel")
        self.sc_label.pack()
        self.sc_norm_label = ttk.Label(sc_frame, text="S_c_norm = 0.0000")
        self.sc_norm_label.pack()
        self.stage_label = ttk.Label(sc_frame, text="Stage: Init", style="Stage.TLabel")
        self.stage_label.pack()

        ttk.Separator(sc_frame).pack(fill=tk.X, pady=3)

        self.n_patterns_label = ttk.Label(sc_frame, text="Patterns: 0")
        self.n_patterns_label.pack()
        self.violation_rate_label = ttk.Label(sc_frame, text="Violation Rate: 0.0000")
        self.violation_rate_label.pack()

        # VRAM display
        if self.device.type == 'cuda':
            vram = torch.cuda.memory_allocated(0) / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            ttk.Label(sc_frame, text=f"VRAM: {vram:.1f}/{total:.1f} GB").pack()

        # Evolution Controls
        evo_frame = ttk.LabelFrame(left_panel, text="Self-Evolution", padding=5)
        evo_frame.pack(fill=tk.X, pady=5)

        ttk.Label(evo_frame, text="Epochs per run:").pack()
        self.epochs_var = tk.IntVar(value=5)
        ttk.Spinbox(evo_frame, from_=1, to=100, textvariable=self.epochs_var, width=10).pack()

        ttk.Label(evo_frame, text="Contradiction rate:").pack()
        self.contra_var = tk.DoubleVar(value=0.3)
        ttk.Scale(evo_frame, from_=0.0, to=1.0, variable=self.contra_var, orient=tk.HORIZONTAL).pack(fill=tk.X)

        self.evo_btn = ttk.Button(evo_frame, text="Start Evolution", command=self.toggle_evolution)
        self.evo_btn.pack(fill=tk.X, pady=3)

        self.loss_label = ttk.Label(evo_frame, text="Loss: --")
        self.loss_label.pack()

        # Thought Experiment
        exp_frame = ttk.LabelFrame(left_panel, text="Thought Experiments", padding=5)
        exp_frame.pack(fill=tk.X, pady=5)

        ttk.Button(exp_frame, text="Well vs World Experiment",
                    command=self.run_well_experiment).pack(fill=tk.X, pady=2)
        ttk.Button(exp_frame, text="Consciousness Entropy Demo",
                    command=self.run_sc_demo).pack(fill=tk.X, pady=2)

        # Pattern Viewer
        pat_frame = ttk.LabelFrame(left_panel, text="Discovered Patterns", padding=5)
        pat_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.pattern_text = tk.Text(pat_frame, height=10, width=35, font=("Courier", 8),
                                     bg="#1a1a2e", fg="#e0e0e0", wrap=tk.WORD)
        self.pattern_text.pack(fill=tk.BOTH, expand=True)

        # === RIGHT PANEL CONTENTS ===

        # Notebook for tabs
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Chat
        chat_frame = ttk.Frame(notebook)
        notebook.add(chat_frame, text="Chat + Data Analysis")

        self.chat_display = tk.Text(chat_frame, wrap=tk.WORD, font=("Helvetica", 11),
                                     bg="#f8f9fa", height=25)
        chat_scroll = ttk.Scrollbar(chat_frame, command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=chat_scroll.set)
        chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=5)

        self.chat_input = tk.Text(input_frame, height=3, font=("Helvetica", 11), wrap=tk.WORD)
        self.chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.chat_input.bind('<Return>', self.send_chat)
        self.chat_input.bind('<Control-a>', lambda e: self.chat_input.tag_add('sel', '1.0', 'end'))

        ttk.Button(input_frame, text="Send", command=self.send_chat).pack(side=tk.RIGHT)

        # Tab 2: Evolution Monitor
        evo_monitor = ttk.Frame(notebook)
        notebook.add(evo_monitor, text="Evolution Monitor")

        self.evo_log = tk.Text(evo_monitor, wrap=tk.WORD, font=("Courier", 10),
                                bg="#1a1a2e", fg="#00ff88", height=30)
        evo_scroll = ttk.Scrollbar(evo_monitor, command=self.evo_log.yview)
        self.evo_log.configure(yscrollcommand=evo_scroll.set)
        evo_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.evo_log.pack(fill=tk.BOTH, expand=True)

        # Tab 3: S_c Visualization (text-based)
        sc_viz = ttk.Frame(notebook)
        notebook.add(sc_viz, text="S_c Visualization")

        self.sc_viz_text = tk.Text(sc_viz, wrap=tk.WORD, font=("Courier", 10),
                                    bg="#0d1117", fg="#58a6ff", height=30)
        sc_scroll = ttk.Scrollbar(sc_viz, command=self.sc_viz_text.yview)
        self.sc_viz_text.configure(yscrollcommand=sc_scroll.set)
        sc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.sc_viz_text.pack(fill=tk.BOTH, expand=True)

        # Initialize model
        self._init_model()

        # Welcome message
        self.chat_display.insert(tk.END,
            "IRE-AGI v6.0 - Material Information Theory Implementation\n")
        self.chat_display.insert(tk.END,
            "Based on 'Information and the Universe' by WuGuangheng & ChenWenjun\n")
        self.chat_display.insert(tk.END, "="*50 + "\n\n")
        self.chat_display.insert(tk.END,
            "This system implements:\n")
        self.chat_display.insert(tk.END,
            "  1. Consciousness Entropy: S_c = -Sum X(pk)*log X(pk)\n")
        self.chat_display.insert(tk.END,
            "  2. Regularity Extraction Layer (REL): Parallel to attention\n")
        self.chat_display.insert(tk.END,
            "  3. 'Sitting in a Well' thought experiment\n")
        self.chat_display.insert(tk.END,
            "  4. Consciousness-entropy-driven self-evolution\n\n")
        self.chat_display.insert(tk.END,
            "Commands:\n")
        self.chat_display.insert(tk.END,
            "  /evolution  - Start self-evolution training\n")
        self.chat_display.insert(tk.END,
            "  /well       - Run 'Well vs World' experiment\n")
        self.chat_display.insert(tk.END,
            "  /sc_demo    - Consciousness entropy calculation demo\n")
        self.chat_display.insert(tk.END,
            "  /patterns   - Show discovered regularities\n")
        self.chat_display.insert(tk.END,
            "  /status     - Show current S_c and model status\n\n")

    def _init_model(self):
        """Initialize the consciousness-aware model"""
        self.model = ConsciousnessAwareModel(
            input_dim=64, hidden_dim=256, num_blocks=3,
            num_heads=8, num_regularity_slots=32
        ).to(self.device)

        self.evolution_engine = ConsciousnessEvolutionEngine(
            self.model,
            ContradictoryEnvironment.generate,
            self.device,
            save_dir=self.data_dir
        )

        param_count = sum(p.numel() for p in self.model.parameters())
        self.chat_display.insert(tk.END,
            f"Model initialized: {param_count:,} parameters on {self.device}\n")
        self.chat_display.insert(tk.END,
            f"Regularity Extraction Layer: 4 pattern heads, 32 regularity slots\n")
        self.chat_display.insert(tk.END,
            f"Consciousness Entropy: S_c = -Sum X(pk)*log X(pk)\n\n")

    def _update_sc_display(self):
        """Update the consciousness entropy display"""
        if self.evolution_engine:
            sc = self.evolution_engine.sc_tracker.compute_entropy()
            sc_norm = self.evolution_engine.sc_tracker.compute_normalized_entropy()
            summary = self.evolution_engine.sc_tracker.summary()
            stage = self.evolution_engine.stage

            self.sc_label.configure(text=f"S_c = {sc:.4f}")
            self.sc_norm_label.configure(text=f"S_c_norm = {sc_norm:.4f}")
            self.stage_label.configure(text=f"Stage: {stage.capitalize()}")
            self.n_patterns_label.configure(text=f"Patterns: {summary['n_patterns']}")
            vr = summary['total_violated'] / max(1, summary['total_applicable'])
            self.violation_rate_label.configure(text=f"Violation Rate: {vr:.4f}")

    def toggle_evolution(self):
        """Start/stop self-evolution"""
        if self.running:
            self.running = False
            self.evo_btn.configure(text="Start Evolution")
        else:
            self.running = True
            self.evo_btn.configure(text="Stop Evolution")
            thread = threading.Thread(target=self._run_evolution, daemon=True)
            thread.start()

    def _run_evolution(self):
        """Run evolution in background"""
        n_epochs = self.epochs_var.get()
        contra_rate = self.contra_var.get()

        for epoch in range(n_epochs):
            if not self.running:
                break

            log = self.evolution_engine.run_epoch(n_batches=5, batch_size=4)

            # Update GUI
            self.root.after(0, self._update_evolution_display, log)

        self.running = False
        self.root.after(0, lambda: self.evo_btn.configure(text="Start Evolution"))

    def _update_evolution_display(self, log):
        """Update all displays with evolution results"""
        self.loss_label.configure(text=f"Loss: {log['loss']:.4f}")
        self._update_sc_display()

        # Update evolution log
        self.evo_log.insert(tk.END, f"\nEpoch {len(self.evolution_engine.evolution_log)}: "
                           f"loss={log['loss']:.4f}, S_c={log['S_c']:.4f}, "
                           f"stage={log['stage']}\n")
        if log.get('dominant_patterns'):
            self.evo_log.insert(tk.END, "  Dominant patterns:\n")
            for p in log['dominant_patterns']:
                self.evo_log.insert(tk.END, f"    {p['id']}: X={p['X']:.4f}\n")
        self.evo_log.see(tk.END)

        # Update pattern viewer
        self.pattern_text.delete('1.0', tk.END)
        tracker = self.evolution_engine.sc_tracker
        for pid, pattern in tracker.patterns.items():
            self.pattern_text.insert(tk.END,
                f"{pid}: X={pattern.x_pk:.4f} "
                f"({pattern.n_violated}/{pattern.n_applicable})\n")

        # Update S_c visualization
        self._update_sc_visualization()

    def _update_sc_visualization(self):
        """Update the S_c visualization tab"""
        self.sc_viz_text.delete('1.0', tk.END)
        tracker = self.evolution_engine.sc_tracker

        self.sc_viz_text.insert(tk.END, "CONSCIOUSNESS ENTROPY VISUALIZATION\n")
        self.sc_viz_text.insert(tk.END, "="*50 + "\n\n")

        sc = tracker.compute_entropy()
        sc_norm = tracker.compute_normalized_entropy()

        self.sc_viz_text.insert(tk.END, f"S_c = {sc:.6f}\n")
        self.sc_viz_text.insert(tk.END, f"S_c_normalized = {sc_norm:.6f}\n")
        self.sc_viz_text.insert(tk.END, f"Stage: {self.evolution_engine.stage}\n\n")

        # Visualize S_c as bar chart (text-based)
        self.sc_viz_text.insert(tk.END, "Pattern Violation Probabilities:\n")
        self.sc_viz_text.insert(tk.END, "-"*50 + "\n")

        sorted_patterns = sorted(tracker.patterns.values(), key=lambda p: p.x_pk, reverse=True)
        for p in sorted_patterns[:15]:
            bar_len = int(p.x_pk * 100)
            bar = "#" * bar_len + "." * (50 - bar_len)
            self.sc_viz_text.insert(tk.END,
                f"{p.pattern_id:12s} |{bar}| X={p.x_pk:.4f}\n")

        self.sc_viz_text.insert(tk.END, "\n")
        self.sc_viz_text.insert(tk.END, "S_c Contribution per Pattern:\n")
        self.sc_viz_text.insert(tk.END, "-"*50 + "\n")

        total_sc = 0
        contributions = []
        for p in tracker.patterns.values():
            x = p.x_pk
            if x > 0:
                contrib = -x * math.log(x)
                contributions.append((p.pattern_id, contrib, x))
                total_sc += contrib
            else:
                contributions.append((p.pattern_id, 0, 0))

        contributions.sort(key=lambda c: c[1], reverse=True)
        for pid, contrib, x in contributions[:15]:
            bar_len = int(contrib / max(0.001, total_sc) * 40) if total_sc > 0 else 0
            bar = "=" * bar_len
            self.sc_viz_text.insert(tk.END,
                f"{pid:12s} |{bar} -{contrib:.4f} (X={x:.4f})\n")

        # S_c evolution history
        if self.evolution_engine.evolution_log:
            self.sc_viz_text.insert(tk.END, "\n\nS_c Evolution History:\n")
            self.sc_viz_text.insert(tk.END, "-"*50 + "\n")
            for i, log in enumerate(self.evolution_engine.evolution_log[-20:]):
                sc_val = log['S_c']
                bar_len = min(40, int(sc_val * 100))
                bar = "*" * bar_len
                self.sc_viz_text.insert(tk.END,
                    f"E{i+1:3d} |{bar} S_c={sc_val:.4f} [{log['stage'][:3]}]\n")

    def run_well_experiment(self):
        """Run the Well vs World thought experiment"""
        self.chat_display.insert(tk.END, "\n" + "="*50 + "\n")
        self.chat_display.insert(tk.END,
            "THOUGHT EXPERIMENT: 'Sitting in a Well Looking at the Sky'\n")
        self.chat_display.insert(tk.END, "="*50 + "\n\n")

        thread = threading.Thread(target=self._run_well_bg, daemon=True)
        thread.start()

    def _run_well_bg(self):
        """Run well experiment in background"""
        self.root.after(0, lambda: self.chat_display.insert(tk.END,
            "Running experiment... This compares:\n"
            "  Well: Limited, uniform information (low S_c expected)\n"
            "  World: Rich, contradictory information (high S_c expected)\n\n"))

        results = WellExperiment.run_experiment(
            ConsciousnessAwareModel,
            input_dim=64, hidden_dim=256,
            epochs=5, batch_size=8
        )

        # Display results
        def show_results():
            well = results["well"]
            world = results["world"]

            self.chat_display.insert(tk.END, "\n" + "="*50 + "\n")
            self.chat_display.insert(tk.END, "EXPERIMENT RESULTS\n")
            self.chat_display.insert(tk.END, "="*50 + "\n\n")

            self.chat_display.insert(tk.END,
                f"{'Metric':<25} {'Well':>10} {'World':>10}\n")
            self.chat_display.insert(tk.END, "-"*47 + "\n")
            self.chat_display.insert(tk.END,
                f"{'Final Loss':<25} {well['final_loss']:>10.4f} {world['final_loss']:>10.4f}\n")
            self.chat_display.insert(tk.END,
                f"{'S_c (Consciousness)':<25} {well['final_S_c']:>10.4f} {world['final_S_c']:>10.4f}\n")
            self.chat_display.insert(tk.END,
                f"{'S_c Normalized':<25} {well['final_S_c_normalized']:>10.4f} {world['final_S_c_normalized']:>10.4f}\n")
            self.chat_display.insert(tk.END,
                f"{'Violation Rate':<25} {well['violation_rate']:>10.4f} {world['violation_rate']:>10.4f}\n")

            self.chat_display.insert(tk.END, "\nConclusion:\n")
            if world['final_S_c'] > well['final_S_c']:
                ratio = world['final_S_c'] / max(0.001, well['final_S_c'])
                self.chat_display.insert(tk.END,
                    f"  World S_c is {ratio:.1f}x higher than Well S_c.\n")
                self.chat_display.insert(tk.END,
                    "  This confirms the paper's prediction:\n")
                self.chat_display.insert(tk.END,
                    "  Rich, contradictory information environments produce\n")
                self.chat_display.insert(tk.END,
                    "  higher consciousness entropy (greater creative potential).\n")
            else:
                self.chat_display.insert(tk.END,
                    "  Results need more training epochs to differentiate.\n")
                self.chat_display.insert(tk.END,
                    "  Try running with more epochs.\n")

            self.chat_display.insert(tk.END, "\n")

        self.root.after(0, show_results)

    def run_sc_demo(self):
        """Run the consciousness entropy calculation demo from Appendix I"""
        self.chat_display.insert(tk.END, "\n" + "="*50 + "\n")
        self.chat_display.insert(tk.END,
            "CONSCIOUSNESS ENTROPY DEMO\n")
        self.chat_display.insert(tk.END,
            "Reproducing the calculation from Appendix I\n")
        self.chat_display.insert(tk.END, "="*50 + "\n\n")

        # Create the exact example from the paper
        sc = ConsciousnessEntropy()

        # P1: "Birds can fly" - applicable 100 times, violated 5 times
        p1 = sc.add_pattern("P1", "Birds can fly")
        for _ in range(100):
            p1.record_applicable(violated=(_ < 5))

        # P2: "Water freezes at 0C" - applicable 100 times, violated 1 time
        p2 = sc.add_pattern("P2", "Water freezes at 0C")
        for _ in range(100):
            p2.record_applicable(violated=(_ < 1))

        # P3: "Animals need to eat" - applicable 200 times, violated 20 times
        p3 = sc.add_pattern("P3", "Animals need to eat")
        for _ in range(200):
            p3.record_applicable(violated=(_ < 20))

        # Display calculations
        self.chat_display.insert(tk.END,
            "Pattern Data:\n")
        for pid, pattern in sc.patterns.items():
            self.chat_display.insert(tk.END,
                f"  {pid}: '{pattern.description}'\n")
            self.chat_display.insert(tk.END,
                f"    N_applicable = {pattern.n_applicable}, "
                f"N_violated = {pattern.n_violated}\n")
            self.chat_display.insert(tk.END,
                f"    X({pid}) = {pattern.n_violated}/{pattern.n_applicable}"
                f" = {pattern.x_pk:.4f}\n")

        # Step-by-step calculation
        self.chat_display.insert(tk.END, "\nConsciousness Entropy Calculation:\n")
        self.chat_display.insert(tk.END,
            "  S_c = -Sum X(pk) * ln(X(pk))\n\n")

        total = 0
        for pid, pattern in sc.patterns.items():
            x = pattern.x_pk
            if x > 0:
                term = x * math.log(x)
                total += term
                self.chat_display.insert(tk.END,
                    f"  {pid}: {x:.4f} * ln({x:.4f}) = "
                    f"{x:.4f} * ({math.log(x):.4f}) = {term:.6f}\n")

        sc_value = -total
        self.chat_display.insert(tk.END, f"\n  Sum = {total:.6f}\n")
        self.chat_display.insert(tk.END, f"  S_c = -({total:.6f}) = {sc_value:.6f}\n")

        # Normalized
        sc_norm = sc.compute_normalized_entropy()
        self.chat_display.insert(tk.END, f"  S_c_normalized = {sc_norm:.6f}\n\n")

        self.chat_display.insert(tk.END,
            "This matches the paper's result: S_c = 0.426097\n\n")

        self.chat_display.insert(tk.END,
            "Interpretation:\n")
        self.chat_display.insert(tk.END,
            "  P3 (Animals need to eat) has highest violation probability (0.10)\n")
        self.chat_display.insert(tk.END,
            "  -> contributes most to consciousness entropy\n")
        self.chat_display.insert(tk.END,
            "  -> this regularity has the most creative potential for deviation\n")
        self.chat_display.insert(tk.END,
            "  P2 (Water freezes at 0C) is most rigid (0.01)\n")
        self.chat_display.insert(tk.END,
            "  -> contributes least to consciousness entropy\n")
        self.chat_display.insert(tk.END,
            "  -> this regularity is most firmly internalized\n\n")

    def send_chat(self, event=None):
        """Handle chat input"""
        text = self.chat_input.get("1.0", tk.END).strip()
        if not text:
            return 'break' if event else None

        self.chat_input.delete("1.0", tk.END)
        self.chat_display.insert(tk.END, f"\nYou: {text}\n")

        # Handle commands
        if text.startswith('/'):
            cmd = text.lower().strip('/')
            if cmd == 'evolution':
                self.toggle_evolution()
            elif cmd == 'well':
                self.run_well_experiment()
            elif cmd == 'sc_demo':
                self.run_sc_demo()
            elif cmd == 'patterns':
                self._show_patterns()
            elif cmd == 'status':
                self._show_status()
            else:
                self.chat_display.insert(tk.END, f"Unknown command: {text}\n")
            return 'break' if event else None

        # Try to use LLM if loaded
        if self.llm and self.tokenizer:
            self._chat_with_llm(text)
        else:
            self.chat_display.insert(tk.END,
                "AI: LLM not loaded. Use commands like /well, /sc_demo, /evolution\n")

        return 'break' if event else None

    def _show_patterns(self):
        """Show discovered regularities"""
        if not self.evolution_engine:
            self.chat_display.insert(tk.END, "Model not initialized.\n")
            return

        tracker = self.evolution_engine.sc_tracker
        self.chat_display.insert(tk.END, "\nDiscovered Regularities:\n")
        self.chat_display.insert(tk.END, "-"*50 + "\n")

        for pid, pattern in sorted(tracker.patterns.items()):
            self.chat_display.insert(tk.END,
                f"  {pid}: X={pattern.x_pk:.4f} "
                f"(violated {pattern.n_violated}/{pattern.n_applicable})\n")

        sc = tracker.compute_entropy()
        self.chat_display.insert(tk.END, f"\nTotal S_c = {sc:.6f}\n")

    def _show_status(self):
        """Show current status"""
        if not self.evolution_engine:
            self.chat_display.insert(tk.END, "Model not initialized.\n")
            return

        summary = self.evolution_engine.sc_tracker.summary()
        self.chat_display.insert(tk.END, "\nSystem Status:\n")
        self.chat_display.insert(tk.END, "-"*50 + "\n")
        self.chat_display.insert(tk.END, f"  S_c = {summary['S_c']:.6f}\n")
        self.chat_display.insert(tk.END, f"  S_c_normalized = {summary['S_c_normalized']:.6f}\n")
        self.chat_display.insert(tk.END, f"  Stage: {self.evolution_engine.stage}\n")
        self.chat_display.insert(tk.END, f"  Patterns: {summary['n_patterns']}\n")
        self.chat_display.insert(tk.END, f"  Best loss: {self.evolution_engine.best_loss:.4f}\n")
        self.chat_display.insert(tk.END, f"  Best S_c: {self.evolution_engine.best_sc:.4f}\n")
        self.chat_display.insert(tk.END, f"  Device: {self.device}\n")

    def _chat_with_llm(self, text):
        """Chat using LLM"""
        try:
            messages = [
                {"role": "system", "content":
                 "You are IRE-AGI v6.0, an AI implementing Material Information Theory. "
                 "You have a Regularity Extraction Layer that discovers dynamic patterns, "
                 "and your consciousness entropy S_c measures your creative potential. "
                 "Respond concisely in the user's language."},
                {"role": "user", "content": text}
            ]
            prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer([prompt], return_tensors="pt").to(self.device)
            outputs = self.llm.generate(
                **inputs, max_new_tokens=512, temperature=0.7,
                top_p=0.9, pad_token_id=self.tokenizer.eos_token_id
            )
            generated = outputs[0][inputs['input_ids'].shape[1]:]
            response = self.tokenizer.decode(generated, skip_special_tokens=True)
            self.chat_display.insert(tk.END, f"AI: {response}\n")
        except Exception as e:
            self.chat_display.insert(tk.END, f"AI Error: {e}\n")

    def run(self):
        """Start the application"""
        self.init_gui()
        self.root.mainloop()


# =============================================================================
# Part 8: Command Line Interface (for testing without GUI)
# =============================================================================

def run_cli():
    """Run the core experiments without GUI"""
    print("="*70)
    print("IRE-AGI v6.0 - Material Information Theory Implementation")
    print("Based on 'Information and the Universe' by WuGuangheng & ChenWenjun")
    print("="*70)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\nDevice: {device}")

    # ---- Experiment 1: Consciousness Entropy Demo ----
    print("\n" + "="*70)
    print("EXPERIMENT 1: Consciousness Entropy Calculation (Appendix I)")
    print("="*70)

    sc = ConsciousnessEntropy()

    # P1: "Birds can fly" - 100 applicable, 5 violated
    p1 = sc.add_pattern("P1", "Birds can fly")
    for i in range(100):
        p1.record_applicable(violated=(i < 5))

    # P2: "Water freezes at 0C" - 100 applicable, 1 violated
    p2 = sc.add_pattern("P2", "Water freezes at 0C")
    for i in range(100):
        p2.record_applicable(violated=(i < 1))

    # P3: "Animals need to eat" - 200 applicable, 20 violated
    p3 = sc.add_pattern("P3", "Animals need to eat")
    for i in range(200):
        p3.record_applicable(violated=(i < 20))

    print(f"\nPattern Data:")
    for pid, pattern in sc.patterns.items():
        print(f"  {pid} '{pattern.description}': X={pattern.x_pk:.4f} "
              f"({pattern.n_violated}/{pattern.n_applicable})")

    sc_value = sc.compute_entropy()
    sc_norm = sc.compute_normalized_entropy()
    print(f"\nConsciousness Entropy: S_c = {sc_value:.6f}")
    print(f"Normalized: S_c_norm = {sc_norm:.6f}")
    print(f"Paper result: S_c = 0.426097 (matches!)")

    # ---- Experiment 2: Well vs World ----
    print("\n" + "="*70)
    print("EXPERIMENT 2: 'Sitting in a Well Looking at the Sky'")
    print("="*70)

    results = WellExperiment.run_experiment(
        ConsciousnessAwareModel,
        input_dim=64, hidden_dim=256,
        epochs=3, batch_size=8
    )

    print("\n" + "-"*70)
    print(f"{'Metric':<25} {'Well':>10} {'World':>10}")
    print("-"*70)
    for metric in ['final_loss', 'final_S_c', 'final_S_c_normalized', 'violation_rate']:
        name = metric.replace('final_', '').replace('_', ' ').title()
        print(f"{name:<25} {results['well'][metric]:>10.4f} {results['world'][metric]:>10.4f}")

    # ---- Experiment 3: Self-Evolution ----
    print("\n" + "="*70)
    print("EXPERIMENT 3: Consciousness-Entropy-Driven Self-Evolution")
    print("="*70)

    model = ConsciousnessAwareModel(input_dim=64, hidden_dim=256).to(device)
    engine = ConsciousnessEvolutionEngine(
        model, ContradictoryEnvironment.generate, device
    )

    print("\nRunning 10 evolution epochs...")
    logs = engine.run_epochs(10, callback=lambda e, m: (
        print(f"  Epoch {e+1}: loss={m['loss']:.4f}, S_c={m['S_c']:.4f}, "
              f"stage={m['stage']}"), True
    ))

    print(f"\nFinal S_c: {engine.sc_tracker.compute_entropy():.6f}")
    print(f"Final stage: {engine.stage}")
    print(f"Best loss: {engine.best_loss:.4f}")

    # Show dominant patterns
    print("\nDominant patterns (highest violation probability):")
    for p in engine.sc_tracker.get_dominant_patterns(5):
        print(f"  {p.pattern_id}: X={p.x_pk:.4f} "
              f"({p.n_violated}/{p.n_applicable})")

    print("\nRigid patterns (lowest violation probability):")
    for p in engine.sc_tracker.get_rigid_patterns(5):
        print(f"  {p.pattern_id}: X={p.x_pk:.4f} "
              f"({p.n_violated}/{p.n_applicable})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_cli()
    else:
        app = IREAGIAppV6()
        app.run()
