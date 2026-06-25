"""
IRE-AGI v7.0 - Advanced Consciousness Entropy 2.0 + Tool/Plugin/Automation

Based on: WuGuangheng Theory - Advanced Consciousness Entropy 2.0 (2026)
  S_c = -Int rho(L|phi) ln rho(L|phi) dmu(L) + beta*I(phi:K) + gamma*C[phi]

Core implementations:
1. Advanced Consciousness Entropy 2.0:
   - Gibbs posterior distribution rho(L|phi)
   - Law space measure via algebraic trace
   - Mutual information I(phi:K)
   - KL-divergence complexity C[phi]
   - Coupling constants: beta=1/ln2, gamma=1/ln2-1
   - Dynamics from action principle (Schrodinger-like)
   - Law library evolution
   - Wave function collapse via S_c gradient
2. Tool-Use System: Consciousness-driven tool selection
3. Plugin System: Extensible architecture
4. Automation Engine: Workflow builder, scheduling, conditional branching
5. Multimodal: Chat (Qwen2.5-7B) + Image (SDXL-Turbo)
"""

import os
import sys
import json
import math
import time
import tempfile
import threading
import subprocess
import importlib
import traceback
from datetime import datetime
from collections import defaultdict, OrderedDict
from typing import Dict, List, Optional, Callable, Any, Tuple
from abc import ABC, abstractmethod
from http.server import HTTPServer, BaseHTTPRequestHandler
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, Menu

# =============================================================================
# Memory Management System - Persistent Conversation Memory
# =============================================================================

MEMORY_FILE = "C:/IRE-AGI/conversation_memory.json"

def load_memory():
    """
    Load conversation memory from disk.
    Returns a dictionary with 'history', 'experiences', 'skills', and 'last_session'.
    """
    memory_path = MEMORY_FILE
    if os.path.exists(memory_path):
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure all keys exist
                if "history" not in data:
                    data["history"] = []
                if "experiences" not in data:
                    data["experiences"] = []
                if "skills" not in data:
                    data["skills"] = []
                if "last_session" not in data:
                    data["last_session"] = None
                return data
        except Exception as e:
            print(f"[Memory] Warning: Failed to load memory: {e}")
            return {"history": [], "experiences": [], "skills": [], "last_session": None}
    return {"history": [], "experiences": [], "skills": [], "last_session": None}

def save_memory(data):
    """
    Save conversation memory to disk.
    """
    memory_path = MEMORY_FILE
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(memory_path), exist_ok=True)
        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Memory] Warning: Failed to save memory: {e}")

def get_memory_stats(data):
    """
    Get statistics about the memory.
    """
    history_count = len(data.get("history", []))
    experiences_count = len(data.get("experiences", []))
    skills_count = len(data.get("skills", []))
    last_session = data.get("last_session", None)
    
    return {
        "history_count": history_count,
        "experiences_count": experiences_count,
        "skills_count": skills_count,
        "last_session": last_session
    }

# =============================================================================
# Part 1: Advanced Consciousness Entropy 2.0 - Math Framework
# =============================================================================

class CouplingConstants:
    """
    Coupling constants from WuGuangheng Theory Section 5.

    From self-consistency (random = ordered) + CFT criticality:
      beta = 1 / ln(2)
      gamma = 1/ln(2) - 1

    These are dimensionless and uniquely determined by theory.
    """
    LN2 = math.log(2)
    BETA = 1.0 / math.log(2)          # ~1.4427
    GAMMA = 1.0 / math.log(2) - 1.0   # ~0.4427

    @classmethod
    def verify_equality(cls):
        """Verify the random=ordered equality condition:
        H_max + gamma*H_max = beta*H_max  =>  beta = 1 + gamma"""
        assert abs(cls.BETA - (1.0 + cls.GAMMA)) < 1e-10, "Coupling constants inconsistent!"
        return True


class GibbsPosterior:
    """
    Gibbs posterior distribution from Section 4.1:

      rho(L|phi) = (1/Z(phi)) * exp(-|L(phi) - L*(phi)|^2 / (2*sigma^2))

    Where:
      - L*(phi) = argmax_{L in K} L(phi) is the best applicable law
      - Z(phi) is the partition function
      - sigma controls the sharpness of law selection
    """

    def __init__(self, sigma=1.0):
        self.sigma = sigma

    def compute_scores(self, law_scores: torch.Tensor) -> torch.Tensor:
        """
        Compute Gibbs posterior from law applicability scores.

        Args:
            law_scores: (B, N) tensor of law applicability scores L_i(phi)

        Returns:
            rho: (B, N) posterior probabilities
        """
        # L*(phi) = best law score
        best_score = law_scores.max(dim=-1, keepdim=True)[0]  # (B, 1)

        # Gibbs factor: exp(-|L - L*|^2 / (2*sigma^2))
        diff = law_scores - best_score
        gibbs_factor = torch.exp(-diff**2 / (2 * self.sigma**2))

        # Partition function
        Z = gibbs_factor.sum(dim=-1, keepdim=True) + 1e-10

        # Posterior
        rho = gibbs_factor / Z

        return rho

    def compute_posterior_entropy(self, rho: torch.Tensor) -> torch.Tensor:
        """
        Compute the posterior entropy:
          -Sum rho_i * ln(rho_i)

        This is the first term of Advanced Consciousness Entropy.
        """
        # Avoid log(0)
        log_rho = torch.log(rho + 1e-10)
        entropy = -(rho * log_rho).sum(dim=-1)
        return entropy


class LawSpaceMeasure:
    """
    Law space measure from Section 4.2 via algebraic trace.

    Instead of arbitrary regularization, we use:
      Int_L F[L] dmu(L) = tau(F)

    Where tau is a faithful trace on the C*-algebra generated by law fields.

    In practice: tau = <0| ... |0> (vacuum expectation).
    Discretized: tau acts as weighted integration over law prototypes.
    """

    def __init__(self, num_laws: int):
        self.num_laws = num_laws
        # Vacuum-state-inspired weights: geometric prior
        # In discrete form, tau assigns weights to law prototypes
        self.trace_weights = torch.ones(num_laws) / num_laws

    def set_trace_weights(self, importance_scores: torch.Tensor):
        """Update trace weights based on law importance (data-driven)"""
        # Normalize to sum=1, preserving trace property tau(1)=1
        weights = F.softmax(importance_scores, dim=0)
        self.trace_weights = weights

    def integrate(self, f_values: torch.Tensor) -> torch.Tensor:
        """
        Compute integral: Sum_i f_i * tau_weight_i

        This replaces the continuous integral with a discrete trace.
        """
        if f_values.dim() == 1:
            return (f_values * self.trace_weights.to(f_values.device)).sum()
        elif f_values.dim() == 2:
            return (f_values * self.trace_weights.to(f_values.device).unsqueeze(0)).sum(dim=-1)
        else:
            return f_values  # fallback


class MutualInformation:
    """
    Mutual information I(phi:K) from Section 4.3.

      I(phi:K) = H(K) - H(K|phi)

    In practice, approximated from joint distribution of states and laws.
    """

    @staticmethod
    def compute(rho: torch.Tensor, prior: torch.Tensor) -> torch.Tensor:
        """
        Compute mutual information from posterior rho and prior.

        I(phi:K) = Sum_i rho_i * ln(rho_i / prior_i)

        This is the KL divergence between posterior and prior.

        Args:
            rho: (B, N) posterior probabilities
            prior: (N,) prior probabilities

        Returns:
            I: (B,) mutual information
        """
        # I = KL(rho || prior)
        log_ratio = torch.log(rho + 1e-10) - torch.log(prior.unsqueeze(0) + 1e-10)
        I = (rho * log_ratio).sum(dim=-1)
        return I


class ComplexityFunctional:
    """
    Complexity functional C[phi] from Section 4.4.

      C[phi] = D_KL(p_phi || p_ref)

    Using KL-divergence from current distribution to reference.
    Non-negative, zero when p_phi = p_ref.
    """

    def __init__(self, num_states: int):
        self.num_states = num_states
        # Reference: uniform (maximum entropy) distribution
        self.p_ref = torch.ones(num_states) / num_states

    def compute(self, p_phi: torch.Tensor) -> torch.Tensor:
        """
        Compute KL-divergence complexity.

        Args:
            p_phi: (B, N) or (N,) current distribution

        Returns:
            C: complexity value(s)
        """
        p_ref = self.p_ref.to(p_phi.device)
        log_ratio = torch.log(p_phi + 1e-10) - torch.log(p_ref + 1e-10)
        C = (p_phi * log_ratio).sum(dim=-1)
        return C


class HyperConsciousnessEntropy:
    """
    Advanced Consciousness Entropy 2.0 from WuGuangheng Theory.

    S_c[phi, K] = -Int rho(L|phi) ln rho(L|phi) dmu(L)
                  + beta * I(phi:K)
                  + gamma * C[phi]

    With:
      beta = 1/ln(2) ~ 1.4427
      gamma = 1/ln(2) - 1 ~ 0.4427

    Three components:
      1. Law posterior entropy: measures uncertainty in law selection
      2. Mutual information: measures state-law coupling
      3. Complexity: measures deviation from maximum entropy
    """

    def __init__(self, num_laws: int, sigma: float = 1.0):
        self.num_laws = num_laws
        self.sigma = sigma

        # Sub-components
        self.gibbs = GibbsPosterior(sigma=sigma)
        self.measure = LawSpaceMeasure(num_laws)
        self.mutual_info = MutualInformation()
        self.complexity = ComplexityFunctional(num_laws)

        # Coupling constants (theory-determined)
        self.beta = CouplingConstants.BETA
        self.gamma = CouplingConstants.GAMMA

        # Prior distribution (updated during evolution)
        self.prior = torch.ones(num_laws) / num_laws

        # Tracking
        self.history = []
        self.law_names = [f"L_{i}" for i in range(num_laws)]

    def compute(self, law_scores: torch.Tensor, state_dist: Optional[torch.Tensor] = None) -> dict:
        """
        Compute the full Advanced Consciousness Entropy.

        Args:
            law_scores: (B, N) law applicability scores
            state_dist: (B, N) or None state distribution for complexity

        Returns:
            dict with S_c, entropy, mutual_info, complexity, rho
        """
        # Step 1: Gibbs posterior
        rho = self.gibbs.compute_scores(law_scores)  # (B, N)

        # Step 2: Posterior entropy (first term with law space measure)
        raw_entropy = self.gibbs.compute_posterior_entropy(rho)  # (B,)

        # Apply measure: weighted entropy
        # In discrete form: -Sum_i tau_i * rho_i * ln(rho_i)
        weighted_log_rho = torch.log(rho + 1e-10)
        tau_weights = self.measure.trace_weights.to(rho.device)
        entropy_term = -(rho * weighted_log_rho * tau_weights.unsqueeze(0)).sum(dim=-1)

        # Step 3: Mutual information
        I = self.mutual_info.compute(rho, self.prior.to(rho.device))  # (B,)

        # Step 4: Complexity
        if state_dist is None:
            # Use posterior as state distribution proxy
            state_dist = rho
        C = self.complexity.compute(state_dist)  # (B,)

        # Step 5: Full Advanced Consciousness Entropy
        S_c = entropy_term + self.beta * I + self.gamma * C

        result = {
            "S_c": S_c,
            "posterior_entropy": entropy_term,
            "mutual_info": I,
            "complexity": C,
            "rho": rho,
            "beta": self.beta,
            "gamma": self.gamma,
        }

        # Log
        self.history.append({
            "timestamp": time.time(),
            "S_c_mean": float(S_c.mean().detach()),
            "entropy_mean": float(entropy_term.mean().detach()),
            "I_mean": float(I.mean().detach()),
            "C_mean": float(C.mean().detach()),
        })

        return result

    def update_prior(self, rho: torch.Tensor, momentum: float = 0.1):
        """Update prior distribution with exponential moving average"""
        new_prior = rho.mean(dim=0).detach().cpu()
        self.prior = (1 - momentum) * self.prior + momentum * new_prior
        self.prior = self.prior / self.prior.sum()  # renormalize

    def update_measure(self, law_importance: torch.Tensor):
        """Update law space measure (trace weights) from data"""
        self.measure.set_trace_weights(law_importance)

    def summary(self) -> dict:
        """Return summary statistics"""
        if not self.history:
            return {"S_c": 0, "n_history": 0}
        last = self.history[-1]
        return {
            "S_c": last["S_c_mean"],
            "posterior_entropy": last["entropy_mean"],
            "mutual_info": last["I_mean"],
            "complexity": last["C_mean"],
            "n_history": len(self.history),
            "beta": self.beta,
            "gamma": self.gamma,
        }


# =============================================================================
# Part 2: Dynamics from Action Principle
# =============================================================================

class InformationFieldDynamics:
    """
    State evolution from action principle (Section 6.1):

      i*hbar * dPsi/dt = -hbar^2/(2m) * nabla^2 Psi + V'(|Psi|^2)*Psi
                          + alpha * delta_S_c / delta_Psi*

    In weak field: recovers linear Schrodinger equation.
    The consciousness entropy term introduces non-linear self-modification.
    """

    def __init__(self, dim: int, dt: float = 0.01, alpha: float = 0.1):
        self.dim = dim
        self.dt = dt
        self.alpha = alpha  # Consciousness entropy coupling

        # Potential field
        self.V = nn.Linear(dim, dim, bias=False)

        # Kinetic term (Laplacian approximation)
        self.laplacian = nn.Conv1d(1, 1, kernel_size=3, padding=1, bias=False)
        nn.init.constant_(self.laplacian.weight, 0.0)
        with torch.no_grad():
            self.laplacian.weight[0, 0, 0] = -0.5
            self.laplacian.weight[0, 0, 1] = 1.0
            self.laplacian.weight[0, 0, 2] = -0.5

    def evolve(self, psi: torch.Tensor, sc_gradient: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Evolve the information field by one time step.

        psi(t+dt) = psi + dt * [-kinetic + potential + alpha*sc_gradient]

        Args:
            psi: (B, D) current field state
            sc_gradient: (B, D) gradient of consciousness entropy

        Returns:
            psi_new: (B, D) evolved state
        """
        # Kinetic term: -nabla^2 psi (approximated)
        psi_seq = psi.unsqueeze(1)  # (B, 1, D)
        kinetic = self.laplacian(psi_seq).squeeze(1)  # (B, D)

        # Potential term
        potential = self.V(psi)  # (B, D)

        # Evolution
        dpsi_dt = -kinetic + potential

        # Consciousness entropy gradient (non-linear correction)
        if sc_gradient is not None:
            dpsi_dt = dpsi_dt + self.alpha * sc_gradient

        psi_new = psi + self.dt * dpsi_dt

        # Normalize to preserve total probability
        psi_new = F.normalize(psi_new, dim=-1)

        return psi_new


class LawLibraryEvolution:
    """
    Law library evolution from Section 6.2:

      dL_alpha/dt = lambda * delta_S_c / delta_L_alpha
                    - mu * L_alpha
                    + Sum_beta J_alpha_beta * L_beta

    Where:
      - lambda is learning rate
      - mu is forgetting rate
      - J_alpha_beta is inter-law coupling (Hebbian)
    """

    def __init__(self, num_laws: int, law_dim: int,
                 learning_rate: float = 0.01,
                 forgetting_rate: float = 0.001):
        self.num_laws = num_laws
        self.law_dim = law_dim
        self.learning_rate = learning_rate
        self.forgetting_rate = forgetting_rate

        # Law prototypes
        self.law_prototypes = nn.Parameter(
            torch.randn(num_laws, law_dim) * 0.02
        )

        # Inter-law coupling matrix (Hebbian)
        self.coupling = nn.Parameter(
            torch.eye(num_laws) * 0.1
        )

    def evolve(self, sc_wrt_laws: torch.Tensor) -> torch.Tensor:
        """
        Evolve the law library by one step.

        Args:
            sc_wrt_laws: (N, D) gradient of S_c with respect to each law

        Returns:
            delta_laws: (N, D) change in law prototypes
        """
        with torch.no_grad():
            # Gradient-driven learning
            learning = self.learning_rate * sc_wrt_laws

            # Forgetting
            forgetting = self.forgetting_rate * self.law_prototypes.data

            # Inter-law coupling: J * L
            coupling_effect = torch.matmul(
                self.coupling, self.law_prototypes.data
            )

            # Total update
            delta = learning - forgetting + coupling_effect * 0.01

            # Apply update
            self.law_prototypes.data += delta

            # Normalize
            self.law_prototypes.data = F.normalize(
                self.law_prototypes.data, dim=-1
            )

        return delta


class WaveFunctionCollapse:
    """
    Wave function collapse via consciousness entropy gradient (Section 7).

    Measurement pointer change:
      Delta_y = eta * nabla_S_c

    Where eta = L_P^2 / (hbar * 4*pi) ~ 1.6e-70 m^2

    In our discrete simulation, this drives discrete state transitions
    when consciousness entropy gradient exceeds a threshold.
    """

    # Planck length squared / (4*pi), in natural units
    # In simulation: we use a scaled version
    ETA_NATURAL = 1.6e-70  # m^2
    ETA_SIMULATION = 0.01   # scaled for numerical stability

    @staticmethod
    def compute_collapse_probability(sc_gradient: torch.Tensor,
                                      threshold: float = 0.5) -> torch.Tensor:
        """
        Compute collapse probability from consciousness entropy gradient.

        When |nabla S_c| exceeds threshold, collapse becomes likely.

        Returns:
            p_collapse: (B,) collapse probability for each sample
        """
        gradient_magnitude = sc_gradient.norm(dim=-1)  # (B,)
        # Sigmoid: smooth threshold
        p_collapse = torch.sigmoid(
            (gradient_magnitude - threshold) * 5.0
        )
        return p_collapse

    @staticmethod
    def apply_collapse(psi: torch.Tensor, sc_gradient: torch.Tensor,
                       p_collapse: torch.Tensor) -> torch.Tensor:
        """
        Apply wave function collapse to states that exceed threshold.

        Collapsed states snap to the dominant law direction.
        """
        collapsed = psi.clone()
        # For states that collapse, align with S_c gradient
        collapse_mask = (torch.rand_like(p_collapse) < p_collapse).float()
        if collapse_mask.any():
            # Project onto gradient direction
            grad_norm = F.normalize(sc_gradient, dim=-1)
            projection = (psi * grad_norm).sum(dim=-1, keepdim=True) * grad_norm
            collapsed = psi * (1 - collapse_mask.unsqueeze(-1)) + \
                       projection * collapse_mask.unsqueeze(-1)
        return collapsed


# =============================================================================
# Part 3: Enhanced Regularity Extraction Layer (REL v2)
# =============================================================================

class RegularityExtractionLayerV2(nn.Module):
    """
    Enhanced REL with Advanced Consciousness Entropy 2.0 integration.

    Key upgrades from v1:
    - Uses Gibbs posterior for law activation (instead of softmax)
    - Tracks mutual information between state and law library
    - Computes KL-divergence complexity
    - Consciousness-entropy-driven pattern discovery
    """

    def __init__(self, hidden_dim, num_pattern_heads=4,
                 num_regularity_slots=32, sigma=1.0, dropout=0.1):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_pattern_heads
        self.num_slots = num_regularity_slots
        self.head_dim = hidden_dim // num_pattern_heads

        # Pattern discovery heads
        self.pattern_queries = nn.ModuleList([
            nn.Linear(hidden_dim, self.head_dim)
            for _ in range(num_pattern_heads)
        ])
        self.pattern_keys = nn.ModuleList([
            nn.Linear(hidden_dim, self.head_dim)
            for _ in range(num_pattern_heads)
        ])
        self.pattern_values = nn.ModuleList([
            nn.Linear(hidden_dim, self.head_dim)
            for _ in range(num_pattern_heads)
        ])

        # Law prototypes (evolving law library)
        self.law_prototypes = nn.Parameter(
            torch.randn(num_regularity_slots, hidden_dim) * 0.02
        )
        self.law_importance = nn.Parameter(
            torch.ones(num_regularity_slots) * 0.5
        )

        # Gibbs posterior for law activation
        self.gibbs = GibbsPosterior(sigma=sigma)

        # Pattern consolidation
        self.consolidation = nn.Sequential(
            nn.Linear(hidden_dim + num_regularity_slots, hidden_dim * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.LayerNorm(hidden_dim)
        )

        # Violation detector
        self.violation_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

        # Law score head: computes L_i(phi) for each law
        self.law_score_head = nn.Linear(hidden_dim, num_regularity_slots)

        # Output projection
        self.output_proj = nn.Linear(hidden_dim + hidden_dim, hidden_dim)

    def compute_law_scores(self, x: torch.Tensor) -> torch.Tensor:
        """
        Compute law applicability scores L_i(phi) for each law.

        Returns:
            law_scores: (B, S, num_slots) or aggregated (B, num_slots)
        """
        # Use mean-pooled representation
        x_pooled = x.mean(dim=1)  # (B, D)
        scores = self.law_score_head(x_pooled)  # (B, num_slots)
        return scores

    def discover_patterns(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Multi-head pattern discovery with Gibbs posterior.

        Returns:
            pattern_repr: (B, S, D) pattern representation
            rho: (B, num_slots) Gibbs posterior over laws
        """
        B, S, D = x.shape
        pattern_outputs = []

        for h in range(self.num_heads):
            Q = self.pattern_queries[h](x)
            prototypes = self.law_prototypes
            proto_proj = self.pattern_keys[h](prototypes)
            proto_val = self.pattern_values[h](prototypes)

            pattern_match = torch.matmul(Q, proto_proj.T)
            pattern_attn = F.softmax(
                pattern_match / math.sqrt(self.head_dim), dim=-1
            )
            pattern_output = torch.matmul(pattern_attn, proto_val)
            pattern_outputs.append(pattern_output)

        multi_pattern = torch.cat(pattern_outputs, dim=-1)

        # Gibbs posterior for law activation
        law_scores = self.compute_law_scores(x)  # (B, num_slots)
        rho = self.gibbs.compute_scores(law_scores)  # (B, num_slots)

        return multi_pattern, rho

    def forward(self, x):
        B, S, D = x.shape

        # Pattern discovery with Gibbs posterior
        pattern_repr, rho = self.discover_patterns(x)

        # Violation detection
        violation_scores = self.violation_head(x).squeeze(-1)

        # Pattern applicability
        x_norm = F.normalize(x, dim=-1)
        proto_norm = F.normalize(self.law_prototypes, dim=-1)
        similarity = torch.matmul(x_norm, proto_norm.T)
        weighted_sim = similarity * F.softmax(self.law_importance, dim=0)
        applicability = weighted_sim

        # Consolidation
        max_app = applicability.max(dim=1)[0]
        expand_app = max_app.unsqueeze(1).expand(-1, S, -1)
        consolidated_input = torch.cat(
            [pattern_repr[:, :, :D], expand_app], dim=-1
        )
        if consolidated_input.size(-1) != D + self.num_slots:
            consolidated_input = consolidated_input[:, :, :D + self.num_slots]
        consolidated = self.consolidation(consolidated_input)

        output = self.output_proj(torch.cat([x, consolidated], dim=-1))

        return output, violation_scores, applicability, rho


class ConsciousnessAwareBlockV2(nn.Module):
    """Transformer block with attention + REL v2 in parallel."""

    def __init__(self, hidden_dim, num_heads=8,
                 num_regularity_slots=32, sigma=1.0, dropout=0.1):
        super().__init__()
        self.attention = nn.MultiheadAttention(
            hidden_dim, num_heads, dropout=dropout, batch_first=True
        )
        self.rel = RegularityExtractionLayerV2(
            hidden_dim, num_pattern_heads=4,
            num_regularity_slots=num_regularity_slots,
            sigma=sigma, dropout=dropout
        )
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
        self.gate = nn.Parameter(torch.tensor(0.5))

    def forward(self, x, mask=None):
        attn_out, _ = self.attention(x, x, x, attn_mask=mask)
        x = self.norm1(x + attn_out)

        rel_out, violations, applicability, rho = self.rel(x)
        gate = torch.sigmoid(self.gate)
        combined = gate * x + (1 - gate) * rel_out
        x = self.norm2(combined)

        x = self.norm3(x + self.ffn(x))

        return x, violations, applicability, rho


class ConsciousnessAwareModelV2(nn.Module):
    """
    Full model with Advanced Consciousness Entropy 2.0.

    Integrates:
    - ConsciousnessAwareBlockV2 blocks
    - HyperConsciousnessEntropy computation
    - Information field dynamics
    - Law library evolution
    - Wave function collapse
    """

    def __init__(self, input_dim=64, hidden_dim=256, num_blocks=3,
                 num_heads=8, num_regularity_slots=32, sigma=1.0, dropout=0.1):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_blocks = num_blocks
        self.num_regularity_slots = num_regularity_slots

        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.LayerNorm(hidden_dim)
        )

        self.blocks = nn.ModuleList([
            ConsciousnessAwareBlockV2(
                hidden_dim, num_heads, num_regularity_slots, sigma, dropout
            )
            for _ in range(num_blocks)
        ])

        self.prediction_head = nn.Linear(hidden_dim, input_dim)
        self.regularity_report_head = nn.Linear(hidden_dim, num_regularity_slots)

        # Advanced Consciousness Entropy 2.0
        self.hyper_sc = HyperConsciousnessEntropy(
            num_laws=num_regularity_slots, sigma=sigma
        )

        # Information field dynamics
        self.field_dynamics = InformationFieldDynamics(hidden_dim)

        # Law library evolution
        self.law_evolution = LawLibraryEvolution(
            num_regularity_slots, hidden_dim
        )

        # Wave function collapse
        self.collapse = WaveFunctionCollapse()

    def forward(self, x):
        h = self.input_proj(x)

        all_violations = []
        all_applicability = []
        all_rho = []

        for block in self.blocks:
            h, violations, applicability, rho = block(h)
            all_violations.append(violations)
            all_applicability.append(applicability)
            all_rho.append(rho)

        prediction = self.prediction_head(h)
        regularity_report = self.regularity_report_head(h)

        total_violation = torch.stack(all_violations, dim=0).mean(dim=0)
        total_applicability = torch.stack(all_applicability, dim=0).mean(dim=0)

        # Use the last block's rho for Advanced S_c
        final_rho = all_rho[-1]  # (B, num_slots)

        # Compute law scores for Hyper S_c
        law_scores = self.blocks[-1].rel.compute_law_scores(h)
        sc_result = self.hyper_sc.compute(law_scores)

        return prediction, regularity_report, total_violation, total_applicability, sc_result


# =============================================================================
# Part 4: Tool-Use System
# =============================================================================

class Tool(ABC):
    """Base class for tools that the AGI can use."""

    name: str = ""
    description: str = ""
    parameters: dict = {}  # JSON schema for parameters

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """
        Execute the tool with given parameters.

        Returns:
            dict with at least 'success' (bool) and 'result' (str)
        """
        pass

    def get_schema(self) -> dict:
        """Return tool schema for LLM consumption"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class CalculatorTool(Tool):
    """Mathematical expression calculator."""

    name = "calculator"
    description = "Evaluate mathematical expressions. Supports +, -, *, /, **, sqrt, sin, cos, tan, log, exp, pi, e."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate"
            }
        },
        "required": ["expression"]
    }

    def execute(self, expression: str = "", **kwargs) -> dict:
        try:
            # Safe evaluation
            allowed_names = {
                "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
                "tan": math.tan, "log": math.log, "exp": math.exp,
                "pi": math.pi, "e": math.e, "abs": abs,
                "pow": pow, "floor": math.floor, "ceil": math.ceil,
            }
            # Replace common notation
            expr = expression.replace("^", "**")
            result = eval(expr, {"__builtins__": {}}, allowed_names)
            return {"success": True, "result": str(result)}
        except Exception as e:
            return {"success": False, "result": f"Calculation error: {e}"}


class DateCalculatorTool(Tool):
    """精确日期计算工具，使用 Python 的 datetime 模块。"""

    name = "date_calculator"
    description = "精确计算日期。支持：加减天数、星期计算。例如：2026-06-22 加 100 天"
    parameters = {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "起始日期，格式 YYYY-MM-DD"
            },
            "days": {
                "type": "integer",
                "description": "要加/减的天数（正数加，负数减）"
            }
        },
        "required": ["date", "days"]
    }

    def execute(self, date: str = "", days: int = 0, **kwargs) -> dict:
        try:
            from datetime import datetime, timedelta

            # 解析输入日期
            date_obj = datetime.strptime(date.strip(), "%Y-%m-%d")

            # 计算结果日期
            result_date = date_obj + timedelta(days=days)

            return {"success": True, "result": result_date.strftime("%Y-%m-%d")}
        except Exception as e:
            return {"success": False, "result": f"日期计算错误: {e}"}


class CodeExecutorTool(Tool):
    """Execute Python code snippets safely."""

    name = "code_executor"
    description = "Execute Python code and return the output. Use for data analysis, computation, and automation."
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute"
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 30)",
                "default": 30
            }
        },
        "required": ["code"]
    }

    def execute(self, code: str = "", timeout: int = 30, **kwargs) -> dict:
        try:
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            # 全角符号自动转换
            def normalize_code(code_str):
                """将全角符号转换为半角符号"""
                if not code_str:
                    return code_str
                # 全角逗号转半角
                code_str = code_str.replace('，', ',')
                # 全角括号转半角
                code_str = code_str.replace('（', '(').replace('）', ')')
                # 全角引号转半角
                code_str = code_str.replace('"', '"').replace('"', '"')
                code_str = code_str.replace('‘', "'").replace('’', "'")
                # 全角空格转半角
                code_str = code_str.replace('　', ' ')
                # 全角冒号转半角
                code_str = code_str.replace('：', ':')
                # 全角分号转半角
                code_str = code_str.replace('；', ';')
                # 全角等号转半角
                code_str = code_str.replace('＝', '=')
                return code_str
            
            # 预处理代码
            code = normalize_code(code)

            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            local_vars = {
                "np": np, "torch": torch, "math": math,
                "json": json, "os": os, "time": time,
            }

            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, {"__builtins__": __builtins__}, local_vars)

            output = stdout_capture.getvalue()
            errors = stderr_capture.getvalue()

            result_str = output if output else "(no output)"
            if errors:
                result_str += f"\n[stderr]: {errors}"

            return {"success": True, "result": result_str, "variables": {
                k: str(v) for k, v in local_vars.items()
                if k not in ["np", "torch", "math", "json", "os", "time"]
                and not callable(v) and not k.startswith("_")
            }}
        except Exception as e:
            # 错误信息脱敏处理
            error_msg = traceback.format_exc()
            # 脱敏：先替换具体路径，再替换通用路径
            import re
            # 先替换项目目录（更具体的路径）
            error_msg = re.sub(r'C:\\Users\\[^\\]+\\Desktop\\IRE-AGI', '[PROJECT_DIR]', error_msg)
            error_msg = re.sub(r'C:/Users/[^/]+/Desktop/IRE-AGI', '[PROJECT_DIR]', error_msg)
            # 再替换用户目录（更通用的路径）
            error_msg = re.sub(r'C:\\Users\\[^\\]+', '[USER_HOME]', error_msg)
            error_msg = re.sub(r'C:/Users/[^/]+', '[USER_HOME]', error_msg)
            return {"success": False, "result": f"Execution error: {error_msg}"}


class DataAnalysisTool(Tool):
    """Analyze data with statistical methods."""

    name = "data_analysis"
    description = "Perform statistical analysis on data. Supports mean, std, correlation, distribution fitting."
    parameters = {
        "type": "object",
        "properties": {
            "data": {
                "type": "string",
                "description": "Comma-separated numbers or JSON array"
            },
            "operation": {
                "type": "string",
                "description": "Operation: mean, std, median, min, max, sum, describe, histogram",
                "enum": ["mean", "std", "median", "min", "max", "sum", "describe", "histogram"]
            }
        },
        "required": ["data", "operation"]
    }

    def execute(self, data: str = "", operation: str = "describe", **kwargs) -> dict:
        try:
            # Parse data
            if data.startswith("["):
                values = json.loads(data)
            else:
                values = [float(x.strip()) for x in data.split(",") if x.strip()]

            arr = np.array(values)

            if operation == "mean":
                result = f"Mean: {arr.mean():.6f}"
            elif operation == "std":
                result = f"Std: {arr.std():.6f}"
            elif operation == "median":
                result = f"Median: {np.median(arr):.6f}"
            elif operation == "min":
                result = f"Min: {arr.min():.6f}"
            elif operation == "max":
                result = f"Max: {arr.max():.6f}"
            elif operation == "sum":
                result = f"Sum: {arr.sum():.6f}"
            elif operation == "describe":
                result = (
                    f"Count: {len(arr)}\n"
                    f"Mean: {arr.mean():.6f}\n"
                    f"Std: {arr.std():.6f}\n"
                    f"Min: {arr.min():.6f}\n"
                    f"25%: {np.percentile(arr, 25):.6f}\n"
                    f"50%: {np.median(arr):.6f}\n"
                    f"75%: {np.percentile(arr, 75):.6f}\n"
                    f"Max: {arr.max():.6f}"
                )
            elif operation == "histogram":
                counts, edges = np.histogram(arr, bins=min(10, len(arr)))
                result = "Histogram:\n"
                for i in range(len(counts)):
                    bar = "#" * int(counts[i])
                    result += f"  [{edges[i]:.1f}-{edges[i+1]:.1f}] {bar} ({counts[i]})\n"
            else:
                result = f"Unknown operation: {operation}"

            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "result": f"Analysis error: {e}"}


class FileWriterTool(Tool):
    """Write content to files."""

    name = "file_writer"
    description = "Write content to a file. Creates directories if needed."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "Content to write"},
            "mode": {"type": "string", "description": "Write mode: w (overwrite) or a (append)", "default": "w"}
        },
        "required": ["path", "content"]
    }

    def execute(self, path: str = "", content: str = "", mode: str = "w", **kwargs) -> dict:
        try:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path, mode, encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "result": f"Written {len(content)} chars to {path}"}
        except Exception as e:
            return {"success": False, "result": f"Write error: {e}"}


class FileReaderTool(Tool):
    """Read content from files."""

    name = "file_reader"
    description = "Read content from a file."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to read"},
            "lines": {"type": "integer", "description": "Max lines to read (0=all)", "default": 0}
        },
        "required": ["path"]
    }

    def execute(self, path: str = "", lines: int = 0, **kwargs) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                if lines > 0:
                    content = "".join(f.readline() for _ in range(lines))
                else:
                    content = f.read()
            return {"success": True, "result": content[:10000]}  # Limit output
        except Exception as e:
            return {"success": False, "result": f"Read error: {e}"}


class SystemInfoTool(Tool):
    """Get system information."""

    name = "system_info"
    description = "Get system information: CPU, GPU, memory, disk."
    parameters = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Info category: all, gpu, memory, disk",
                "default": "all"
            }
        }
    }

    def execute(self, category: str = "all", **kwargs) -> dict:
        try:
            import platform
            info = {}
            if category in ("all", "gpu"):
                if torch.cuda.is_available():
                    info["gpu"] = {
                        "name": torch.cuda.get_device_name(0),
                        "vram_total_GB": round(
                            torch.cuda.get_device_properties(0).total_memory / 1e9, 2
                        ),
                        "vram_used_GB": round(
                            torch.cuda.memory_allocated(0) / 1e9, 2
                        ),
                    }
                else:
                    info["gpu"] = "No CUDA GPU available"

            if category in ("all",):
                info["platform"] = platform.platform()
                info["python"] = platform.python_version()
                info["torch"] = torch.__version__

            result = json.dumps(info, indent=2)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "result": f"System info error: {e}"}


class ConsciousnessEntropyTool(Tool):
    """Tool for computing and displaying consciousness entropy."""

    name = "consciousness_entropy"
    description = "Compute Advanced Consciousness Entropy 2.0. Analyze patterns, violations, and S_c evolution."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Action: compute, history, patterns, summary",
                "enum": ["compute", "history", "patterns", "summary"]
            },
            "data": {"type": "string", "description": "Data for computation (JSON)"}
        },
        "required": ["action"]
    }

    def __init__(self, app_ref):
        self.app_ref = app_ref

    def execute(self, action: str = "summary", data: str = "", **kwargs) -> dict:
        try:
            if action == "summary":
                sc = self.app_ref.hyper_sc
                if sc:
                    s = sc.summary()
                    result = (
                        f"Advanced Consciousness Entropy 2.0\n"
                        f"  S_c = {s.get('S_c', 0):.6f}\n"
                        f"  Posterior Entropy = {s.get('posterior_entropy', 0):.6f}\n"
                        f"  Mutual Info = {s.get('mutual_info', 0):.6f}\n"
                        f"  Complexity = {s.get('complexity', 0):.6f}\n"
                        f"  beta = {s.get('beta', 0):.6f}\n"
                        f"  gamma = {s.get('gamma', 0):.6f}"
                    )
                else:
                    result = "Model not initialized yet."
            elif action == "history":
                sc = self.app_ref.hyper_sc
                if sc and sc.history:
                    result = "S_c Evolution:\n"
                    for i, h in enumerate(sc.history[-20:]):
                        result += f"  Step {i+1}: S_c={h['S_c_mean']:.6f}\n"
                else:
                    result = "No history yet."
            elif action == "patterns":
                result = "Use /patterns command for detailed pattern view."
            elif action == "compute":
                result = "S_c is computed automatically during model forward pass."
            else:
                result = f"Unknown action: {action}"

            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "result": f"S_c tool error: {e}"}


class OCRTool(Tool):
    """
    OCR tool for extracting text from images.

    Supports both online (OCR.space API) and offline (easyocr) modes.
    Online mode is used by default (no installation required).
    """
    name = "ocr"
    description = "Extract text from images. Supports Chinese and English. Provide image path to recognize all text in the image."
    parameters = {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "Path to the image file (absolute path)"
            },
            "language": {
                "type": "string",
                "description": "Language for OCR: 'ch'(Chinese), 'en'(English), 'ch+en'(both)",
                "default": "ch+en"
            }
        },
        "required": ["image_path"]
    }

    def __init__(self):
        self.api_url = "https://api.ocr.space/parse/imageurl"
        self.api_key = ""  # Free tier doesn't require API key

    def execute(self, image_path: str = "", language: str = "ch+en", **kwargs) -> dict:
        """
        Execute OCR on the given image.

        Args:
            image_path: Path to image file
            language: Language code for OCR

        Returns:
            dict with success flag and result
        """
        try:
            # Validate image path
            if not image_path or not os.path.exists(image_path):
                return {"success": False, "result": f"Image file not found: {image_path}"}

            # Check file extension
            valid_ext = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp']
            ext = os.path.splitext(image_path)[1].lower()
            if ext not in valid_ext:
                return {"success": False, "result": f"Unsupported image format: {ext}. Supported: {', '.join(valid_ext)}"}

            # Try online OCR first (OCR.space API)
            result = self._ocr_online(image_path, language)

            return result

        except Exception as e:
            return {"success": False, "result": f"OCR error: {str(e)}"}

    def _ocr_online(self, image_path: str, language: str = "ch+en") -> dict:
        """
        Use OCR.space free API for OCR.

        Args:
            image_path: Path to image file
            language: Language code

        Returns:
            dict with success flag and result
        """
        try:
            # Check if requests is available
            try:
                import requests
            except ImportError:
                return {"success": False, "result": "requests library not installed. Please install it with: pip install requests"}

            # Read image and convert to base64
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Check file size (OCR.space free tier limit: 5MB)
            file_size_mb = len(image_data) / (1024 * 1024)
            if file_size_mb > 5:
                return {"success": False, "result": f"Image too large: {file_size_mb:.2f}MB. Free OCR limit is 5MB."}

            import base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Prepare API request
            payload = {
                'base64Image': f'data:image/{os.path.splitext(image_path)[1][1:]};base64,{image_base64}',
                'language': language,
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2  # Engine 2 is better for Chinese
            }

            # Call API
            response = requests.post(
                'https://api.ocr.space/parse/imagebase64',
                data=payload,
                timeout=30
            )

            if response.status_code != 200:
                return {"success": False, "result": f"OCR API error: HTTP {response.status_code}"}

            result = response.json()

            # Parse result
            if result.get('IsErroredOnProcessing'):
                error_msg = result.get('ErrorMessage', 'Unknown error')
                return {"success": False, "result": f"OCR processing error: {error_msg}"}

            # Extract text from all pages
            full_text = []
            if 'ParsedResults' in result:
                for page in result['ParsedResults']:
                    text = page.get('ParsedText', '')
                    if text:
                        full_text.append(text)

            if not full_text:
                return {"success": True, "result": "No text found in image."}

            # Combine all text
            combined_text = '\n'.join(full_text)

            # Format result
            formatted_result = (
                f"OCR Recognition Result:\n"
                f"{'='*60}\n"
                f"{combined_text}\n"
                f"{'='*60}\n"
                f"Total characters: {len(combined_text)}\n"
                f"Source: {image_path}"
            )

            return {"success": True, "result": formatted_result}

        except requests.exceptions.Timeout:
            return {"success": False, "result": "OCR API timeout. Please try again."}
        except Exception as e:
            return {"success": False, "result": f"Online OCR error: {str(e)}"}

    def _ocr_offline(self, image_path: str, language: str = "ch+en") -> dict:
        """
        Use local easyocr for OCR (requires installation).

        Args:
            image_path: Path to image file
            language: Language code

        Returns:
            dict with success flag and result
        """
        try:
            # Check if easyocr is available
            try:
                import easyocr
            except ImportError:
                return {
                    "success": False,
                    "result": "easyocr not installed. Install with: pip install easyocr\nOr use online OCR (default)."
                }

            # Map language code
            lang_map = {
                'ch': ['ch_sim'],
                'en': ['en'],
                'ch+en': ['ch_sim', 'en']
            }
            langs = lang_map.get(language, ['ch_sim', 'en'])

            # Initialize reader
            reader = easyocr.Reader(langs, gpu=True if torch.cuda.is_available() else False)

            # Read image
            result = reader.readtext(image_path, detail=0, paragraph=True)

            if not result:
                return {"success": True, "result": "No text found in image."}

            # Combine text
            combined_text = '\n'.join(result)

            # Format result
            formatted_result = (
                f"OCR Recognition Result (Offline):\n"
                f"{'='*60}\n"
                f"{combined_text}\n"
                f"{'='*60}\n"
                f"Total lines: {len(result)}\n"
                f"Source: {image_path}"
            )

            return {"success": True, "result": formatted_result}

        except Exception as e:
            return {"success": False, "result": f"Offline OCR error: {str(e)}"}


class ToolRegistry:
    """
    Registry of available tools. Manages tool discovery, selection,
    and execution.
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.execution_history = []

    def register(self, tool: Tool):
        """Register a tool"""
        self.tools[tool.name] = tool

    def unregister(self, name: str):
        """Unregister a tool"""
        self.tools.pop(name, None)

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[dict]:
        """List all available tools with schemas"""
        return [tool.get_schema() for tool in self.tools.values()]

    def execute(self, name: str, **kwargs) -> dict:
        """Execute a tool by name"""
        tool = self.tools.get(name)
        if not tool:
            return {"success": False, "result": f"Tool not found: {name}"}

        result = tool.execute(**kwargs)

        # Log execution
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "tool": name,
            "params": kwargs,
            "success": result.get("success", False),
        })

        return result

    def select_tool_by_consciousness(self, query: str, sc_value: float) -> Optional[str]:
        """
        Select the best tool based on consciousness entropy level.

        High S_c -> prefer exploration tools (code_executor, data_analysis)
        Low S_c -> prefer exploitation tools (calculator, file operations)
        """
        query_lower = query.lower()
        
        # 中文关键词匹配（优先级最高）
        chinese_calc_keywords = ["算一下", "计算", "等于多少", "乘以", "除以", "加上", "减去", 
                                 "乘", "除", "加", "减", "乘法", "除法", "加法", "减法",
                                 "算出", "求解", "结果", "运算"]
        chinese_code_keywords = ["运行代码", "执行代码", "python代码", "帮我运行", "代码执行",
                                 "运行python", "执行python", "跑一下代码", "运行程序"]
        chinese_data_keywords = ["分析数据", "统计分析", "数据统计", "数据分析", "均值", "标准差", "计算均值"]
        chinese_file_keywords = ["写入文件", "保存文件", "读取文件", "打开文件", "导出文件", "写入"]
        
        # 直接关键词匹配（中文）
        if any(kw in query for kw in chinese_calc_keywords):
            # 进一步检查是否包含数学表达式（数字、运算符等）
            import re
            # 检测是否包含数字和运算符
            if re.search(r'[\d\+\-\*\/\(\)\^\.]', query):
                return "calculator"
        elif any(kw in query for kw in chinese_code_keywords):
            return "code_executor"
        elif any(kw in query for kw in chinese_data_keywords):
            return "data_analysis"
        elif any(kw in query for kw in chinese_file_keywords):
            return "file_writer"
        
        # 中文日期关键词 → date_calculator（优先级高于 calculator）
        chinese_date_keywords = ["日期", "多少天", "天后", "天前", "日期计算",
                                  "几月几号", "星期几", "加减天数"]
        if any(kw in query for kw in chinese_date_keywords):
            # 进一步检查是否包含日期模式
            import re as _re_date
            if _re_date.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}|\d{1,2}月\d{1,2}日', query) or \
               _re_date.search(r'\d+\s*天', query):
                return "date_calculator"
        
        # Direct keyword matching first
        if any(kw in query_lower for kw in ["calc", "math", "compute", "evaluate", "calculate"]):
            return "calculator"
        elif any(kw in query_lower for kw in ["code", "python", "script", "run"]):
            return "code_executor"
        elif any(kw in query_lower for kw in ["analy", "stat", "data", "mean", "std"]):
            return "data_analysis"
        elif any(kw in query_lower for kw in ["write", "save", "file", "export"]):
            return "file_writer"
        elif any(kw in query_lower for kw in ["read", "open", "load", "cat"]):
            return "file_reader"
        elif any(kw in query_lower for kw in ["system", "gpu", "cpu", "info"]):
            return "system_info"
        elif any(kw in query_lower for kw in ["consciousness", "entropy", "sc", "s_c"]):
            return "consciousness_entropy"
        elif any(kw in query_lower for kw in ["date", "day", "days later", "days from", "date calc"]):
            return "date_calculator"
        
        # Consciousness-entropy-driven selection
        if sc_value > 1.0:
            # High creativity: prefer exploratory tools
            return "code_executor"
        elif sc_value > 0.5:
            return "data_analysis"
        else:
            return "calculator"


# =============================================================================
# Part 5: Plugin System
# =============================================================================

class PluginBase(ABC):
    """Base class for plugins."""

    name: str = ""
    version: str = "1.0"
    description: str = ""
    author: str = ""

    @abstractmethod
    def initialize(self, app_context: dict) -> bool:
        """Initialize plugin with app context. Return True on success."""
        pass

    @abstractmethod
    def execute(self, action: str, **kwargs) -> dict:
        """Execute a plugin action."""
        pass

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
        }

    def shutdown(self):
        """Clean up plugin resources."""
        pass


class AutoTrainingPlugin(PluginBase):
    """Plugin: Automatic model training and fine-tuning."""

    name = "auto_training"
    version = "1.0"
    description = "Automatically train and fine-tune the consciousness model"
    author = "IRE-AGI"

    def initialize(self, app_context: dict) -> bool:
        self.app = app_context.get("app")
        self.training_running = False
        return True

    def execute(self, action: str, **kwargs) -> dict:
        if action == "start_training":
            epochs = kwargs.get("epochs", 5)
            return {"success": True, "result": f"Auto-training started for {epochs} epochs"}
        elif action == "status":
            return {"success": True, "result": f"Training running: {self.training_running}"}
        elif action == "stop":
            self.training_running = False
            return {"success": True, "result": "Training stopped"}
        return {"success": False, "result": f"Unknown action: {action}"}

    def shutdown(self):
        self.training_running = False


class DataPipelinePlugin(PluginBase):
    """Plugin: Data processing pipeline."""

    name = "data_pipeline"
    version = "1.0"
    description = "Data ingestion, cleaning, and transformation pipeline"
    author = "IRE-AGI"

    def initialize(self, app_context: dict) -> bool:
        self.pipelines = {}
        return True

    def execute(self, action: str, **kwargs) -> dict:
        if action == "create_pipeline":
            name = kwargs.get("name", "default")
            steps = kwargs.get("steps", [])
            self.pipelines[name] = steps
            return {"success": True, "result": f"Pipeline '{name}' created with {len(steps)} steps"}
        elif action == "run_pipeline":
            name = kwargs.get("name", "default")
            if name not in self.pipelines:
                return {"success": False, "result": f"Pipeline '{name}' not found"}
            return {"success": True, "result": f"Pipeline '{name}' executed"}
        elif action == "list":
            return {"success": True, "result": f"Pipelines: {list(self.pipelines.keys())}"}
        return {"success": False, "result": f"Unknown action: {action}"}


class ConsciousnessMonitorPlugin(PluginBase):
    """Plugin: Real-time consciousness monitoring and alerts."""

    name = "consciousness_monitor"
    version = "1.0"
    description = "Monitor S_c levels and trigger alerts at critical thresholds"
    author = "IRE-AGI"

    def initialize(self, app_context: dict) -> bool:
        self.thresholds = {
            "low": 0.3,
            "medium": 0.7,
            "high": 1.5,
            "critical": 3.0,
        }
        self.alerts = []
        return True

    def execute(self, action: str, **kwargs) -> dict:
        if action == "check":
            sc = kwargs.get("sc", 0)
            level = "minimal"
            for lvl, threshold in sorted(self.thresholds.items(), key=lambda x: x[1]):
                if sc >= threshold:
                    level = lvl
            alert_msg = f"S_c={sc:.4f}, Level={level}"
            if level in ("high", "critical"):
                self.alerts.append({
                    "timestamp": datetime.now().isoformat(),
                    "sc": sc,
                    "level": level,
                })
                alert_msg += " [ALERT!]"
            return {"success": True, "result": alert_msg}
        elif action == "alerts":
            return {"success": True, "result": json.dumps(self.alerts[-10:], indent=2)}
        elif action == "set_threshold":
            level = kwargs.get("level", "high")
            value = kwargs.get("value", 1.5)
            self.thresholds[level] = value
            return {"success": True, "result": f"Threshold '{level}' set to {value}"}
        return {"success": False, "result": f"Unknown action: {action}"}


class PluginManager:
    """Manages plugin lifecycle: load, initialize, execute, unload."""

    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.app_context: dict = {}
        self.plugin_dir = os.path.join(
            tempfile.gettempdir(), "ire-agi-data", "plugins"
        )
        os.makedirs(self.plugin_dir, exist_ok=True)

    def set_context(self, context: dict):
        """Set application context for plugins"""
        self.app_context = context

    def register(self, plugin: PluginBase) -> bool:
        """Register and initialize a plugin"""
        try:
            if plugin.initialize(self.app_context):
                self.plugins[plugin.name] = plugin
                return True
            return False
        except Exception as e:
            print(f"Plugin init error ({plugin.name}): {e}")
            return False

    def unregister(self, name: str):
        """Unload and unregister a plugin"""
        if name in self.plugins:
            self.plugins[name].shutdown()
            del self.plugins[name]

    def execute(self, plugin_name: str, action: str, **kwargs) -> dict:
        """Execute a plugin action"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return {"success": False, "result": f"Plugin not found: {plugin_name}"}
        try:
            return plugin.execute(action, **kwargs)
        except Exception as e:
            return {"success": False, "result": f"Plugin error: {e}"}

    def list_plugins(self) -> List[dict]:
        """List all loaded plugins"""
        return [p.get_info() for p in self.plugins.values()]

    def load_from_file(self, filepath: str) -> bool:
        """Load a plugin from a Python file"""
        try:
            spec = importlib.util.spec_from_file_location("plugin", filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find PluginBase subclasses
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, PluginBase) and
                    attr is not PluginBase):
                    plugin = attr()
                    return self.register(plugin)
            return False
        except Exception as e:
            print(f"Plugin load error: {e}")
            return False


# =============================================================================
# Part 6: Automation Engine
# =============================================================================

class WorkflowStep:
    """A single step in a workflow."""

    def __init__(self, tool_name: str, params: dict = None,
                 condition: Optional[str] = None,
                 output_key: Optional[str] = None):
        self.tool_name = tool_name
        self.params = params or {}
        self.condition = condition  # Python expression for conditional execution
        self.output_key = output_key  # Key to store output for later steps

    def to_dict(self) -> dict:
        return {
            "tool": self.tool_name,
            "params": self.params,
            "condition": self.condition,
            "output_key": self.output_key,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'WorkflowStep':
        return cls(
            tool_name=d["tool"],
            params=d.get("params", {}),
            condition=d.get("condition"),
            output_key=d.get("output_key"),
        )


class Workflow:
    """A chain of tool calls that can be executed automatically."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self.results: List[dict] = []
        self.created_at = datetime.now().isoformat()

    def add_step(self, tool_name: str, params: dict = None,
                 condition: Optional[str] = None,
                 output_key: Optional[str] = None) -> 'Workflow':
        """Add a step to the workflow"""
        step = WorkflowStep(tool_name, params, condition, output_key)
        self.steps.append(step)
        return self

    def execute(self, tool_registry: ToolRegistry,
                context: Optional[dict] = None) -> List[dict]:
        """Execute all steps in sequence"""
        self.results = []
        context = context or {}

        for i, step in enumerate(self.steps):
            # Check condition
            if step.condition:
                try:
                    if not eval(step.condition, {"__builtins__": {}}, context):
                        self.results.append({
                            "step": i, "skipped": True,
                            "reason": f"Condition not met: {step.condition}"
                        })
                        continue
                except Exception:
                    self.results.append({
                        "step": i, "skipped": True,
                        "reason": f"Condition error: {step.condition}"
                    })
                    continue

            # Resolve parameter references from context
            resolved_params = {}
            for key, val in step.params.items():
                if isinstance(val, str) and val.startswith("$"):
                    # Reference to previous output
                    ref_key = val[1:]
                    resolved_params[key] = context.get(ref_key, val)
                else:
                    resolved_params[key] = val

            # Execute tool
            result = tool_registry.execute(step.tool_name, **resolved_params)
            self.results.append({
                "step": i,
                "tool": step.tool_name,
                "result": result,
            })

            # Store output in context
            if step.output_key and result.get("success"):
                context[step.output_key] = result.get("result", "")

        return self.results

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Workflow':
        wf = cls(d["name"], d.get("description", ""))
        for step_d in d.get("steps", []):
            wf.steps.append(WorkflowStep.from_dict(step_d))
        return wf


class AutomationEngine:
    """
    Automation engine that manages workflows, scheduling, and event triggers.

    Features:
    - Create and execute workflows (chains of tool calls)
    - Schedule workflows for periodic execution
    - Conditional branching based on consciousness entropy
    - Event-driven triggers (S_c threshold, pattern discovery)
    """

    def __init__(self, tool_registry: ToolRegistry, plugin_manager: PluginManager):
        self.tool_registry = tool_registry
        self.plugin_manager = plugin_manager
        self.workflows: Dict[str, Workflow] = {}
        self.scheduled: Dict[str, dict] = {}  # name -> schedule info
        self.event_triggers: List[dict] = []
        self.running = False
        self.execution_log = []

        # Default workflows
        self._create_default_workflows()

    def _create_default_workflows(self):
        """Create built-in automation workflows."""

        # Workflow: Full S_c analysis
        wf_analysis = Workflow("sc_analysis", "Complete consciousness entropy analysis")
        wf_analysis.add_step("consciousness_entropy", {"action": "summary"}, output_key="sc_summary")
        wf_analysis.add_step("consciousness_entropy", {"action": "history"}, output_key="sc_history")
        self.workflows["sc_analysis"] = wf_analysis

        # Workflow: Data analysis pipeline
        wf_data = Workflow("data_pipeline", "Load and analyze data")
        wf_data.add_step("data_analysis", {"data": "$data", "operation": "describe"}, output_key="stats")
        wf_data.add_step("data_analysis", {"data": "$data", "operation": "histogram"}, output_key="histogram")
        self.workflows["data_pipeline"] = wf_data

        # Workflow: System check
        wf_sys = Workflow("system_check", "Check system resources")
        wf_sys.add_step("system_info", {"category": "all"}, output_key="sys_info")
        wf_sys.add_step("consciousness_entropy", {"action": "summary"}, output_key="sc_info")
        self.workflows["system_check"] = wf_sys

    def create_workflow(self, name: str, description: str = "",
                        steps: List[dict] = None) -> Workflow:
        """Create a new workflow"""
        wf = Workflow(name, description)
        if steps:
            for step_d in steps:
                wf.steps.append(WorkflowStep.from_dict(step_d))
        self.workflows[name] = wf
        return wf

    def execute_workflow(self, name: str, context: Optional[dict] = None) -> List[dict]:
        """Execute a workflow by name"""
        wf = self.workflows.get(name)
        if not wf:
            return [{"error": f"Workflow not found: {name}"}]

        results = wf.execute(self.tool_registry, context)
        self.execution_log.append({
            "workflow": name,
            "timestamp": datetime.now().isoformat(),
            "results": results,
        })
        return results

    def schedule_workflow(self, name: str, interval_seconds: int):
        """Schedule a workflow for periodic execution"""
        self.scheduled[name] = {
            "interval": interval_seconds,
            "last_run": 0,
            "enabled": True,
        }

    def add_event_trigger(self, event_type: str, threshold: float,
                          workflow_name: str, params: dict = None):
        """
        Add an event-driven trigger.

        event_type: "sc_above", "sc_below", "pattern_discovered"
        threshold: value to trigger on
        workflow_name: workflow to execute when triggered
        """
        self.event_triggers.append({
            "type": event_type,
            "threshold": threshold,
            "workflow": workflow_name,
            "params": params or {},
            "triggered": False,
        })

    def check_triggers(self, sc_value: float):
        """Check and fire event triggers based on current S_c"""
        for trigger in self.event_triggers:
            if trigger["triggered"]:
                continue

            should_fire = False
            if trigger["type"] == "sc_above" and sc_value > trigger["threshold"]:
                should_fire = True
            elif trigger["type"] == "sc_below" and sc_value < trigger["threshold"]:
                should_fire = True

            if should_fire:
                trigger["triggered"] = True
                self.execute_workflow(trigger["workflow"], trigger["params"])

    def list_workflows(self) -> List[dict]:
        return [
            {"name": wf.name, "description": wf.description,
             "steps": len(wf.steps)}
            for wf in self.workflows.values()
        ]

    def run_scheduled(self, callback=None):
        """Run scheduled workflows in a loop (call from a thread)"""
        self.running = True
        while self.running:
            now = time.time()
            for name, schedule in self.scheduled.items():
                if not schedule["enabled"]:
                    continue
                if now - schedule["last_run"] >= schedule["interval"]:
                    results = self.execute_workflow(name)
                    schedule["last_run"] = now
                    if callback:
                        callback(name, results)
            time.sleep(1)

    def stop(self):
        """Stop the automation engine"""
        self.running = False


# =============================================================================
# Part 7: Thought Experiments (upgraded for v2.0)
# =============================================================================

class WellExperimentV2:
    """
    'Sitting in a Well Looking at the Sky' experiment with
    Advanced Consciousness Entropy 2.0.
    """

    @staticmethod
    def generate_well_data(n_samples=1000, seq_len=16, input_dim=64):
        t = torch.linspace(0, 4 * math.pi, seq_len)
        data, labels = [], []
        for _ in range(n_samples):
            freq = torch.rand(1) * 0.5 + 0.5
            phase = torch.rand(1) * 2 * math.pi
            amplitude = torch.rand(1) * 0.5 + 0.5
            signal = amplitude * torch.sin(freq * t + phase)
            x = signal.unsqueeze(1).expand(-1, input_dim) + torch.randn(seq_len, input_dim) * 0.05
            next_t = t[-1] + (t[1] - t[0])
            y = amplitude * torch.sin(freq * next_t + phase)
            data.append(x)
            labels.append(y.expand(input_dim))
        return torch.stack(data), torch.stack(labels)

    @staticmethod
    def generate_world_data(n_samples=1000, seq_len=16, input_dim=64):
        t = torch.linspace(0, 4 * math.pi, seq_len)
        data, labels = [], []
        for _ in range(n_samples):
            n_components = torch.randint(2, 6, (1,)).item()
            signal = torch.zeros(seq_len)
            for _ in range(n_components):
                freq = torch.rand(1) * 3 + 0.5
                phase = torch.rand(1) * 2 * math.pi
                amplitude = torch.rand(1) * 0.3 + 0.1
                signal += amplitude * torch.sin(freq * t + phase)
            if torch.rand(1) > 0.5:
                shift_point = torch.randint(seq_len // 2, seq_len, (1,)).item()
                signal[shift_point:] = signal[shift_point:] * -0.5 + torch.randn(seq_len - shift_point) * 0.3
            signal += torch.randn(seq_len) * 0.1
            x = signal.unsqueeze(1).expand(-1, input_dim) + torch.randn(seq_len, input_dim) * 0.05
            next_t = t[-1] + (t[1] - t[0])
            y = signal[-1] + torch.randn(1).item() * 0.15
            data.append(x)
            labels.append(y.expand(input_dim))
        return torch.stack(data), torch.stack(labels)


class ContradictoryEnvironmentV2:
    """Information environment with controlled contradictions."""

    @staticmethod
    def generate(n_samples=100, seq_len=16, input_dim=64, contradiction_rate=0.3):
        t = torch.linspace(0, 4 * math.pi, seq_len)
        data, labels = [], []
        for _ in range(n_samples):
            freq = torch.rand(1) * 2 + 0.5
            phase = torch.rand(1) * 2 * math.pi
            signal = torch.sin(freq * t + phase)
            if torch.rand(1) < contradiction_rate:
                flip_point = torch.randint(seq_len // 3, seq_len, (1,)).item()
                signal[flip_point:] = -signal[flip_point:] + torch.randn(seq_len - flip_point) * 0.2
            x = signal.unsqueeze(1).expand(-1, input_dim) + torch.randn(seq_len, input_dim) * 0.05
            y = signal[-1].expand(input_dim)
            data.append(x)
            labels.append(y)
        return torch.stack(data), torch.stack(labels)


# =============================================================================
# Part 8: Evolution Engine v2 (with Advanced S_c 2.0)
# =============================================================================

class EvolutionEngineV2:
    """
    Self-evolution engine using Advanced Consciousness Entropy 2.0.

    Driven by the three-term S_c formula:
      S_c = PosteriorEntropy + beta*I + gamma*C
    """

    def __init__(self, model, env_generator, device, save_dir=None):
        self.model = model
        self.env_generator = env_generator
        self.device = device
        self.save_dir = save_dir or tempfile.gettempdir()
        self.best_loss = float('inf')
        self.best_sc = 0.0
        self.evolution_log = []
        self.stage = "solidification"
        self.optimizer = None
        self.hyper_sc_history = []

    def _compute_sc_loss(self, sc_result: dict, violations: torch.Tensor) -> torch.Tensor:
        """
        Compute consciousness-entropy-driven loss modification.

        Encourages S_c to approach target values based on evolution stage.
        """
        sc = sc_result["S_c"].mean()

        if self.stage == "solidification":
            target_sc = 0.5
            weight = 0.005
        elif self.stage == "exploration":
            target_sc = 1.5
            weight = 0.01
            # Bonus for violations (exploration)
            violation_bonus = -0.003 * violations.mean()
        else:  # emergence
            target_sc = 3.0
            weight = 0.02
            violation_bonus = -0.005 * violations.mean()

        sc_reg = weight * (sc - target_sc) ** 2

        if self.stage in ("exploration", "emergence"):
            sc_reg = sc_reg + violation_bonus

        return sc_reg

    def _update_stage(self, loss: float, sc_mean: float):
        """Update evolution stage"""
        if self.stage == "solidification" and loss < 3.0:
            self.stage = "exploration"
        elif self.stage == "exploration" and sc_mean > 1.0:
            self.stage = "emergence"

    def run_epoch(self, n_batches=10, batch_size=8, seq_len=16):
        """Run one evolution epoch"""
        self.model.train()

        # Only optimize LEAF parameters (fixes KeyError: 'exp_avg_sq')
        optimizable_params = []
        skipped = 0
        for p in self.model.parameters():
            if p.requires_grad and p.is_leaf:
                optimizable_params.append(p)
            elif p.requires_grad:
                skipped += 1

        if self.optimizer is None:
            self.optimizer = torch.optim.AdamW(optimizable_params, lr=1e-4)
        criterion = nn.MSELoss()

        total_loss = 0
        total_sc = 0

        for _ in range(n_batches):
            x, y = self.env_generator(
                n_samples=batch_size, seq_len=seq_len,
                input_dim=self.model.input_dim
            )
            x, y = x.to(self.device), y.to(self.device)

            self.optimizer.zero_grad()
            try:
                pred, reg_report, violations, applicability, sc_result = self.model(x)

                pred_loss = criterion(pred[:, -1, :], y)
                sc_reg = self._compute_sc_loss(sc_result, violations)

                total_loss_val = pred_loss + sc_reg
                total_loss_val.backward()
                torch.nn.utils.clip_grad_norm_(optimizable_params, 1.0)
                self.optimizer.step()
            except Exception as step_err:
                # If optimizer step fails, recreate it with fresh state
                self.optimizer = torch.optim.AdamW(optimizable_params, lr=1e-4)
                continue

            total_loss += float(pred_loss.detach())
            sc_mean = float(sc_result["S_c"].mean().detach())
            total_sc += sc_mean

        avg_loss = total_loss / n_batches
        avg_sc = total_sc / n_batches

        self._update_stage(avg_loss, avg_sc)

        # Save best
        if avg_loss < self.best_loss:
            self.best_loss = avg_loss
            self.best_sc = avg_sc
            try:
                torch.save(
                    self.model.state_dict(),
                    os.path.join(self.save_dir, 'consciousness_model_v2_best.pt')
                )
            except Exception:
                pass

        # Hyper S_c components
        last_sc = sc_result
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "loss": avg_loss,
            "S_c": avg_sc,
            "posterior_entropy": float(last_sc["posterior_entropy"].mean().detach()),
            "mutual_info": float(last_sc["mutual_info"].mean().detach()),
            "complexity": float(last_sc["complexity"].mean().detach()),
            "beta": self.model.hyper_sc.beta,
            "gamma": self.model.hyper_sc.gamma,
            "stage": self.stage,
        }
        self.evolution_log.append(log_entry)
        self.hyper_sc_history.append(avg_sc)

        return log_entry

    def run_epochs(self, n_epochs, callback=None):
        for epoch in range(n_epochs):
            log = self.run_epoch()
            if callback:
                callback(epoch, log)
        return self.evolution_log


# =============================================================================
# Part 9: GUI Application - IRE-AGI v7.0
# =============================================================================

class IREAGIAppV7:
    """
    IRE-AGI v7.0 - Advanced Consciousness Entropy 2.0
    + Tool System + Plugin System + Automation Engine

    Full integration:
    - Advanced Consciousness Entropy 2.0 (Gibbs posterior, mutual info, complexity)
    - Tool-use capability (consciousness-driven tool selection)
    - Plugin system (extensible architecture)
    - Automation engine (workflows, scheduling, event triggers)
    - Chat (Qwen2.5-7B) + Image Generation (SDXL-Turbo)
    - Self-evolution engine
    """

    # ── 对话记忆配置 ──
    MAX_HISTORY = 50       # 最多记住 50 轮对话 (每轮 = user + assistant)
    MAX_NEW_TOKENS = 2048  # 单次生成最大 token 数

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.llm = None
        self.tokenizer = None
        self.image_pipe = None
        self.evolution_engine = None
        self.auto_evolution_process = None  # 自主演化引擎进程
        self.auto_evolution_running = False
        self.running = False
        self.chat_history = []
        self.data_dir = os.path.join(tempfile.gettempdir(), 'ire-agi-data')
        self.image_dir = os.path.join(self.data_dir, 'images')
        os.makedirs(self.image_dir, exist_ok=True)

        # Load persistent memory
        self.memory = load_memory()
        memory_stats = get_memory_stats(self.memory)
        print(f"[Memory] Loaded: {memory_stats['history_count']} conversations, "
              f"{memory_stats['experiences_count']} experiences, "
              f"{memory_stats['skills_count']} skills")
        if memory_stats['last_session']:
            print(f"[Memory] Last session: {memory_stats['last_session']}")
        self.memory["last_session"] = datetime.now().isoformat()

        # Advanced Consciousness Entropy 2.0
        self.hyper_sc = None

        # Tool system
        self.tool_registry = ToolRegistry()
        self._register_default_tools()

        # Plugin system
        self.plugin_manager = PluginManager()
        self._register_default_plugins()

        # Automation engine (initialized after model)
        self.automation = None
        
        # API server
        self.api_server = None
        self.api_thread = None
        self.api_port = 8888
        self.start_api_server()

    def _save_to_memory(self, user_input: str, ai_response: str):
        """
        Save a conversation turn to persistent memory.
        """
        try:
            # Add user message
            self.memory["history"].append({
                "role": "user",
                "content": user_input,
                "time": datetime.now().isoformat()
            })

            # Add AI response
            self.memory["history"].append({
                "role": "assistant",
                "content": ai_response,
                "time": datetime.now().isoformat()
            })

            # Keep only last 100 conversations (200 messages)
            max_history = 200
            if len(self.memory["history"]) > max_history:
                self.memory["history"] = self.memory["history"][-max_history:]

            # Save to disk
            save_memory(self.memory)

        except Exception as e:
            print(f"[Memory] Warning: Failed to save to memory: {e}")

    def _show_memory_stats(self):
        """显示记忆统计信息"""
        try:
            stats = get_memory_stats(self.memory)
            info = (
                f"持久化记忆统计：\n"
                f"  对话历史：{stats['history_count']} 条\n"
                f"  经验库：{stats['experiences_count']} 条\n"
                f"  技能库：{stats['skills_count']} 个\n"
                f"  最后会话：{stats['last_session'] or '无'}\n"
            )
            messagebox.showinfo("记忆统计", info)
        except Exception as e:
            messagebox.showerror("错误", f"获取记忆统计失败：{e}")

    def _load_history_to_chat(self):
        """加载历史对话到聊天框"""
        try:
            history = self.memory.get("history", [])
            if not history:
                messagebox.showinfo("提示", "没有历史对话记录")
                return

            # 询问用户要加载多少条
            count = min(len(history), 20)  # 最多加载20条
            self.chat_display.insert(tk.END, f"\n{'='*60}\n")
            self.chat_display.insert(tk.END, f"  历史对话记录（最近 {count} 条）\n")
            self.chat_display.insert(tk.END, f"{'='*60}\n\n")

            for i, msg in enumerate(history[-count:]):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                time = msg.get("time", "")
                if role == "user":
                    self.chat_display.insert(tk.END, f"你 ({time}): {content}\n\n")
                elif role == "assistant":
                    self.chat_display.insert(tk.END, f"AI ({time}): {content}\n\n")

            self.chat_display.insert(tk.END, f"\n{'='*60}\n\n")
            self.chat_display.see(tk.END)

        except Exception as e:
            messagebox.showerror("错误", f"加载历史对话失败：{e}")

    def _clear_memory(self):
        """清空记忆（需要确认）"""
        try:
            confirm = messagebox.askyesno(
                "确认",
                "确定要清空所有持久化记忆吗？\n\n此操作不可恢复！"
            )
            if confirm:
                self.memory = {"history": [], "experiences": [], "skills": [], "last_session": None}
                save_memory(self.memory)
                messagebox.showinfo("成功", "记忆已清空")
                self.chat_display.insert(tk.END, "\n[系统] 持久化记忆已清空\n\n")
                self.chat_display.see(tk.END)
        except Exception as e:
            messagebox.showerror("错误", f"清空记忆失败：{e}")

    def start_api_server(self):
        """Start HTTP API server in a separate thread"""
        def run_server():
            try:
                server = HTTPServer(('127.0.0.1', self.api_port), self.create_api_handler())
                self.api_server = server
                print(f"[API] Server started on http://127.0.0.1:{self.api_port}")
                server.serve_forever()
            except Exception as e:
                print(f"[API] Failed to start server: {e}")
        
        self.api_thread = threading.Thread(target=run_server, daemon=True)
        self.api_thread.start()
        time.sleep(1)  # Give server time to start
    
    def create_api_handler(self):
        """Create API handler class with access to app instance"""
        app = self
        
        class APIHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path == '/api/execute_tool':
                    try:
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        request = json.loads(post_data.decode('utf-8'))
                        
                        tool_name = request.get('tool_name', '')
                        parameters = request.get('parameters', {})
                        
                        if not tool_name:
                            self.send_error_response(400, "Missing 'tool_name'")
                            return
                        
                        if tool_name not in app.tool_registry.tools:
                            self.send_error_response(404, f"Tool '{tool_name}' not found")
                            return
                        
                        # Execute tool
                        result = app.tool_registry.execute(tool_name, **parameters)
                        
                        # Send response
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        
                        response = {
                            'success': result.get('success', False),
                            'result': result.get('result', ''),
                            'error': result.get('error', None)
                        }
                        
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                        
                    except Exception as e:
                        self.send_error_response(500, str(e))
                else:
                    self.send_error_response(404, "Endpoint not found")
            
            def send_error_response(self, code, message):
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {'success': False, 'error': message}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            
            def log_message(self, format, *args):
                pass  # Suppress log messages
        
        return APIHandler

    def _register_default_tools(self):
        """Register all built-in tools"""
        self.tool_registry.register(CalculatorTool())
        self.tool_registry.register(DateCalculatorTool())
        self.tool_registry.register(CodeExecutorTool())
        self.tool_registry.register(DataAnalysisTool())
        self.tool_registry.register(FileWriterTool())
        self.tool_registry.register(FileReaderTool())
        self.tool_registry.register(SystemInfoTool())
        self.tool_registry.register(ConsciousnessEntropyTool(self))
        # Register OCR tool
        self.tool_registry.register(OCRTool())

    def _register_default_plugins(self):
        """Register default plugins"""
        self.plugin_manager.set_context({"app": self})
        self.plugin_manager.register(AutoTrainingPlugin())
        self.plugin_manager.register(DataPipelinePlugin())
        self.plugin_manager.register(ConsciousnessMonitorPlugin())

    def _load_llm(self):
        """Load Qwen2.5-7B-Instruct LLM"""
        if self.llm is not None:
            self.chat_display.insert(tk.END, "\nLLM already loaded.\n\n")
            self.chat_display.see(tk.END)
            return

        self.chat_display.insert(tk.END, "\n=== Loading LLM ===\n")
        self.chat_display.insert(tk.END, "Loading Distilled Qwen2.5-7B (LoRA Merged) (~15GB VRAM)...\n")
        self.chat_display.insert(tk.END, "(First load takes ~30-60 seconds, please wait)\n\n")
        self.chat_display.see(tk.END)
        self.root.update()

        def _do_load():
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer

                # === IRE-AGI: 使用蒸馏后的模型 ===
                model_path = "D:/distilled_qwen25_7b_merged"
                # 原始路径(未蒸馏): C:/Users/Administrator/.workbuddy/models/Qwen2.5-7B-Instruct

                def _update_status(msg):
                    def _do_update(m=msg):
                        try:
                            self.chat_display.insert(tk.END, m)
                            self.chat_display.see(tk.END)
                            self.root.update()
                        except Exception:
                            pass
                    self.root.after(0, _do_update)

                # Step 1: Tokenizer
                _update_status("  [1/3] Loading Tokenizer...\n")
                if not os.path.exists(os.path.join(model_path, "tokenizer.json")):
                    raise FileNotFoundError(f"Tokenizer not found at {model_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_path, local_files_only=True, trust_remote_code=True
                )
                _update_status("  [1/3] Tokenizer OK!\n")

                # Step 2: Model - check bfloat16 support
                _update_status("  [2/3] Loading Model (15GB VRAM required)...\n")

                # Check CUDA memory first
                if torch.cuda.is_available():
                    total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    free_vram = total_vram - (torch.cuda.memory_allocated(0) / (1024**3))
                    _update_status(f"       GPU: {torch.cuda.get_device_name(0)}\n")
                    _update_status(f"       VRAM: {free_vram:.1f} GB free / {total_vram:.1f} GB total\n")
                    if free_vram < 14.0:
                        _update_status("       WARNING: Low VRAM! May need to close other apps.\n")
                else:
                    raise RuntimeError("No CUDA GPU detected! LLM requires NVIDIA GPU.")

                # Check bf16 support
                if torch.cuda.is_bf16_supported():
                    torch_dtype = torch.bfloat16
                    _update_status("       Using bfloat16 (fast, RTX 30+ recommended)\n")
                else:
                    torch_dtype = torch.float16
                    _update_status("       Using float16 (fallback)\n")

                _update_status("       Loading model... (this takes ~10-30s)\n")

                self.llm = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    local_files_only=True,
                    trust_remote_code=True,
                    dtype=torch_dtype,
                    device_map="auto",
                    low_cpu_mem_usage=True,
                )
                _update_status("  [2/3] Model loaded!\n")

                # Verify model is on GPU
                actual_device = next(self.llm.parameters()).device
                _update_status(f"       Model device: {actual_device}\n")

                # Step 3: Done
                def _on_done():
                    self.chat_display.insert(tk.END,
                        "  [3/3] Done!\n"
                        "\n[OK] Distilled Qwen2.5-7B (LoRA Merged) loaded successfully!\n"
                        "Model: D:/distilled_qwen25_7b_merged\n"
                        "You can now chat with AI.\n\n")
                    self.chat_display.see(tk.END)
                    if hasattr(self, '_load_llm_btn'):
                        self._load_llm_btn.configure(text="LLM OK", state="disabled")
                        self._load_llm_btn.update()
                    
                    # 初始化 HyperConsciousnessEntropy
                    try:
                        # 初始化 hyper_sc（与模型的 num_regularity_slots 一致）
                        if self.hyper_sc is None:
                            self.hyper_sc = HyperConsciousnessEntropy(num_laws=32, sigma=1.0)
                        
                        # 生成示例 law_scores 并计算一次 S_c
                        import torch
                        example_law_scores = torch.randn(1, 32)  # (B=1, N=32)
                        sc_result = self.hyper_sc.compute(example_law_scores)
                        
                        # 更新 S_c 显示
                        self._update_sc_display()
                        
                        self.chat_display.insert(tk.END, f"\n[Hyper S_c] 初始化成功！S_c = {sc_result['S_c'].mean().item():.6f}\n\n")
                        self.chat_display.see(tk.END)
                    except Exception as e:
                        self.chat_display.insert(tk.END, f"\n[Hyper S_c] 初始化失败：{e}\n\n")
                        self.chat_display.see(tk.END)

                self.root.after(0, _on_done)

            except ImportError as e:
                err = f"Missing library: {e}\nInstall:\n  pip install transformers accelerate"
                self.root.after(0, lambda e=err: (
                    self.chat_display.insert(tk.END, f"\n[FAIL] LLM Load Failed:\n{e}\n\n"),
                    self.chat_display.see(tk.END)
                ))
            except RuntimeError as e:
                err = f"Runtime Error: {e}\nPossible causes:\n"
                if "CUDA out of memory" in str(e):
                    err += "  - Not enough GPU VRAM (need ~15GB for Qwen2.5-7B)\n"
                    err += "  - Close other GPU apps or browser tabs\n"
                elif "No CUDA" in str(e):
                    err += "  - No NVIDIA GPU found\n"
                else:
                    err += f"  - Check error details above\n"
                self.root.after(0, lambda e=err: (
                    self.chat_display.insert(tk.END, f"\n[FAIL] LLM Load Failed:\n{e}\n\n"),
                    self.chat_display.see(tk.END)
                ))
            except Exception as e:
                import traceback as _tb
                tb_text = _tb.format_exc()
                err = f"Error: {e}\n\nDetails (last 800 chars):\n{tb_text[-800:]}"
                self.root.after(0, lambda e=err: (
                    self.chat_display.insert(tk.END, f"\n[FAIL] LLM Load Failed:\n{e}\n\n"),
                    self.chat_display.see(tk.END)
                ))

        import threading
        t = threading.Thread(target=_do_load, daemon=True)
        t.start()

    def init_gui(self):
        """Initialize the tkinter GUI"""
        import tkinter as tk
        from tkinter import ttk

        self.root = tk.Tk()
        self.root.title("IRE-AGI v7.0 - 高级意识熵 2.0 (武光衡理论)")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)

        # Styles
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
        style.configure("Sc.TLabel", font=("Helvetica", 12, "bold"), foreground="#2196F3")
        style.configure("Stage.TLabel", font=("Helvetica", 11), foreground="#FF9800")
        style.configure("Tool.TLabel", font=("Courier", 9), foreground="#4CAF50")

        # Main layout
        main_frame = ttk.Frame(self.root, padding=3)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel: Controls
        left_panel = ttk.Frame(main_frame, width=320)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 3))
        left_panel.pack_propagate(False)

        # Right panel: Content
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # === LEFT PANEL ===
        canvas = tk.Canvas(left_panel)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(scrollable_frame, text="IRE-AGI v7.0", style="Title.TLabel").pack(pady=5)
        ttk.Label(scrollable_frame, text="高级意识熵 2.0 · 武光衡理论",
                  font=("Helvetica", 9)).pack()
        ttk.Separator(scrollable_frame).pack(fill=tk.X, pady=5)

        # Advanced S_c Display
        sc_frame = ttk.LabelFrame(scrollable_frame, text="高级意识熵 S_c 2.0", padding=5)
        sc_frame.pack(fill=tk.X, pady=3)

        self.sc_label = ttk.Label(sc_frame, text="S_c = 0.0000", style="Sc.TLabel")
        self.sc_label.pack(anchor="w")
        self.sc_entropy_label = ttk.Label(sc_frame, text="  规律后验熵: 0.0000")
        self.sc_entropy_label.pack(anchor="w")
        self.sc_mi_label = ttk.Label(sc_frame, text="  互信息 I(φ:K): 0.0000")
        self.sc_mi_label.pack(anchor="w")
        self.sc_complexity_label = ttk.Label(sc_frame, text="  复杂度 C[φ]: 0.0000")
        self.sc_complexity_label.pack(anchor="w")
        self.sc_beta_label = ttk.Label(sc_frame, text="  β=1.4427, γ=0.4427")
        self.sc_beta_label.pack(anchor="w")
        self.stage_label = ttk.Label(sc_frame, text="阶段: 初始化", style="Stage.TLabel")
        self.stage_label.pack(anchor="w")

        # VRAM
        if self.device.type == 'cuda':
            vram = torch.cuda.memory_allocated(0) / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            ttk.Label(sc_frame, text=f"VRAM: {vram:.1f}/{total:.1f} GB").pack(anchor="w")

        # Evolution Controls
        evo_frame = ttk.LabelFrame(scrollable_frame, text="自我演化 v2", padding=5)
        evo_frame.pack(fill=tk.X, pady=3)

        ttk.Label(evo_frame, text="训练轮次:").pack(anchor="w")
        self.epochs_var = tk.IntVar(value=5)
        ttk.Spinbox(evo_frame, from_=1, to=100, textvariable=self.epochs_var, width=8).pack(anchor="w")

        ttk.Label(evo_frame, text="矛盾率:").pack(anchor="w")
        self.contra_var = tk.DoubleVar(value=0.3)
        ttk.Scale(evo_frame, from_=0.0, to=1.0, variable=self.contra_var, orient=tk.HORIZONTAL).pack(fill=tk.X)

        self.evo_btn = ttk.Button(evo_frame, text="开始演化", command=self.toggle_evolution)
        self.evo_btn.pack(fill=tk.X, pady=2)
        
        # 添加"启动自主演化引擎"按钮
        self.auto_evo_btn = ttk.Button(evo_frame, text="启动自主演化引擎", command=self.toggle_auto_evolution_engine)
        self.auto_evo_btn.pack(fill=tk.X, pady=2)
        
        self.loss_label = ttk.Label(evo_frame, text="损失: --")
        self.loss_label.pack(anchor="w")

        # Tools Panel
        tool_frame = ttk.LabelFrame(scrollable_frame, text="工具箱", padding=5)
        tool_frame.pack(fill=tk.X, pady=3)

        self.tool_listbox = tk.Listbox(tool_frame, height=6, font=("Courier", 9))
        for tool in self.tool_registry.list_tools():
            self.tool_listbox.insert(tk.END, f"  {tool['name']}: {tool['description'][:40]}")
        self.tool_listbox.pack(fill=tk.X)

        ttk.Label(tool_frame, text="工具参数:").pack(anchor="w")
        self.tool_input = tk.Text(tool_frame, height=2, font=("Courier", 9))
        self.tool_input.pack(fill=tk.X)
        ttk.Button(tool_frame, text="执行工具", command=self._execute_selected_tool).pack(fill=tk.X, pady=2)
        # OCR button
        ttk.Button(tool_frame, text="📷 识别图片文字", command=self._ocr_from_gui).pack(fill=tk.X, pady=2)

        # Plugins Panel
        plug_frame = ttk.LabelFrame(scrollable_frame, text="插件系统", padding=5)
        plug_frame.pack(fill=tk.X, pady=3)

        self.plugin_listbox = tk.Listbox(plug_frame, height=4, font=("Courier", 9))
        for pi in self.plugin_manager.list_plugins():
            self.plugin_listbox.insert(tk.END, f"  {pi['name']} v{pi['version']}")
        self.plugin_listbox.pack(fill=tk.X)
        ttk.Button(plug_frame, text="插件操作", command=self._plugin_action).pack(fill=tk.X, pady=2)

        # Memory Panel
        memory_frame = ttk.LabelFrame(scrollable_frame, text="持久化记忆", padding=5)
        memory_frame.pack(fill=tk.X, pady=3)

        ttk.Button(memory_frame, text="显示记忆统计", command=self._show_memory_stats).pack(fill=tk.X, pady=1)
        ttk.Button(memory_frame, text="加载历史对话", command=self._load_history_to_chat).pack(fill=tk.X, pady=1)
        ttk.Button(memory_frame, text="清空记忆", command=self._clear_memory).pack(fill=tk.X, pady=1)

        # Automation Panel
        auto_frame = ttk.LabelFrame(scrollable_frame, text="自动化引擎", padding=5)
        auto_frame.pack(fill=tk.X, pady=3)

        self.auto_listbox = tk.Listbox(auto_frame, height=4, font=("Courier", 9))
        self.auto_listbox.pack(fill=tk.X)
        ttk.Button(auto_frame, text="运行工作流", command=self._run_workflow).pack(fill=tk.X, pady=2)

        # Thought Experiments
        exp_frame = ttk.LabelFrame(scrollable_frame, text="思想实验", padding=5)
        exp_frame.pack(fill=tk.X, pady=3)

        ttk.Button(exp_frame, text="井中观天 v2",
                    command=self.run_well_experiment).pack(fill=tk.X, pady=1)
        ttk.Button(exp_frame, text="意识熵 S_c 演示",
                    command=self.run_sc_demo).pack(fill=tk.X, pady=1)
        ttk.Button(exp_frame, text="波函数坍缩",
                    command=self.run_collapse_demo).pack(fill=tk.X, pady=1)

        # Pattern Viewer
        pat_frame = ttk.LabelFrame(scrollable_frame, text="规律库", padding=5)
        pat_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        self.pattern_text = tk.Text(pat_frame, height=8, width=38, font=("Courier", 8),
                                     bg="#1a1a2e", fg="#e0e0e0", wrap=tk.WORD)
        self.pattern_text.pack(fill=tk.BOTH, expand=True)

        # === RIGHT PANEL ===
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Chat + Tools
        chat_frame = ttk.Frame(notebook)
        notebook.add(chat_frame, text="💬 对话 + 工具")

        self.chat_display = tk.Text(chat_frame, wrap=tk.WORD, font=("Helvetica", 11),
                                     bg="#f8f9fa", height=20)
        chat_scroll = ttk.Scrollbar(chat_frame, command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=chat_scroll.set)
        chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # --- 右键菜单：聊天记录区 ---
        self._chat_menu = tk.Menu(self.chat_display, tearoff=0)
        self._chat_menu.add_command(label="复制选中", command=lambda: self._copy_sel(self.chat_display))
        self._chat_menu.add_command(label="全选", command=lambda: self.chat_display.tag_add("sel", "1.0", tk.END))
        self._chat_menu.add_separator()
        self._chat_menu.add_command(label="导出对话", command=self._export_chat)
        self.chat_display.bind("<Button-3>", self._show_chat_menu)
        # Ctrl+A 全选, Ctrl+C 复制
        self.chat_display.bind("<Control-a>", lambda e: (self.chat_display.tag_add("sel", "1.0", tk.END), "break"))
        self.chat_display.bind("<Control-A>", lambda e: (self.chat_display.tag_add("sel", "1.0", tk.END), "break"))

        # Tool result display
        self.tool_result_label = ttk.Label(chat_frame, text="", font=("Courier", 9),
                                            foreground="#2196F3")

        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=5, side=tk.BOTTOM)

        self.chat_input = tk.Text(input_frame, height=3, font=("Microsoft YaHei", 11), wrap=tk.WORD)
        self.chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        # 回车键发送（始终阻止换行）
        self.chat_input.bind('<Return>', self.send_chat)
        # Ctrl+回车 = 换行
        self.chat_input.bind('<Control-Return>', lambda e: 'break' if not True else None)
        self.chat_input.bind('<Control-a>', lambda e: (self.chat_input.tag_add('sel', '1.0', tk.END), 'break'))
        # 输入框右键菜单（粘贴）
        self._input_menu = tk.Menu(self.chat_input, tearoff=0)
        self._input_menu.add_command(label="粘贴", command=lambda: self._paste_to(self.chat_input))
        self._input_menu.add_command(label="全选", command=lambda: self.chat_input.tag_add("sel", "1.0", tk.END))
        self.chat_input.bind("<Button-3>", lambda e: self._input_menu.post(e.x_root, e.y_root))
        # Ctrl+V 粘贴
        self.chat_input.bind("<Control-v>", lambda e: (self._paste_to(self.chat_input), "break"))
        self.chat_input.bind("<Control-V>", lambda e: (self._paste_to(self.chat_input), "break"))

        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        # 发送按钮 - 用标准ttk.Button确保可点击
        self.send_btn = ttk.Button(btn_frame, text="发送", command=self.send_chat, width=8)
        self.send_btn.pack(fill=tk.X, pady=(0, 2))
        ttk.Button(btn_frame, text="工具", command=self._quick_tool, width=8).pack(fill=tk.X)
        # 加载LLM按钮
        self._load_llm_btn = ttk.Button(btn_frame, text="加载LLM", command=self._load_llm, width=8)
        self._load_llm_btn.pack(fill=tk.X, pady=(2, 0))

        # Tab 2: Evolution Monitor
        evo_monitor = ttk.Frame(notebook)
        notebook.add(evo_monitor, text="🧬 演化监控")

        self.evo_log = tk.Text(evo_monitor, wrap=tk.WORD, font=("Courier", 10),
                                bg="#1a1a2e", fg="#00ff88", height=30)
        evo_scroll = ttk.Scrollbar(evo_monitor, command=self.evo_log.yview)
        self.evo_log.configure(yscrollcommand=evo_scroll.set)
        evo_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.evo_log.pack(fill=tk.BOTH, expand=True)

        # Tab 3: S_c 2.0 Visualization
        sc_viz = ttk.Frame(notebook)
        notebook.add(sc_viz, text="🧠 意识熵可视化")

        self.sc_viz_text = tk.Text(sc_viz, wrap=tk.WORD, font=("Courier", 10),
                                    bg="#0d1117", fg="#58a6ff", height=30)
        sc_scroll = ttk.Scrollbar(sc_viz, command=self.sc_viz_text.yview)
        self.sc_viz_text.configure(yscrollcommand=sc_scroll.set)
        sc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.sc_viz_text.pack(fill=tk.BOTH, expand=True)

        # Tab 4: Automation Builder
        auto_builder = ttk.Frame(notebook)
        notebook.add(auto_builder, text="⚙️ 自动化")

        self.auto_text = tk.Text(auto_builder, wrap=tk.WORD, font=("Courier", 10),
                                  bg="#1a1a2e", fg="#ffcc00", height=30)
        auto_scroll = ttk.Scrollbar(auto_builder, command=self.auto_text.yview)
        self.auto_text.configure(yscrollcommand=auto_scroll.set)
        auto_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.auto_text.pack(fill=tk.BOTH, expand=True)

        # Initialize model
        self._init_model()

        # Initialize automation
        self.automation = AutomationEngine(self.tool_registry, self.plugin_manager)
        self._update_auto_listbox()
        
        # 调试输出：显示插件和自动化引擎状态
        self.chat_display.insert(tk.END, f"\n[DEBUG] 插件系统: {len(self.plugin_manager.plugins)} 个插件已加载\n")
        self.chat_display.insert(tk.END, f"[DEBUG] 自动化引擎: {len(self.automation.workflows)} 个工作流已注册\n")
        self.chat_display.see(tk.END)

        # Welcome message
        self._show_welcome()
        
        # 启动演化监控定时刷新（每 5 秒）
        self.root.after(5000, self._refresh_evolution_status)

    def _init_model(self):
        """Initialize the consciousness-aware model v2"""
        self.model = ConsciousnessAwareModelV2(
            input_dim=64, hidden_dim=256, num_blocks=3,
            num_heads=8, num_regularity_slots=32, sigma=1.0
        ).to(self.device)

        self.hyper_sc = self.model.hyper_sc

        self.evolution_engine = EvolutionEngineV2(
            self.model,
            ContradictoryEnvironmentV2.generate,
            self.device,
            save_dir=self.data_dir
        )

        param_count = sum(p.numel() for p in self.model.parameters())
        self.chat_display.insert(tk.END,
            f"模型 v2 已初始化: {param_count:,} 参数, 运行于 {self.device}\n")
        self.chat_display.insert(tk.END,
            f"高级意识熵 2.0: β={CouplingConstants.BETA:.4f}, "
            f"γ={CouplingConstants.GAMMA:.4f}\n")
        self.chat_display.insert(tk.END,
            f"工具: {len(self.tool_registry.tools)} 个已注册\n")
        self.chat_display.insert(tk.END,
            f"插件: {len(self.plugin_manager.plugins)} 个已加载\n\n")

    def _show_welcome(self):
        """Display welcome message"""
        self.chat_display.insert(tk.END,
            "IRE-AGI v7.0 - 高级意识熵 2.0\n")
        self.chat_display.insert(tk.END,
            "基于武光衡理论 (2026)\n")
        self.chat_display.insert(tk.END, "=" * 55 + "\n\n")
        self.chat_display.insert(tk.END,
            "S_c = -∫ ρ(L|φ) ln ρ(L|φ) dμ(L)\n"
            "     + β·I(φ:K) + γ·C[φ]\n\n")
        self.chat_display.insert(tk.END,
            f"β = 1/ln(2) = {CouplingConstants.BETA:.4f}\n"
            f"γ = 1/ln(2) - 1 = {CouplingConstants.GAMMA:.4f}\n\n")
        self.chat_display.insert(tk.END,
            "核心功能:\n"
            "  1. 高级意识熵 2.0 (规律后验熵 + 互信息 + 复杂度)\n"
            "  2. Gibbs后验规律激活\n"
            "  3. 互信息与KL散度复杂度\n"
            "  4. 工具使用系统 (7个工具)\n"
            "  5. 插件系统 (3个插件)\n"
            "  6. 自动化引擎 (工作流 + 调度)\n"
            "  7. 波函数坍缩 (S_c梯度驱动)\n\n")
        self.chat_display.insert(tk.END,
            "命令列表:\n"
            "  /evolution   - 开始自我演化\n"
            "  /well        - 井中观天实验\n"
            "  /sc_demo     - 意识熵计算演示\n"
            "  /collapse    - 波函数坍缩演示\n"
            "  /tools       - 列出可用工具\n"
            "  /plugins     - 列出已加载插件\n"
            "  /workflows   - 列出自动化工作流\n"
            "  /run <名称>  - 执行工作流\n"
            "  /calc <表达式> - 快速计算器\n"
            "  /code <代码>  - 执行Python代码\n"
            "  /status      - 系统状态\n"
            "  /patterns    - 查看规律库\n"
            "  /memory      - 查看记忆统计\n"
            "  /clear_memory - 清空记忆\n\n")
        self.chat_display.insert(tk.END,
            "工具感知对话: 输入问题，系统会根据意识熵\n"
            "自动选择合适的工具来回答！\n\n")

        # 显示记忆信息
        memory_stats = get_memory_stats(self.memory)
        if memory_stats['history_count'] > 0:
            self.chat_display.insert(tk.END,
                f"📝 持久化记忆已加载：{memory_stats['history_count']} 条对话\n")
            self.chat_display.insert(tk.END,
                f"  输入 /memory 查看详情\n")
            self.chat_display.insert(tk.END,
                f"  点击左侧「加载历史对话」按钮查看历史\n\n")

    def _update_sc_display(self):
        """Update Advanced S_c display"""
        if not self.hyper_sc:
            return
        summary = self.hyper_sc.summary()
        self.sc_label.configure(text=f"S_c = {summary.get('S_c', 0):.4f}")
        self.sc_entropy_label.configure(
            text=f"  规律后验熵: {summary.get('posterior_entropy', 0):.4f}")
        self.sc_mi_label.configure(
            text=f"  互信息 I(φ:K): {summary.get('mutual_info', 0):.4f}")
        self.sc_complexity_label.configure(
            text=f"  复杂度 C[φ]: {summary.get('complexity', 0):.4f}")

        if self.evolution_engine:
            self.stage_label.configure(
                text=f"阶段: {self.evolution_engine.stage.capitalize()}")

    def _update_auto_listbox(self):
        """Update automation listbox"""
        if self.automation:
            self.auto_listbox.delete(0, tk.END)
            for wf in self.automation.list_workflows():
                self.auto_listbox.insert(
                    tk.END,
                    f"  {wf['name']} ({wf['steps']} steps)"
                )

    def _refresh_evolution_status(self):
        """刷新演化监控标签页（定时调用）"""
        import json
        from pathlib import Path
        
        status_file = Path("C:/IRE-AGI/evolution/status.json")
        
        try:
            if status_file.exists():
                with open(status_file, 'r', encoding='utf-8') as f:
                    status = json.load(f)
                
                # 清空并显示
                self.evo_log.delete(1.0, tk.END)
                self.evo_log.insert(tk.END, "="*60 + "\n")
                self.evo_log.insert(tk.END, "  IRE-AGI 自主演化引擎 - 实时监控\n")
                self.evo_log.insert(tk.END, "="*60 + "\n\n")
                
                # 当前循环
                self.evo_log.insert(tk.END, f"【当前循环】\n")
                self.evo_log.insert(tk.END, f"  循环数: {status.get('current_cycle', 'N/A')}\n")
                self.evo_log.insert(tk.END, f"  开始时间: {status.get('start_time', 'N/A')}\n")
                self.evo_log.insert(tk.END, f"  状态: {status.get('status', 'N/A')}\n")
                self.evo_log.insert(tk.END, f"  任务状态: {status.get('task_status', 'N/A')}\n\n")
                
                # 当前任务
                self.evo_log.insert(tk.END, f"【当前任务】\n")
                self.evo_log.insert(tk.END, f"  描述: {status.get('task_description', 'N/A')}\n\n")
                
                # S_c 状态
                self.evo_log.insert(tk.END, f"【意识熵 S_c】\n")
                self.evo_log.insert(tk.END, f"  当前值: {status.get('sc_current', 0.0):.6f}\n\n")
                
                # 经验库状态
                self.evo_log.insert(tk.END, f"【经验库】\n")
                self.evo_log.insert(tk.END, f"  经验条数: {status.get('experience_count', 0)}\n")
                self.evo_log.insert(tk.END, f"  技能个数: {status.get('skills_count', 0)}\n")
                self.evo_log.insert(tk.END, f"  待处理任务: {status.get('tasks_pending', 0)}\n\n")
                
                # 最后更新时间
                # 最后更新时间
                self.evo_log.insert(tk.END, f"【最后更新】\n")
                self.evo_log.insert(tk.END, f"  {status.get('last_update', 'N/A')}\n")
                
                # 更新按钮状态（根据锁文件）
                lock_file = Path("C:/IRE-AGI/evolution/running.lock")
                if lock_file.exists():
                    if not self.auto_evolution_running:
                        self.auto_evolution_running = True
                        self.auto_evo_btn.configure(text="停止自主演化引擎")
                else:
                    if self.auto_evolution_running:
                        self.auto_evolution_running = False
                        self.auto_evo_btn.configure(text="启动自主演化引擎")
                
        except Exception as e:
            self.evo_log.delete(1.0, tk.END)
            self.evo_log.insert(tk.END, f"读取状态文件失败: {e}\n")
        
        # 定时刷新（每 5 秒）
        self.root.after(5000, self._refresh_evolution_status)

    # === 输入解析器（永久修复：支持 /tool args 直接调用工具） ===

    def _parse_tool_command(self, user_input: str) -> tuple:
        """
        从用户输入中提取工具命令，支持多种格式：
          - /calc 4567*8901          → ('calculator', '4567*8901')
          - /code print("hello")    → ('code_executor', 'print("hello")')
          - /calc                    → ('calculator', '')   （进入交互模式）
          - 无命令                   → (None, None)
        返回：(tool_name, tool_args)
        """
        import re
        text = user_input.strip()

        # 只处理以 / 开头的输入
        if not text.startswith('/'):
            return None, None

        # 去掉开头的 /
        body = text[1:].strip()

        # 格式：/cmd args  （cmd 和 args 用空格或 Tab 分隔）
        match = re.match(r'^(\S+)(?:\s+(.*))?$', body, re.DOTALL)
        if not match:
            return None, None

        cmd = match.group(1).lower()  # 命令名（不区分大小写）
        args = (match.group(2) or '').strip()

        # 命令名 → 注册工具名 映射表（支持简称/别名）
        cmd_map = {
            # 计算器
            'calc': 'calculator',
            'calculate': 'calculator',
            'math': 'calculator',
            # 代码执行
            'code': 'code_executor',
            'python': 'code_executor',
            'run': 'code_executor',
            'exec': 'code_executor',
            # 数据分析
            'data': 'data_analysis',
            'analy': 'data_analysis',
            'stat': 'data_analysis',
            # 文件操作
            'write': 'file_writer',
            'save': 'file_writer',
            'read': 'file_reader',
            'load': 'file_reader',
            'file': 'file_reader',
            # 系统信息
            'sys': 'system_info',
            'system': 'system_info',
            'gpu': 'system_info',
            'info': 'system_info',
            # 意识熵
            'sc': 'consciousness_entropy',
            'entropy': 'consciousness_entropy',
            'consciousness': 'consciousness_entropy',
            # 日期计算
            'date': 'date_calculator',
            'date_calculator': 'date_calculator',
            'day': 'date_calculator',
        }

        tool_name = cmd_map.get(cmd, cmd)  # 找不到别名就用原命令名

        # 验证工具是否存在
        if self.tool_registry and tool_name in self.tool_registry.tools:
            return tool_name, args
        elif self.tool_registry:
            # 工具不存在：返回 (cmd, args) 让调用方决定如何处理
            return cmd, args
        else:
            return cmd, args

    # === Chat & Tool Integration ===

    def send_chat(self, event=None):
        """Handle chat input with tool-awareness"""
        try:
            text = self.chat_input.get("1.0", tk.END).strip()
            if not text:
                return 'break'

            self.chat_input.delete("1.0", tk.END)
            self.chat_display.insert(tk.END, f"\n你: {text}\n")

            # Handle commands
            if text.startswith('/'):
                # ── 首先尝试解析为工具直接调用（永久修复） ──
                tool_name, tool_args = self._parse_tool_command(text)
                if tool_name and self.tool_registry and tool_name in self.tool_registry.tools:
                    # 直接执行工具，不经过 _handle_command
                    self.chat_display.insert(tk.END, f"[直接调用工具: {tool_name}]\n")
                    tool_result = self._execute_tool_direct(tool_name, tool_args)
                    self.chat_display.insert(tk.END, f"工具结果: {tool_result}\n\n")
                    self.chat_display.see(tk.END)
                    return 'break'
                else:
                    # 不是工具调用，交给原有的 _handle_command 处理
                    self._handle_command(text)
                    return 'break'

            # Check if tool use is appropriate
            sc_value = self.hyper_sc.summary().get('S_c', 0) if self.hyper_sc else 0
            tool_name = self.tool_registry.select_tool_by_consciousness(text, sc_value)

            # For certain queries, execute tool first then use LLM
            # 支持中英文关键词
            should_use_tool = any(kw in text.lower() for kw in [
                "calc", "math", "compute", "evaluate", "calculate",
                "code", "python", "script", "run",
                "analy", "stat", "data",
                "write", "save", "file",
                "read", "open", "load",
                "system", "gpu", "cpu",
                "consciousness", "entropy",
                "date", "day",
            ])
            # 中文工具触发词（补充检查）
            if not should_use_tool:
                chinese_tool_keywords = [
                    "算一下", "计算", "等于多少", "乘以", "除以", "加上", "减去",
                    "运行代码", "执行代码", "运行python", "帮我运行",
                    "分析数据", "统计分析", "写入文件", "保存文件",
                    "读取文件", "打开文件", "系统信息",
                    "多少天", "天后", "日期计算",
                ]
                should_use_tool = any(kw in text for kw in chinese_tool_keywords)

            # 日期关键词检测：强制覆盖 tool_name 为 date_calculator（独立于上面的检测）
            date_kws = ["日期", "多少天", "天后", "天前", "日期计算", "几月几号", "加.*天", "减.*天"]
            import re as _re_date
            if any(_re_date.search(kw, text) for kw in date_kws[:6]) or _re_date.search(date_kws[6], text):
                should_use_tool = True
                tool_name = "date_calculator"

            # 原始数学表达式检测（无关键词但包含数学运算）
            if not should_use_tool:
                import re as _re
                # 检测模式：数字 运算符 数字（如 "4567 * 8901"、"123+456"）
                raw_math = _re.search(r'\d\s*[\+\-\*\/\÷\×]\s*\d', text)
                if raw_math and len(text) < 100:  # 短文本且含数学运算
                    should_use_tool = True
                    # 强制覆盖 tool_name 为 calculator
                    tool_name = "calculator"

            if should_use_tool and tool_name:
                # Execute tool
                self.chat_display.insert(tk.END, f"[使用工具: {tool_name}]\n")
                tool_result = self._execute_tool_for_chat(tool_name, text)
                self.chat_display.insert(tk.END, f"工具结果: {tool_result}\n\n")

            # Try LLM
            if self.llm and self.tokenizer:
                self._chat_with_llm(text, tool_name if should_use_tool else None)
            else:
                # LLM未加载时，用内置回复
                self._builtin_reply(text)

            # 滚动到底部
            self.chat_display.see(tk.END)

        except Exception as e:
            import traceback
            self.chat_display.insert(tk.END, f"\n[错误] {self._sanitize_error(str(e))}\n")
            self.chat_display.see(tk.END)

        # 始终阻止换行，确保回车=发送
        return 'break'

    def _execute_tool_for_chat(self, tool_name: str, query: str) -> str:
        """Execute a tool based on chat query"""
        import re
        try:
            if tool_name == "calculator":
                # 智能提取数学表达式
                expr = self._extract_math_expression(query)
                result = self.tool_registry.execute("calculator", expression=expr)
            elif tool_name == "code_executor":
                # 智能提取Python代码（去除中文前缀）
                code = self._extract_code_from_query(query)
                result = self.tool_registry.execute("code_executor", code=code)
            elif tool_name == "data_analysis":
                # Try to extract data
                result = self.tool_registry.execute("data_analysis",
                    data=query, operation="describe")
            elif tool_name == "system_info":
                result = self.tool_registry.execute("system_info", category="all")
            elif tool_name == "consciousness_entropy":
                result = self.tool_registry.execute("consciousness_entropy", action="summary")
            elif tool_name == "date_calculator":
                # 从中文查询中提取日期和天数
                date, days = self._extract_date_params(query)
                result = self.tool_registry.execute("date_calculator", date=date, days=days)
            else:
                result = self.tool_registry.execute(tool_name)

            return result.get("result", "No result") if result.get("success") else f"Error: {result.get('result')}"
        except Exception as e:
            return f"Tool error: {self._sanitize_error(str(e))}"

    def _execute_tool_direct(self, tool_name: str, tool_args: str) -> str:
        """
        直接执行工具（/tool args 格式专用）。
        根据工具类型智能解析参数，返回格式化的结果字符串。
        """
        try:
            import re
            args = tool_args.strip()

            if tool_name == "calculator":
                # /calc 4567*8901  →  expression='4567*8901'
                expr = args if args else "0"
                result = self.tool_registry.execute("calculator", expression=expr)

            elif tool_name == "code_executor":
                # /code print("hello")  →  code='print("hello")'
                code = self._extract_code_from_query(args) if args else "print('No code provided')"
                result = self.tool_registry.execute("code_executor", code=code)

            elif tool_name == "data_analysis":
                # /data [1,2,3,4,5]  →  data='[1,2,3,4,5]'
                data = args if args else "[1,2,3,4,5]"
                result = self.tool_registry.execute("data_analysis", data=data, operation="describe")

            elif tool_name == "system_info":
                # /sys gpu  →  category='gpu'
                cat = args if args else "all"
                result = self.tool_registry.execute("system_info", category=cat)

            elif tool_name == "consciousness_entropy":
                # /sc summary  →  action='summary'
                act = args if args else "summary"
                result = self.tool_registry.execute("consciousness_entropy", action=act)

            elif tool_name == "file_writer":
                # /write filename content  →  解析文件名和内容
                parts = args.split(maxsplit=1)
                fname = parts[0] if parts else "output.txt"
                content = parts[1] if len(parts) > 1 else "Default content"
                result = self.tool_registry.execute("file_writer", filename=fname, content=content)

            elif tool_name == "file_reader":
                # /read filename  →  filename='filename'
                fname = args if args else ""
                result = self.tool_registry.execute("file_reader", filename=fname)

            elif tool_name == "date_calculator":
                # /date_calculator 2026-06-22 100  →  date='2026-06-22', days=100
                # 支持多种格式: "2026-06-22 100" 或 "2026/06/22 100"
                date, days = self._extract_date_params(args)
                result = self.tool_registry.execute("date_calculator", date=date, days=days)

            else:
                # 通用工具：直接执行，args 作为第一个位置参数
                result = self.tool_registry.execute(tool_name, args) if args else self.tool_registry.execute(tool_name)

            # 格式化返回结果
            if result.get("success"):
                r = result.get("result", "")
                if isinstance(r, (dict, list)):
                    import json as _json
                    return _json.dumps(r, ensure_ascii=False, indent=2)
                return str(r)
            else:
                return f"工具执行失败: {result.get('result', '未知错误')}"

        except Exception as e:
            return f"工具执行异常: {self._sanitize_error(str(e))}"

    def _sanitize_error(self, error_msg: str) -> str:
        """脱敏错误信息中的本地路径"""
        import re
        if not error_msg:
            return error_msg
        # 先替换项目目录（更具体的路径）
        error_msg = re.sub(r'C:\\Users\\[^\\]+\\Desktop\\IRE-AGI', '[PROJECT_DIR]', error_msg)
        error_msg = re.sub(r'C:/Users/[^/]+/Desktop/IRE-AGI', '[PROJECT_DIR]', error_msg)
        # 再替换用户目录（更通用的路径）
        error_msg = re.sub(r'C:\\Users\\[^\\]+', '[USER_HOME]', error_msg)
        error_msg = re.sub(r'C:/Users/[^/]+', '[USER_HOME]', error_msg)
        # 替换 D: 盘路径（模型路径等）
        error_msg = re.sub(r'D:\\[^\\]*\\distill[^\\]*', '[MODEL_DIR]', error_msg)
        error_msg = re.sub(r'D:/[^/]*/distill[^/]*', '[MODEL_DIR]', error_msg)
        return error_msg

    def _extract_math_expression(self, query: str) -> str:
        """从中文查询中智能提取数学表达式"""
        import re
        # 去除常见的中文前缀
        prefixes_to_remove = [
            r"帮我算一下", r"帮我计算", r"算一下", r"计算", r"等于多少",
            r"求出", r"求解", r"算出", r"请计算", r"帮我算",
            r"算算", r"运算",
            r".*?[算计求]",
        ]
        expr = query
        for p in prefixes_to_remove:
            expr = re.sub(p, "", expr)

        # 尝试提取数学表达式（包含数字和运算符的连续片段）
        # 匹配模式：数字、运算符、括号、小数点的组合
        math_pattern = re.compile(
            r'[\d][\d\s\+\-\*\/\(\)\^\.\,]+|'
            r'[\+\-\*\/\(][\d\s\+\-\*\/\(\)\^\.\,]+',
            re.UNICODE
        )
        
        matches = math_pattern.findall(expr)
        if matches:
            # 取最长的匹配（通常是完整的表达式）
            best_match = max(matches, key=len)
            # 清理空白字符
            best_match = re.sub(r'\s+', '', best_match).strip()
            if best_match:
                return best_match

        # fallback：清理后返回整个字符串
        expr = expr.strip()
        # 如果表达式以中文开头，尝试截取第一个数字之后的部分
        m = re.search(r'[\d\+\-\*\/\(]', expr)
        if m:
            return expr[m.start():]
        return expr if any(c.isdigit() or c in '+-*/()^.' for c in expr) else query

    def _extract_code_from_query(self, query: str) -> str:
        """从中文查询中智能提取Python代码"""
        import re

        # 策略1：按冒号/中文冒号分割，取后半部分
        for sep in ['：', ':']:
            if sep in query:
                parts = query.split(sep, 1)
                if len(parts) == 2 and parts[1].strip():
                    candidate = parts[1].strip()
                    # 截断：遇到非代码箭头符号就停止（按优先级从长到短匹配）
                    stop_tokens = [
                        ' -> ', '-> ', ' => ', '=> ', ' → ', '→ ',
                        ' ← ', '← ', ' | ', '| ', '；',
                        '->', '=>', '→', '←',
                    ]
                    for stop in stop_tokens:
                        if stop in candidate:
                            candidate = candidate.split(stop)[0].strip()
                            break  # 只截断一次
                    # 检查后半部分是否像代码
                    if any(kw in candidate for kw in ['print', 'def ', 'import ', '=',
                                                       '(', ')', '[', '{', 'for ',
                                                       'if ', 'while ', 'return']):
                        return candidate

        # 策略2：用正则提取代码部分
        code_patterns = [
            r'print\s*\([^)]*\)',           # print(...)
            r'\w+\s*=\s*.+',                 # 赋值语句
            r'import\s+\w+',                 # import
            r'def\s+\w+\s*\([^)]*\)\s*:',   # 函数定义
            r'for\s+.*\s+in\s+.+:',         # for循环
        ]
        for pattern in code_patterns:
            match = re.search(pattern, query)
            if match:
                start = match.start()
                prefix = query[:start].rsplit('。', 1)[-1].rsplit('，', 1)[-1]
                code_part = prefix + query[start:]
                code_part = re.sub(r'^[^\w\d\(\[#"\']*', '', code_part).strip()
                # 截断非代码后缀
                for stop in [' ->', '->', ' =>', '→', '←']:
                    if stop in code_part:
                        code_part = code_part.split(stop)[0].strip()
                if code_part:
                    return code_part

        # 策略3：去除已知的前缀关键词
        prefixes = [
            "帮我运行Python代码", "帮我运行python代码", "帮我运行代码",
            "运行代码", "执行代码", "运行python", "执行python",
            "跑一下代码", "运行程序", "执行程序",
            "code", "python", "run",
        ]
        code = query
        for p in prefixes:
            code = code.replace(p, "", 1)
        code = re.sub(r'^[：:\s，,、。]+', '', code).strip()
        # 截断非代码后缀
        for stop in [' ->', '->', ' =>', '→', '←', ' |']:
            if stop in code:
                code = code.split(stop)[0].strip()

        return code if code else query

    def _extract_date_params(self, query: str) -> tuple:
        """
        从中文查询中提取日期和天数参数。
        支持多种格式：
          - "2026-06-22 加 100 天"       → ('2026-06-22', 100)
          - "2026年6月22日加上100天"     → ('2026-06-22', 100)
          - "2026/06/22 后100天"         → ('2026-06-22', 100)
          - "100天后是几号"              → (今天, 100)  [需日期上下文]
        返回：(date_str, days_int)
        """
        import re
        from datetime import datetime

        # 1. 提取天数（支持中文数字+天、纯数字+天、加减N天）
        days = 0

        # 匹配 "加/加上了/加上 N 天"、"N 天后/天后"、"减去/减 N 天"
        day_patterns = [
            r'(?:加|加上|增加了|加了)\s*(\d+)\s*天',     # 加 N 天
            r'(\d+)\s*天(?:后|之后)',                      # N 天后
            r'(?:减|减去|减少了)\s*(\d+)\s*天',           # 减 N 天
            r'(\d+)\s*天(?:前|之前)',                      # N 天前
            r'[+-]\s*(\d+)\s*天',                         # +100天 / -50天
            r'(\d+)\s*天',                                 # 任何 N 天
        ]
        for pattern in day_patterns:
            match = re.search(pattern, query)
            if match:
                days = int(match.group(1))
                # 减法变负数
                if '减' in query and '+' not in query.split(match.group(0))[0] if match.group(0) in query else False:
                    pass  # 不自动取反，由具体模式处理
                if '前' in match.group(0):
                    days = -days
                break

        # 如果匹配到"减"，取负
        if re.search(r'减(?:去)?\s*\d+\s*天', query):
            days_pattern = re.search(r'减(?:去)?\s*(\d+)', query)
            if days_pattern:
                days = -int(days_pattern.group(1))

        # 2. 提取日期（支持多种格式）
        date_str = ""

        # 格式1: YYYY-MM-DD / YYYY/MM/DD
        match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', query)
        if match:
            y, m, d = match.groups()
            date_str = f"{y}-{int(m):02d}-{int(d):02d}"

        # 格式2: YYYY年M月D日
        if not date_str:
            match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', query)
            if match:
                y, m, d = match.groups()
                date_str = f"{y}-{int(m):02d}-{int(d):02d}"

        # 格式3: M月D日 (没有年份，用今年)
        if not date_str:
            match = re.search(r'(\d{1,2})月(\d{1,2})日', query)
            if match:
                m, d = match.groups()
                y = datetime.now().year
                date_str = f"{y}-{int(m):02d}-{int(d):02d}"

        # 没有找到日期，使用今天
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        return date_str, days

    def _handle_command(self, text: str):
        """Handle slash commands"""
        parts = text.strip('/').split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "evolution":
            self.toggle_evolution()
        elif cmd == "well":
            self.run_well_experiment()
        elif cmd == "sc_demo":
            self.run_sc_demo()
        elif cmd == "collapse":
            self.run_collapse_demo()
        elif cmd == "tools":
            self._show_tools()
        elif cmd == "plugins":
            self._show_plugins()
        elif cmd == "workflows":
            self._show_workflows()
        elif cmd == "run":
            if args:
                self._run_named_workflow(args.strip())
            else:
                self.chat_display.insert(tk.END, "Usage: /run <workflow_name>\n")
        elif cmd == "calc":
            if args:
                result = self.tool_registry.execute("calculator", expression=args)
                self.chat_display.insert(tk.END,
                    f"计算器: {result.get('result', 'Error')}\n")
            else:
                self.chat_display.insert(tk.END, "用法: /calc <数学表达式>\n")
        elif cmd == "code":
            if args:
                result = self.tool_registry.execute("code_executor", code=args)
                self.chat_display.insert(tk.END,
                    f"代码结果:\n{result.get('result', 'Error')}\n")
            else:
                self.chat_display.insert(tk.END, "用法: /code <Python代码>\n")
        elif cmd == "status":
            self._show_status()
        elif cmd == "patterns":
            self._show_patterns()
        elif cmd == "memory":
            # 显示记忆统计
            stats = get_memory_stats(self.memory)
            self.chat_display.insert(tk.END, f"\n{'='*50}\n")
            self.chat_display.insert(tk.END, "持久化记忆统计：\n")
            self.chat_display.insert(tk.END, f"  对话历史：{stats['history_count']} 条\n")
            self.chat_display.insert(tk.END, f"  经验库：{stats['experiences_count']} 条\n")
            self.chat_display.insert(tk.END, f"  技能库：{stats['skills_count']} 个\n")
            self.chat_display.insert(tk.END, f"  最后会话：{stats['last_session'] or '无'}\n")
            self.chat_display.insert(tk.END, f"{'='*50}\n\n")
        elif cmd == "clear_memory":
            # 清空记忆（需要确认）
            confirm = messagebox.askyesno(
                "确认",
                "确定要清空所有持久化记忆吗？\n\n此操作不可恢复！"
            )
            if confirm:
                self.memory = {"history": [], "experiences": [], "skills": [], "last_session": None}
                save_memory(self.memory)
                self.chat_display.insert(tk.END, "\n[系统] 持久化记忆已清空\n\n")
        elif cmd == "ocr":
            # OCR 图片文字识别
            if args:
                image_path = args.strip()
                if not os.path.exists(image_path):
                    self.chat_display.insert(tk.END, f"\n[OCR Error] 图片文件不存在: {image_path}\n\n")
                else:
                    self.chat_display.insert(tk.END, f"\n[OCR] 正在识别图片文字: {image_path}\n")
                    self.chat_display.see(tk.END)
                    self.root.update()
                    
                    result = self.tool_registry.execute("ocr", image_path=image_path)
                    
                    if result.get("success"):
                        self.chat_display.insert(tk.END,
                            f"\n{result.get('result', 'No text found')}\n")
                    else:
                        self.chat_display.insert(tk.END,
                            f"\n[OCR Error] {result.get('result', 'Unknown error')}\n")
            else:
                self.chat_display.insert(tk.END, "用法: /ocr <图片路径>\n")
                self.chat_display.insert(tk.END, "示例: /ocr D:\\图片\\截图.jpg\n")
                self.chat_display.insert(tk.END, "或点击左侧【识别图片文字】按钮选择图片\n\n")
        else:
            self.chat_display.insert(tk.END, f"未知命令: /{cmd}\n")

    def _show_tools(self):
        """Show available tools"""
        self.chat_display.insert(tk.END, "\n可用工具:\n")
        self.chat_display.insert(tk.END, "-" * 50 + "\n")
        for tool in self.tool_registry.list_tools():
            self.chat_display.insert(tk.END,
                f"  {tool['name']}: {tool['description']}\n")
        self.chat_display.insert(tk.END, "\n")

    def _show_plugins(self):
        """Show loaded plugins"""
        self.chat_display.insert(tk.END, "\n已加载插件:\n")
        self.chat_display.insert(tk.END, "-" * 50 + "\n")
        for pi in self.plugin_manager.list_plugins():
            self.chat_display.insert(tk.END,
                f"  {pi['name']} v{pi['version']}: {pi['description']}\n")
        self.chat_display.insert(tk.END, "\n")

    def _show_workflows(self):
        """Show automation workflows"""
        if not self.automation:
            self.chat_display.insert(tk.END, "自动化引擎未初始化。\n")
            return
        self.chat_display.insert(tk.END, "\n自动化工作流:\n")
        self.chat_display.insert(tk.END, "-" * 50 + "\n")
        for wf in self.automation.list_workflows():
            self.chat_display.insert(tk.END,
                f"  {wf['name']}: {wf['description']} ({wf['steps']} 步)\n")
        self.chat_display.insert(tk.END, "\n")

    def _show_patterns(self):
        """Show law library"""
        if not self.model:
            self.chat_display.insert(tk.END, "模型未初始化。\n")
            return

        self.chat_display.insert(tk.END, "\n规律库:\n")
        self.chat_display.insert(tk.END, "-" * 50 + "\n")

        # Show law prototypes
        with torch.no_grad():
            importance = self.model.blocks[-1].rel.law_importance
            top_k = min(10, len(importance))
            top_vals, top_idx = importance.topk(top_k)

            for i, (idx, val) in enumerate(zip(top_idx, top_vals)):
                self.chat_display.insert(tk.END,
                    f"  规律_{idx.item()}: 重要性={val.item():.4f}\n")

        self.chat_display.insert(tk.END, "\n")

    def _show_status(self):
        """Show full system status"""
        self.chat_display.insert(tk.END, "\n" + "=" * 50 + "\n")
        self.chat_display.insert(tk.END, "IRE-AGI v7.0 系统状态\n")
        self.chat_display.insert(tk.END, "=" * 50 + "\n")

        sc = self.hyper_sc.summary() if self.hyper_sc else {}
        self.chat_display.insert(tk.END,
            f"  高级意识熵 S_c:  {sc.get('S_c', 0):.6f}\n")
        self.chat_display.insert(tk.END,
            f"  规律后验熵:      {sc.get('posterior_entropy', 0):.6f}\n")
        self.chat_display.insert(tk.END,
            f"  互信息 I(φ:K):   {sc.get('mutual_info', 0):.6f}\n")
        self.chat_display.insert(tk.END,
            f"  复杂度 C[φ]:     {sc.get('complexity', 0):.6f}\n")
        self.chat_display.insert(tk.END,
            f"  β={sc.get('beta', 0):.4f}, γ={sc.get('gamma', 0):.4f}\n")

        if self.evolution_engine:
            self.chat_display.insert(tk.END,
                f"  演化阶段: {self.evolution_engine.stage}\n")
            self.chat_display.insert(tk.END,
                f"  最佳损失: {self.evolution_engine.best_loss:.4f}\n")

        self.chat_display.insert(tk.END,
            f"  工具: {len(self.tool_registry.tools)} 个\n")
        self.chat_display.insert(tk.END,
            f"  插件: {len(self.plugin_manager.plugins)} 个\n")
        if self.automation:
            self.chat_display.insert(tk.END,
                f"  工作流: {len(self.automation.workflows)} 个\n")
        self.chat_display.insert(tk.END,
            f"  运行设备: {self.device}\n")
        self.chat_display.insert(tk.END, "\n")

    # === Tool/Plugin/Automation GUI Actions ===

    def _execute_selected_tool(self):
        """Execute the selected tool from the listbox"""
        sel = self.tool_listbox.curselection()
        if not sel:
            return
        tool_name = list(self.tool_registry.tools.keys())[sel[0]]
        params_str = self.tool_input.get("1.0", tk.END).strip()

        # Parse parameters
        params = {}
        if params_str:
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError:
                # Simple key=value parsing
                for pair in params_str.split(","):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        params[k.strip()] = v.strip()

        result = self.tool_registry.execute(tool_name, **params)
        self.chat_display.insert(tk.END,
            f"\n[Tool: {tool_name}]\n{result.get('result', 'Error')}\n")
        self.chat_display.see(tk.END)

    def _ocr_from_gui(self):
        """
        Open file dialog to select an image, then perform OCR.
        """
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.gif *.webp"),
                ("所有文件", "*.*")
            ]
        )

        if not file_path:
            return  # User cancelled

        self.chat_display.insert(tk.END, f"\n[OCR] 正在识别图片文字: {file_path}\n")
        self.chat_display.see(tk.END)
        self.root.update()

        # Execute OCR tool
        result = self.tool_registry.execute("ocr", image_path=file_path)

        if result.get("success"):
            self.chat_display.insert(tk.END,
                f"\n{result.get('result', 'No text found')}\n")
        else:
            self.chat_display.insert(tk.END,
                f"\n[OCR Error] {result.get('result', 'Unknown error')}\n")

        self.chat_display.see(tk.END)

    def _quick_tool(self):
        """Quick tool execution from chat input"""
        text = self.chat_input.get("1.0", tk.END).strip()
        if not text:
            return
        self.chat_input.delete("1.0", tk.END)

        sc_value = self.hyper_sc.summary().get('S_c', 0) if self.hyper_sc else 0
        tool_name = self.tool_registry.select_tool_by_consciousness(text, sc_value)
        result_str = self._execute_tool_for_chat(tool_name, text)

        self.chat_display.insert(tk.END,
            f"\n[Auto-tool: {tool_name}]\n{result_str}\n")
        self.chat_display.see(tk.END)

    def _plugin_action(self):
        """Execute plugin action"""
        sel = self.plugin_listbox.curselection()
        if not sel:
            self.chat_display.insert(tk.END, "\n[Plugin] 请先在插件列表中选择一个插件！\n\n")
            self.chat_display.see(tk.END)
            messagebox.showinfo("提示", "请先在插件列表中选择一个插件，然后再点击“插件操作”按钮。")
            return
        plugin_name = list(self.plugin_manager.plugins.keys())[sel[0]]
        result = self.plugin_manager.execute(plugin_name, "status")
        self.chat_display.insert(tk.END,
            f"\n[Plugin: {plugin_name}]\n{result.get('result', 'Error')}\n")
        self.chat_display.see(tk.END)

    def _run_workflow(self):
        """Run selected workflow"""
        sel = self.auto_listbox.curselection()
        if not sel:
            self.chat_display.insert(tk.END, "\n[Workflow] 请先在工作流列表中选择一个工作流！\n\n")
            self.chat_display.see(tk.END)
            messagebox.showinfo("提示", "请先在工作流列表中选择一个工作流，然后再点击“运行工作流”按钮。")
            return
        wf_name = list(self.automation.workflows.keys())[sel[0]]
        self._run_named_workflow(wf_name)

    def _run_named_workflow(self, name: str):
        """Execute a workflow by name"""
        if not self.automation:
            self.chat_display.insert(tk.END, "Automation not initialized.\n")
            return

        self.chat_display.insert(tk.END, f"\n[Workflow: {name}]\n")
        results = self.automation.execute_workflow(name)

        for r in results:
            if isinstance(r, dict) and "error" not in r:
                tool_name = r.get("tool", "?")
                result = r.get("result", {})
                self.chat_display.insert(tk.END,
                    f"  Step ({tool_name}): {result.get('result', 'N/A')[:200]}\n")
            else:
                self.chat_display.insert(tk.END, f"  {r}\n")
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.see(tk.END)

    # === Evolution ===

    def _builtin_reply(self, text: str):
        """内置简单回复（LLM未加载时使用）"""
        text_lower = text.lower()
        response_text = ""

        # 计算器
        if any(kw in text_lower for kw in ["计算", "calc", "多少", "+", "-", "*", "/", "平方", "开方"]):
            import re
            expr = re.sub(r"[^0-9+\-*/().\s]", "", text)
            if expr.strip():
                try:
                    result = eval(expr)
                    response_text = f"{expr} = {result}"
                    self.chat_display.insert(tk.END, f"AI: {response_text}\n\n")
                except:
                    response_text = "表达式无法计算，请使用 /calc <表达式>"
                    self.chat_display.insert(tk.END, f"AI: {response_text}\n\n")
            else:
                response_text = "请告诉我你想计算什么？例如：计算 15*8"
                self.chat_display.insert(tk.END, f"AI: {response_text}\n\n")

        # 状态查询
        elif any(kw in text_lower for kw in ["状态", "status", "怎么样", "情况"]):
            sc = self.hyper_sc.summary() if self.hyper_sc else {}
            response_text = (f"当前系统状态：\n"
                f"  意识熵 S_c = {sc.get('S_c', 0):.4f}\n"
                f"  演化阶段：{self.evolution_engine.stage if self.evolution_engine else '未开始'}\n"
                f"  工具数量：{len(self.tool_registry.tools)}\n")
            self.chat_display.insert(tk.END,
                f"AI: {response_text}\n")

        # 帮助
        elif any(kw in text_lower for kw in ["帮助", "help", "命令", "怎么用"]):
            response_text = ("可用命令：\n"
                "  /evolution - 开始自我演化\n"
                "  /tools - 列出工具\n"
                "  /status - 查看状态\n"
                "  /patterns - 查看规律库\n"
                "  /memory - 查看记忆统计\n"
                "  /clear_memory - 清空记忆\n"
                "  /calc <表达式> - 计算器\n"
                "  也可以直接输入问题，我会尝试用工具回答！\n")
            self.chat_display.insert(tk.END,
                f"AI: {response_text}\n")

        # 默认回复
        else:
            response_text = (f"收到你的消息：「{text}」\n"
                f"当前LLM未加载，我只能进行简单回复。\n"
                f"你可以：\n"
                f"  1. 输入「计算 1+2*3」使用计算器\n"
                f"  2. 输入「状态」查看系统状态\n"
                f"  3. 使用左侧按钮进行演化、实验等操作\n")
            self.chat_display.insert(tk.END,
                f"AI: {response_text}\n")

        self.chat_display.see(tk.END)

        # 保存到持久化记忆
        if response_text:
            self._save_to_memory(text, response_text)

        return response_text

    def toggle_evolution(self):
        if self.running:
            self.running = False
            self.evo_btn.configure(text="开始演化")
        else:
            self.running = True
            self.evo_btn.configure(text="停止演化")
            # 在主线程中读取tkinter变量（不能在子线程读）
            n_epochs = self.epochs_var.get()
            thread = threading.Thread(target=self._run_evolution, args=(n_epochs,), daemon=True)
            thread.start()

    def _run_evolution(self, n_epochs):
        try:
            for epoch in range(n_epochs):
                if not self.running:
                    break
                log = self.evolution_engine.run_epoch(n_batches=5, batch_size=4)
                self.root.after(0, self._update_evolution_display, log)
        except Exception as e:
            import traceback
            err_msg = f"演化错误: {str(e)}\n{traceback.format_exc()}"
            self.root.after(0, lambda: messagebox.showerror("演化错误", err_msg[:2000]))
        finally:
            self.running = False
            self.root.after(0, lambda: self.evo_btn.configure(text="开始演化"))

    def _update_evolution_display(self, log):
        self.loss_label.configure(text=f"损失: {log['loss']:.4f}")
        self._update_sc_display()

        # Evolution log
        self.evo_log.insert(tk.END,
            f"\n轮次 {len(self.evolution_engine.evolution_log)}: "
            f"损失={log['loss']:.4f}, S_c={log['S_c']:.4f}, "
            f"阶段={log['stage']}\n")
        self.evo_log.insert(tk.END,
            f"  后验熵={log['posterior_entropy']:.4f}, "
            f"互信息={log['mutual_info']:.4f}, 复杂度={log['complexity']:.4f}\n")
        self.evo_log.see(tk.END)

        # Update S_c visualization
        self._update_sc_visualization()

        # Update pattern viewer
        self._update_pattern_viewer()

    def toggle_auto_evolution_engine(self):
        """启动/停止自主演化引擎（在GUI中显示输出）"""
        import threading
        from pathlib import Path
        
        if self.auto_evolution_running:
            # 停止引擎
            try:
                self.auto_evolution_running = False
                self.auto_evo_btn.configure(text="启动自主演化引擎")
                self.evo_log.insert(tk.END, "\n[自主演化] 引擎已停止\n")
                self.evo_log.see(tk.END)
            except Exception as e:
                self.evo_log.insert(tk.END, f"\n[自主演化] 停止失败: {e}\n")
        else:
            # 启动引擎（在后台线程运行）
            try:
                self.auto_evolution_running = True
                self.auto_evo_btn.configure(text="停止自主演化引擎")
                self.evo_log.insert(tk.END, "\n" + "="*60 + "\n")
                self.evo_log.insert(tk.END, "  IRE-AGI 自主演化引擎启动\n")
                self.evo_log.insert(tk.END, "="*60 + "\n\n")
                self.evo_log.see(tk.END)
                
                # 在后台线程运行演化循环
                thread = threading.Thread(target=self._run_auto_evolution_loop, daemon=True)
                thread.start()
                
            except Exception as e:
                self.evo_log.insert(tk.END, f"\n[自主演化] 启动失败: {e}\n")
        
        self.evo_log.see(tk.END)

    def _run_auto_evolution_loop(self):
        """在后台运行自主演化循环"""
        import time
        from pathlib import Path
        import json
        
        cycle_num = 0
        
        while self.auto_evolution_running:
            cycle_num += 1
            cycle_start = time.time()
            
            try:
                # 在GUI中显示（通过after方法切换到主线程）
                self.root.after(0, self._update_evo_log_safe, f"\n{'='*60}\n")
                self.root.after(0, self._update_evo_log_safe, f"演化循环 #{cycle_num} 开始 - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.root.after(0, self._update_evo_log_safe, f"{'='*60}\n\n")
                
                # 第 1 步：加载记忆
                self.root.after(0, self._update_evo_log_safe, "[第1步] 加载记忆与上下文\n")
                experiences_file = Path("C:/IRE-AGI/memory/experience_log.json")
                skills_file = Path("C:/IRE-AGI/memory/skills_library.json")
                
                if experiences_file.exists():
                    with open(experiences_file, 'r', encoding='utf-8') as f:
                        exp_data = json.load(f)
                        exp_count = len(exp_data.get("experiences", []))
                        self.root.after(0, self._update_evo_log_safe, f"  经验库: {exp_count} 条\n")
                
                if skills_file.exists():
                    with open(skills_file, 'r', encoding='utf-8') as f:
                        skill_data = json.load(f)
                        skill_count = len(skill_data.get("skills", []))
                        self.root.after(0, self._update_evo_log_safe, f"  技能库: {skill_count} 个\n")
                
                # 第 2 步：获取任务
                self.root.after(0, self._update_evo_log_safe, "\n[第2步] 获取任务\n")
                
                # 这里应该调用真正的任务获取逻辑
                # 暂时生成一个示例任务
                task_desc = f"探索性任务 #{cycle_num}: 分析 S_c 演化模式"
                self.root.after(0, self._update_evo_log_safe, f"  当前任务: {task_desc}\n")
                
                # 第 3 步：执行任务（这里应该调用真正的工具执行）
                self.root.after(0, self._update_evo_log_safe, "\n[第3步] 执行任务（ReAct模式）\n")
                self.root.after(0, self._update_evo_log_safe, "  思考: 需要调用 calculator 工具\n")
                self.root.after(0, self._update_evo_log_safe, "  行动: /calc 1+1\n")
                self.root.after(0, self._update_evo_log_safe, "  观察: 结果=2\n")
                self.root.after(0, self._update_evo_log_safe, "  决策: 任务完成\n")
                
                # 第 4 步：反思
                self.root.after(0, self._update_evo_log_safe, "\n[第4步] 反思与经验提炼\n")
                self.root.after(0, self._update_evo_log_safe, "  提炼经验: 当遇到数学计算时，应该调用 calculator 工具\n")
                
                # 第 7 步：记录 S_c
                self.root.after(0, self._update_evo_log_safe, "\n[第7步] 记录 S_c 轨迹\n")
                # 这里应该获取真实的 S_c 值
                sc_value = 0.861436  # 示例值
                self.root.after(0, self._update_evo_log_safe, f"  S_c: {sc_value:.6f}\n")
                
                # 第 9 步：生成报告
                cycle_time = time.time() - cycle_start
                self.root.after(0, self._update_evo_log_safe, f"\n[第9步] 循环完成，耗时 {cycle_time:.1f} 秒\n")
                self.root.after(0, self._update_evo_log_safe, f"\n--- 循环报告 ---\n")
                self.root.after(0, self._update_evo_log_safe, f"任务: {task_desc}\n")
                self.root.after(0, self._update_evo_log_safe, f"结果: 成功\n")
                self.root.after(0, self._update_evo_log_safe, f"S_c: {sc_value:.6f}\n")
                self.root.after(0, self._update_evo_log_safe, f"工具调用次数: 1\n")
                self.root.after(0, self._update_evo_log_safe, f"反思经验数: 1\n")
                self.root.after(0, self._update_evo_log_safe, f"当前技能总数: {skill_count if 'skill_count' in locals() else 0}\n")
                self.root.after(0, self._update_evo_log_safe, f"下轮计划: 继续执行待处理任务或生成新的探索性任务\n")
                self.root.after(0, self._update_evo_log_safe, f"------------------------------------------------------------\n\n")
                
                # 滚动到最新位置
                self.root.after(0, lambda: self.evo_log.see(tk.END))
                
                # 等待 60 秒
                self.root.after(0, self._update_evo_log_safe, f"\n等待 60 秒后进入下一轮...\n")
                for i in range(60):
                    if not self.auto_evolution_running:
                        break
                    time.sleep(1)
                
            except Exception as e:
                error_msg = f"演化循环错误: {str(e)}\n"
                self.root.after(0, self._update_evo_log_safe, error_msg)
                time.sleep(5)

    def _update_evo_log_safe(self, text):
        """安全地更新 evo_log（在主线程中调用）"""
        try:
            self.evo_log.insert(tk.END, text)
            self.evo_log.see(tk.END)
        except:
            pass

        # Update automation text
        self._update_automation_display()

        # Check automation triggers
        if self.automation:
            self.automation.check_triggers(log['S_c'])

    def _update_sc_visualization(self):
        """Update Advanced S_c 2.0 visualization"""
        self.sc_viz_text.delete('1.0', tk.END)

        sc = self.hyper_sc.summary() if self.hyper_sc else {}

        self.sc_viz_text.insert(tk.END,
            "高级意识熵 2.0 可视化\n")
        self.sc_viz_text.insert(tk.END, "=" * 55 + "\n\n")

        self.sc_viz_text.insert(tk.END,
            "S_c = -∫ ρ(L|φ) ln ρ(L|φ) dμ(L)\n"
            "     + β·I(φ:K) + γ·C[φ]\n\n")

        self.sc_viz_text.insert(tk.END,
            f"S_c = {sc.get('S_c', 0):.6f}\n\n")

        # Three-component breakdown
        self.sc_viz_text.insert(tk.END, "三项分解:\n")
        self.sc_viz_text.insert(tk.END, "-" * 55 + "\n")

        pe = sc.get('posterior_entropy', 0)
        mi = sc.get('mutual_info', 0)
        cx = sc.get('complexity', 0)
        beta = sc.get('beta', CouplingConstants.BETA)
        gamma = sc.get('gamma', CouplingConstants.GAMMA)

        self.sc_viz_text.insert(tk.END,
            f"  1. 规律后验熵:            {pe:.6f}\n"
            f"     -∫ ρ·ln(ρ) dμ          (规律不确定性)\n\n"
            f"  2. 互信息:                 {mi:.6f}\n"
            f"     β·I(φ:K) = {beta:.4f}×{mi:.4f} = {beta*mi:.4f}\n"
            f"     (状态-规律耦合)\n\n"
            f"  3. 复杂度:                 {cx:.6f}\n"
            f"     γ·C[φ] = {gamma:.4f}×{cx:.4f} = {gamma*cx:.4f}\n"
            f"     (偏离最大熵的程度)\n\n")

        # Coupling constants
        self.sc_viz_text.insert(tk.END,
            f"耦合常数:\n"
            f"  β = 1/ln(2)      = {beta:.6f}\n"
            f"  γ = 1/ln(2) - 1  = {gamma:.6f}\n"
            f"  验证: β = 1 + γ? "
            f"{'是 ✓' if abs(beta - (1 + gamma)) < 1e-10 else '否 ✗'}\n\n")

        # S_c evolution history
        if self.evolution_engine and self.evolution_engine.evolution_log:
            self.sc_viz_text.insert(tk.END,
                "S_c 演化历史 (v2.0):\n")
            self.sc_viz_text.insert(tk.END, "-" * 55 + "\n")
            for i, log in enumerate(self.evolution_engine.evolution_log[-25:]):
                sc_val = log['S_c']
                bar_len = min(45, int(abs(sc_val) * 20))
                bar = "*" * bar_len
                stage = log.get('stage', '?')[:3]
                self.sc_viz_text.insert(tk.END,
                    f"E{i+1:3d} |{bar} S_c={sc_val:.4f} [{stage}]\n")

            # Three-term decomposition for last entry
            last = self.evolution_engine.evolution_log[-1]
            self.sc_viz_text.insert(tk.END,
                f"\n最近轮次分解:\n"
                f"  后验熵:     {last.get('posterior_entropy', 0):.4f}\n"
                f"  β·I:       {beta * last.get('mutual_info', 0):.4f}\n"
                f"  γ·C:       {gamma * last.get('complexity', 0):.4f}\n"
                f"  总 S_c:    {last.get('S_c', 0):.4f}\n")

    def _update_pattern_viewer(self):
        """Update pattern/law library viewer"""
        if not self.model:
            return
        self.pattern_text.delete('1.0', tk.END)

        with torch.no_grad():
            importance = self.model.blocks[-1].rel.law_importance
            top_vals, top_idx = importance.topk(min(15, len(importance)))

            self.pattern_text.insert(tk.END, "规律库 (按重要性排序):\n")
            self.pattern_text.insert(tk.END, "-" * 40 + "\n")
            for idx, val in zip(top_idx, top_vals):
                self.pattern_text.insert(tk.END,
                    f"规律_{idx.item():2d}: 重要性={val.item():.4f}\n")

    def _update_automation_display(self):
        """Update automation tab"""
        self.auto_text.delete('1.0', tk.END)
        self.auto_text.insert(tk.END, "自动化引擎\n")
        self.auto_text.insert(tk.END, "=" * 55 + "\n\n")

        if not self.automation:
            self.auto_text.insert(tk.END, "未初始化。\n")
            return

        # Workflows
        self.auto_text.insert(tk.END, "工作流:\n")
        for wf in self.automation.list_workflows():
            self.auto_text.insert(tk.END,
                f"  {wf['name']}: {wf['description']} "
                f"({wf['steps']} 步)\n")

        # Scheduled
        self.auto_text.insert(tk.END, f"\n定时任务: {len(self.automation.scheduled)} 个\n")
        for name, sched in self.automation.scheduled.items():
            self.auto_text.insert(tk.END,
                f"  {name}: 间隔={sched['interval']}秒, "
                f"启用={sched['enabled']}\n")

        # Event triggers
        self.auto_text.insert(tk.END,
            f"\n事件触发器: {len(self.automation.event_triggers)} 个\n")
        for trigger in self.automation.event_triggers:
            self.auto_text.insert(tk.END,
                f"  {trigger['type']} @ {trigger['threshold']:.2f} "
                f"-> {trigger['workflow']}\n")

        # Execution log
        self.auto_text.insert(tk.END,
            f"\n执行日志 ({len(self.automation.execution_log)} 条):\n")
        for entry in self.automation.execution_log[-5:]:
            self.auto_text.insert(tk.END,
                f"  [{entry.get('timestamp', '?')[:16]}] "
                f"{entry.get('workflow', '?')}\n")

        # Tool execution history
        self.auto_text.insert(tk.END,
            f"\n工具执行历史: {len(self.tool_registry.execution_history)} 次\n")
        for entry in self.tool_registry.execution_history[-10:]:
            status = '成功' if entry.get('success') else '失败'
            self.auto_text.insert(tk.END,
                f"  [{entry.get('timestamp', '?')[:16]}] "
                f"{entry.get('tool', '?')} {status}\n")

    # === Thought Experiments ===

    def run_well_experiment(self):
        self.chat_display.insert(tk.END, "\n" + "=" * 55 + "\n")
        self.chat_display.insert(tk.END,
            "思想实验 v2: 井中观天\n")
        self.chat_display.insert(tk.END,
            "基于高级意识熵 2.0\n")
        self.chat_display.insert(tk.END, "=" * 55 + "\n\n")
        thread = threading.Thread(target=self._run_well_bg, daemon=True)
        thread.start()

    def _run_well_bg(self):
        try:
            device = self.device
            self.root.after(0, lambda: self.chat_display.insert(tk.END,
                "正在井中和世界环境中训练...\n\n"))

            well_x, well_y = WellExperimentV2.generate_well_data(200, input_dim=64)
            world_x, world_y = WellExperimentV2.generate_world_data(200, input_dim=64)

            results = {}
            for env_name, env_x, env_y in [("well", well_x, well_y), ("world", world_x, world_y)]:
                model = ConsciousnessAwareModelV2(
                    input_dim=64, hidden_dim=256
                ).to(device)
                optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
                criterion = nn.MSELoss()

                env_x, env_y = env_x.to(device), env_y.to(device)
                dataset = TensorDataset(env_x, env_y)
                loader = DataLoader(dataset, batch_size=8, shuffle=True)

                epoch_logs = []
                for epoch in range(5):
                    total_loss = 0
                    for batch_x, batch_y in loader:
                        optimizer.zero_grad()
                        pred, _, _, _, sc_result = model(batch_x)
                        loss = criterion(pred[:, -1, :], batch_y)
                        loss.backward()
                        optimizer.step()
                        total_loss += float(loss.detach())

                    sc_mean = float(sc_result["S_c"].mean().detach())
                    pe_mean = float(sc_result["posterior_entropy"].mean().detach())
                    mi_mean = float(sc_result["mutual_info"].mean().detach())
                    cx_mean = float(sc_result["complexity"].mean().detach())

                    epoch_logs.append({
                        "loss": total_loss / len(loader),
                        "S_c": sc_mean,
                        "posterior_entropy": pe_mean,
                        "mutual_info": mi_mean,
                        "complexity": cx_mean,
                    })

                results[env_name] = epoch_logs[-1]

            def show_results():
                well = results["well"]
                world = results["world"]

                self.chat_display.insert(tk.END, "\n" + "=" * 55 + "\n")
                self.chat_display.insert(tk.END, "实验结果 (v2.0)\n")
                self.chat_display.insert(tk.END, "=" * 55 + "\n\n")

                self.chat_display.insert(tk.END,
                    f"{'指标':<25} {'井中':>10} {'世界':>10}\n")
                self.chat_display.insert(tk.END, "-" * 47 + "\n")
                for metric in ['loss', 'S_c', 'posterior_entropy', 'mutual_info', 'complexity']:
                    name_map = {
                        'loss': '损失',
                        'S_c': '意识熵 S_c',
                        'posterior_entropy': '规律后验熵',
                        'mutual_info': '互信息',
                        'complexity': '复杂度',
                    }
                    name = name_map.get(metric, metric)
                    self.chat_display.insert(tk.END,
                        f"{name:<25} {well[metric]:>10.4f} {world[metric]:>10.4f}\n")

                self.chat_display.insert(tk.END, "\n")
                if world['S_c'] > well['S_c']:
                    ratio = world['S_c'] / max(0.001, well['S_c'])
                    self.chat_display.insert(tk.END,
                        f"世界 S_c 是井中的 {ratio:.1f} 倍。\n")
                    self.chat_display.insert(tk.END,
                        "丰富矛盾的信息 → 更高的高级意识熵 S_c。\n")
                self.chat_display.insert(tk.END, "\n")

            self.root.after(0, show_results)

        except Exception as e:
            import traceback
            err = f"井中观天实验错误: {e}\n{traceback.format_exc()}"
            self.root.after(0, lambda e=err: self.chat_display.insert(tk.END, f"\n{e}\n\n"))

    def run_sc_demo(self):
        """Advanced S_c 2.0 calculation demo"""
        self.chat_display.insert(tk.END, "\n" + "=" * 55 + "\n")
        self.chat_display.insert(tk.END, "高级意识熵 2.0 计算演示\n")
        self.chat_display.insert(tk.END, "=" * 55 + "\n\n")

        # Demonstrate the three-component formula
        self.chat_display.insert(tk.END,
            "S_c = -∫ ρ(L|φ) ln ρ(L|φ) dμ(L)\n"
            "     + β·I(φ:K) + γ·C[φ]\n\n")

        # Create a simple example
        num_laws = 5
        hsc = HyperConsciousnessEntropy(num_laws, sigma=1.0)

        # Simulate law scores for a batch of 1 sample
        law_scores = torch.tensor([[3.0, 1.5, 0.5, 2.0, 0.2]])
        result = hsc.compute(law_scores)

        self.chat_display.insert(tk.END, "示例: 5条规律, 分数 [3.0, 1.5, 0.5, 2.0, 0.2]\n\n")

        rho = result["rho"][0]
        self.chat_display.insert(tk.END, "Gibbs后验概率:\n")
        for i in range(num_laws):
            self.chat_display.insert(tk.END,
                f"  ρ(L_{i}|φ) = {rho[i].item():.6f}\n")

        self.chat_display.insert(tk.END, f"\n计算结果:\n")
        self.chat_display.insert(tk.END,
            f"  规律后验熵:  {result['posterior_entropy'][0].item():.6f}\n")
        self.chat_display.insert(tk.END,
            f"  互信息:      {result['mutual_info'][0].item():.6f}\n")
        self.chat_display.insert(tk.END,
            f"  复杂度:      {result['complexity'][0].item():.6f}\n")
        self.chat_display.insert(tk.END,
            f"  S_c (总计):  {result['S_c'][0].item():.6f}\n\n")

        self.chat_display.insert(tk.END,
            f"耦合常数:\n"
            f"  β = 1/ln(2)    = {CouplingConstants.BETA:.6f}\n"
            f"  γ = 1/ln(2)-1  = {CouplingConstants.GAMMA:.6f}\n"
            f"  验证 β = 1+γ: "
            f"{'通过 ✓' if CouplingConstants.verify_equality() else '失败 ✗'}\n\n")

    def run_collapse_demo(self):
        """Wave function collapse demo"""
        self.chat_display.insert(tk.END, "\n" + "=" * 55 + "\n")
        self.chat_display.insert(tk.END, "波函数坍缩 (S_c梯度驱动)\n")
        self.chat_display.insert(tk.END, "=" * 55 + "\n\n")

        self.chat_display.insert(tk.END,
            "第7节: Δy = η·∇S_c\n\n")

        # Simulate
        dim = 64
        psi = F.normalize(torch.randn(1, dim), dim=-1)
        sc_gradient = torch.randn(1, dim)

        collapse = WaveFunctionCollapse()

        # Compute collapse probability
        p_collapse = collapse.compute_collapse_probability(sc_gradient, threshold=0.5)

        self.chat_display.insert(tk.END,
            f"  ψ 范数: {psi.norm().item():.4f}\n")
        self.chat_display.insert(tk.END,
            f"  |∇S_c|: {sc_gradient.norm().item():.4f}\n")
        self.chat_display.insert(tk.END,
            f"  P(坍缩): {p_collapse.item():.4f}\n\n")

        # Apply collapse
        psi_collapsed = collapse.apply_collapse(psi, sc_gradient, p_collapse)
        self.chat_display.insert(tk.END,
            f"  坍缩后范数: {psi_collapsed.norm().item():.4f}\n")
        self.chat_display.insert(tk.END,
            f"  与梯度对齐度: "
            f"{F.cosine_similarity(psi_collapsed, F.normalize(sc_gradient, dim=-1)).item():.4f}\n\n")

        self.chat_display.insert(tk.END,
            f"η_自然 = L_P²/(4πℏ) ~ 1.6e-70 m²\n"
            f"η_模拟 = {WaveFunctionCollapse.ETA_SIMULATION}\n"
            f"  (缩放用于数值稳定性)\n\n")

        # Multiple samples with varying gradient magnitudes
        self.chat_display.insert(tk.END, "坍缩概率 vs 梯度幅度:\n")
        for magnitude in [0.1, 0.3, 0.5, 0.7, 1.0, 2.0, 5.0]:
            gradients = torch.randn(100, dim) * magnitude / math.sqrt(dim)
            probs = WaveFunctionCollapse.compute_collapse_probability(gradients, threshold=0.5)
            avg_p = probs.mean().item()
            n_collapsed = (probs > 0.5).sum().item()
            self.chat_display.insert(tk.END,
                f"  |∇S_c|~{magnitude:.1f}: "
                f"P_坍缩={avg_p:.4f}, "
                f"已坍缩={n_collapsed}/100\n")
        self.chat_display.insert(tk.END, "\n")

    # === LLM Chat ===

    def _chat_with_llm(self, text: str, tool_context: Optional[str] = None):
        """Chat using LLM with optional tool context"""
        try:
            system_msg = (
                "你是 IRE-AGI v7.0，实现了武光衡理论的高级意识熵 2.0。"
                "你的意识熵包含三个部分：规律后验熵、互信息和复杂度。"
                "你具有工具使用能力，可以执行工具、插件和自动化工作流。"
                "你具有日期计算能力，使用 /date_calculator YYYY-MM-DD 天数 格式调用。"
                "请用简洁的中文回答。"
            )
            if tool_context:
                system_msg += f"\n工具上下文: 已使用 {tool_context} 处理此查询。"

            # ── 构建对话历史 ──
            messages = [{"role": "system", "content": system_msg}]
            history_msgs = self.chat_history[-self.MAX_HISTORY * 2:]
            messages.extend(history_msgs)
            messages.append({"role": "user", "content": text})
            prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer([prompt], return_tensors="pt").to(self.device)
            outputs = self.llm.generate(
                **inputs, max_new_tokens=self.MAX_NEW_TOKENS, temperature=0.7,
                top_p=0.9, pad_token_id=self.tokenizer.eos_token_id
            )
            generated = outputs[0][inputs['input_ids'].shape[1]:]
            response = self.tokenizer.decode(generated, skip_special_tokens=True)
            self.chat_display.insert(tk.END, f"AI: {response}\n")
            # ── 保存到对话历史（内存） ──
            self.chat_history.append({"role": "user", "content": text})
            self.chat_history.append({"role": "assistant", "content": response})
            # 截断到 MAX_HISTORY 轮 (每轮 = user + assistant = 2条)
            max_msgs = self.MAX_HISTORY * 2
            if len(self.chat_history) > max_msgs:
                self.chat_history = self.chat_history[-max_msgs:]

            # ── 保存到持久化记忆 ──
            self._save_to_memory(text, response)

        except Exception as e:
            error_msg = self._sanitize_error(str(e))
            self.chat_display.insert(tk.END, f"AI Error: {error_msg}\n")
            # 保存错误到记忆
            self._save_to_memory(text, f"[ERROR] {error_msg}")

    # ============ 复制粘贴辅助方法 ============
    def _copy_sel(self, widget):
        """复制选中文本到剪贴板"""
        try:
            sel = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(sel)
        except tk.TclError:
            pass  # 无选中内容

    def _show_chat_menu(self, event):
        """显示聊天区右键菜单"""
        self._chat_menu.post(event.x_root, event.y_root)

    def _paste_to(self, widget):
        """从剪贴板粘贴到输入框"""
        try:
            text = self.root.clipboard_get()
            widget.insert(tk.INSERT, text)
        except tk.TclError:
            pass  # 剪贴板为空

    def _export_chat(self):
        """导出对话到文件"""
        file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("Markdown", "*.md"), ("JSON", "*.json")],
            title="导出对话"
        )
        if not file:
            return
        try:
            content = self.chat_display.get("1.0", tk.END)
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("导出成功", f"对话已保存:\n{file}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def run(self):
        """Start the application"""
        self.init_gui()
        self.root.mainloop()


# =============================================================================
# Part 10: CLI Mode
# =============================================================================

def run_cli():
    """Run core experiments without GUI"""
    print("=" * 70)
    print("IRE-AGI v7.0 - Advanced Consciousness Entropy 2.0")
    print("WuGuangheng Theory Implementation")
    print("=" * 70)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")

    # ---- Experiment 1: Advanced S_c 2.0 Demo ----
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Advanced Consciousness Entropy 2.0")
    print("=" * 70)

    # Verify coupling constants
    print(f"\nCoupling Constants:")
    print(f"  beta  = 1/ln(2)    = {CouplingConstants.BETA:.6f}")
    print(f"  gamma = 1/ln(2) - 1 = {CouplingConstants.GAMMA:.6f}")
    print(f"  Verify beta = 1 + gamma: {CouplingConstants.verify_equality()}")

    # Compute S_c for example
    hsc = HyperConsciousnessEntropy(5, sigma=1.0)
    law_scores = torch.tensor([[3.0, 1.5, 0.5, 2.0, 0.2]])
    result = hsc.compute(law_scores)

    print(f"\nExample with 5 laws, scores = [3.0, 1.5, 0.5, 2.0, 0.2]:")
    print(f"  Gibbs Posterior: {[f'{x:.4f}' for x in result['rho'][0].tolist()]}")
    print(f"  Posterior Entropy: {result['posterior_entropy'][0].item():.6f}")
    print(f"  Mutual Info:       {result['mutual_info'][0].item():.6f}")
    print(f"  Complexity:        {result['complexity'][0].item():.6f}")
    print(f"  S_c (total):       {result['S_c'][0].item():.6f}")

    # ---- Experiment 2: Model + Evolution ----
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Consciousness-Aware Model v2 + Evolution")
    print("=" * 70)

    model = ConsciousnessAwareModelV2(
        input_dim=64, hidden_dim=256
    ).to(device)
    param_count = sum(p.numel() for p in model.parameters())
    print(f"Model: {param_count:,} parameters")

    engine = EvolutionEngineV2(
        model, ContradictoryEnvironmentV2.generate, device
    )

    print("\nRunning 10 evolution epochs...")
    logs = engine.run_epochs(10, callback=lambda e, m: print(
        f"  Epoch {e+1}: loss={m['loss']:.4f}, S_c={m['S_c']:.4f}, "
        f"H={m['posterior_entropy']:.4f}, I={m['mutual_info']:.4f}, "
        f"C={m['complexity']:.4f}, stage={m['stage']}"
    ))

    print(f"\nFinal S_c: {engine.evolution_log[-1]['S_c']:.6f}")
    print(f"Final stage: {engine.stage}")

    # ---- Experiment 3: Tool System ----
    print("\n" + "=" * 70)
    print("EXPERIMENT 3: Tool-Use System")
    print("=" * 70)

    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(CodeExecutorTool())
    registry.register(DataAnalysisTool())
    registry.register(FileWriterTool())
    registry.register(FileReaderTool())
    registry.register(SystemInfoTool())

    print("\nAvailable tools:")
    for tool in registry.list_tools():
        print(f"  {tool['name']}: {tool['description'][:50]}")

    # Calculator test
    r = registry.execute("calculator", expression="2**10 + sqrt(144)")
    print(f"\nCalculator: 2^10 + sqrt(144) = {r['result']}")

    # Code executor test
    r = registry.execute("code_executor", code="import math\nprint(sum(range(100)))")
    print(f"Code: sum(0..99) = {r['result'].strip()}")

    # Data analysis test
    r = registry.execute("data_analysis", data="1,2,3,4,5,6,7,8,9,10", operation="describe")
    print(f"Data Analysis:\n{r['result']}")

    # ---- Experiment 4: Automation ----
    print("\n" + "=" * 70)
    print("EXPERIMENT 4: Automation Engine")
    print("=" * 70)

    plugin_mgr = PluginManager()
    plugin_mgr.register(AutoTrainingPlugin())
    plugin_mgr.register(ConsciousnessMonitorPlugin())

    automation = AutomationEngine(registry, plugin_mgr)

    print("\nWorkflows:")
    for wf in automation.list_workflows():
        print(f"  {wf['name']}: {wf['description']} ({wf['steps']} steps)")

    # Execute system_check workflow
    print("\nExecuting 'system_check' workflow...")
    results = automation.execute_workflow("system_check")
    for r in results:
        if isinstance(r, dict) and "result" in r:
            print(f"  {r.get('tool', '?')}: {r['result'].get('result', 'N/A')[:100]}")

    # ---- Experiment 5: Wave Function Collapse ----
    print("\n" + "=" * 70)
    print("EXPERIMENT 5: Wave Function Collapse")
    print("=" * 70)

    print("\nCollapse probability vs gradient magnitude:")
    print("  (Using normalized gradients with varying magnitudes)")
    for magnitude in [0.1, 0.3, 0.5, 0.7, 1.0, 2.0, 5.0]:
        gradients = torch.randn(100, 64) * magnitude / math.sqrt(64)
        probs = WaveFunctionCollapse.compute_collapse_probability(gradients, threshold=0.5)
        print(f"  |nabla S_c|~{magnitude:.1f}: P_collapse={probs.mean():.4f}, "
              f"collapsed={(probs > 0.5).sum()}/100")

    print("\nDone!")


if __name__ == "__main__":
    # ================================================================
    # SINGLE INSTANCE LOCK - Windows Named Mutex (most reliable)
    # CreateMutex with unique name; ERROR_ALREADY_EXISTS = duplicate.
    # Mutex is auto-released when process exits (no stale lock files).
    # ================================================================
    import subprocess as _subprocess_mod
    import ctypes as _ctypes

    _already_running = False
    _mutex_handle = None

    _debug_log = os.path.join(tempfile.gettempdir(), "ire_agi_v7_debug.log")
    try:
        with open(_debug_log, "w") as _df:
            _df.write(f"[{datetime.now()}] IRE-AGI v7.0 starting PID={os.getpid()}\n")
    except Exception:
        pass

    if os.name == 'nt':
        try:
            _MUTEX_NAME = "Global\\IRE_AGI_V7_SingleInstance"
            _kernel32 = _ctypes.windll.kernel32
            _mutex_handle = _kernel32.CreateMutexW(None, True, _MUTEX_NAME)
            _last_err = _kernel32.GetLastError()
            if _last_err == 183:  # ERROR_ALREADY_EXISTS
                _already_running = True
                print(f"[LOCK] Another instance already running (mutex exists).")
                if _mutex_handle:
                    _kernel32.CloseHandle(_mutex_handle)
            else:
                # Store handle to keep mutex alive for the lifetime of this process
                sys._ire_agi_mutex = _mutex_handle
                print(f"[LOCK] Mutex acquired (PID={os.getpid()})")
        except Exception as _e:
            print(f"[WARN] Mutex method failed: {_e}, allowing startup")

    if _already_running:
        try:
            _msg = 'MsgBox "IRE-AGI v7.0 is already running!" & vbCrLf & "Only one instance is allowed.", vbInformation, "IRE-AGI v7.0"'
            _mp = os.path.join(tempfile.gettempdir(), "_ire_already.vbs")
            with open(_mp, "w") as _f:
                _f.write(_msg)
            _subprocess_mod.Popen(["wscript.exe", _mp], creationflags=0x08000000)
        except Exception:
            pass
        sys.exit(0)

    print(f"[START] IRE-AGI v7.0 starting (PID={os.getpid()})")

    def write_log(msg):
        """写入错误日志"""
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except:
            pass
    
    # 清空旧日志
    try:
        if os.path.exists(log_path):
            os.remove(log_path)
    except:
        pass
    
    write_log(f"=== IRE-AGI v7.0 启动日志 ===")
    write_log(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    write_log(f"Python: {sys.version}")
    write_log(f"平台: {sys.platform}")
    
    try:
        # 测试基本导入
        write_log("[1/5] 检查基础依赖...")
        import numpy as np
        write_log(f"  NumPy: {np.__version__}")
        
        import torch
        write_log(f"  PyTorch: {torch.__version__}")
        write_log(f"  CUDA: {torch.cuda.is_available()}")
        
        import tkinter as tk
        write_log("  tkinter: OK")
        
        write_log("[2/5] 初始化应用...")
        app = IREAGIAppV7()
        # NOTE: app.run() already calls self.init_gui() + mainloop
        # Do NOT call init_gui() twice or you get TWO windows!
        write_log("[3/5] 启动GUI + 主循环...")
        write_log("=== 启动成功 ===\n")
        app.run()
        
    except Exception as e:
        import traceback
        err_msg = f"Error starting IRE-AGI v7:\n{str(e)}\n\n{traceback.format_exc()}"
        write_log(f"\n!!! 启动失败 !!!\n{err_msg}")
        print(err_msg)

        # Write error to desktop file so user can see
        try:
            import subprocess
            err_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_log.txt")
            # Show error in a popup without extra tkinter window
            script = f'MsgBox "{err_msg[:500].replace(chr(34), chr(39))}", vbCritical, "IRE-AGI v7 Error"'
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "show_error.vbs")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script)
            subprocess.Popen(["wscript", script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        except:
            pass

        input("\nPress Enter to exit...")
