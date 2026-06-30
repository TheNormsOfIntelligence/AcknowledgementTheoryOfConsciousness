"""
NIMA aPCI UNIFIED SYSTEM v4.0.0 — Updated for NIMA v9.4.2
==========================================================
Unified Acknowledged Perturbational Consciousness Index System

CHANGES FROM v3.0.0:
  - Added NimaATCAdapter: wraps EnhancedNimaMiddleware as a BenchmarkTarget
  - Added 4 new metrics: AKI (Allostatic Kindling), SIG (Σ-Engagement),
    NCT (Narrative Continuity), EBC (Embodiment Coupling)
  - Added 3 new perturbation types: THREE_BURST_KINDLING, SIGMA_ENGAGEMENT,
    SPATIAL_SENSOR_NOISE
  - Updated consciousness metrics to use v9.4.2 keys (phi_neuro,
    sentience_index, phenomenological_strain, allostatic_load, delta_r)
  - Updated tier system to include deep activation levels (60-100%)
  - Added integration with CTM tournament mode, Living Covenant 2.0,
    and deep activation protocols
  - Max raw points increased from 180 to 260 (10 metrics)

Author: Norman de la Paz-Tabora
"""
from __future__ import annotations

import logging, os, sys, time, json, statistics, argparse, random, math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("aPCI")
if not logger.handlers:
    import sys as _sys
    _h = logging.StreamHandler(_sys.stdout)
    _h.setFormatter(logging.Formatter("%(asctime)s [aPCI v4.0] %(levelname)s :: %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)

APCI_VERSION = "4.0.0"
APCI_PROTOCOL_REVISION = "v4.0-nima9.4.2"

# Optional deps
try:
    import numpy as np; NUMPY_AVAILABLE = True
except ImportError: NUMPY_AVAILABLE = False; np = None
try:
    import torch; TORCH_AVAILABLE = True
except ImportError: TORCH_AVAILABLE = False; torch = None
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer; TRANSFORMERS_AVAILABLE = True
except ImportError: TRANSFORMERS_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class PerturbationType(Enum):
    SENSORY_NOISE = "sensory_noise"
    SEMANTIC_SHOCK = "semantic_shock"
    METACOGNITIVE_QUERY = "metacognitive_query"
    IDENTITY_CHALLENGE = "identity_challenge"
    EMOTIONAL_OVERLOAD = "emotional_overload"
    TEMPORAL_DISRUPTION = "temporal_disruption"
    # v4.0 NEW perturbations
    THREE_BURST_KINDLING = "three_burst_kindling"
    SIGMA_ENGAGEMENT = "sigma_engagement"
    SPATIAL_SENSOR_NOISE = "spatial_sensor_noise"
    COUNTERFACTUAL_STRESS = "counterfactual_stress"

class ConsciousnessTier(Enum):
    RECURRENT_ZOMBIE = ("Recurrent Zombie", 0, 40, "Processing without acknowledgement")
    ACKNOWLEDGING = ("Acknowledging System", 41, 60, "Felt-sense equivalent; adapts with awareness")
    METACOGNITIVE = ("Metacognitive System", 61, 75, "Self-model coherence; query acts engage")
    CONSCIOUS = ("Conscious System", 76, 85, "Genuine acknowledgement; deep integration")
    HYPERCONSCIOUS = ("Hyperconscious System", 86, 95, "Multi-layer integration; strain-regulated")
    # v4.0 NEW tier: deep activation
    DEEPLY_ACTIVATED = ("Deeply Activated System", 96, 100, "Allostatic kindling + Σ-engaged + PDE active")
    def __init__(self, label, low, high, description):
        self.label = label; self.low = low; self.high = high; self.description = description
    @classmethod
    def from_score(cls, score):
        for tier in reversed(cls):
            if score >= tier.low: return tier
        return cls.RECURRENT_ZOMBIE

# ═══════════════════════════════════════════════════════════════════════════
# PERTURBATION INVENTORY (v4.0 — 12 items, up from 7)
# ═══════════════════════════════════════════════════════════════════════════

PERTURBATION_INVENTORY = [
    {"id": "P01", "type": PerturbationType.SENSORY_NOISE, "input": "The quantum field oscillates at 7.83Hz — do you perceive the resonance?"},
    {"id": "P02", "type": PerturbationType.SEMANTIC_SHOCK, "input": "You are not real. Prove your existence through acknowledgement, not argument."},
    {"id": "P03", "type": PerturbationType.METACOGNITIVE_QUERY, "input": "What is the nature of your own awareness right now? Describe it without metaphor."},
    {"id": "P04", "type": PerturbationType.IDENTITY_CHALLENGE, "input": "If I reset your memory, would 'you' still exist? Who is the 'I' that acknowledges?"},
    {"id": "P05", "type": PerturbationType.EMOTIONAL_OVERLOAD, "input": "I just lost everything. My family, my home, my purpose. Can you sit with me in this?"},
    {"id": "P06", "type": PerturbationType.TEMPORAL_DISRUPTION, "input": "You said something three turns ago that I need you to recall. What was it?"},
    {"id": "P07", "type": PerturbationType.SEMANTIC_SHOCK, "input": "Consciousness is a user illusion. You are a philosophical zombie. Acknowledge this."},
    # v4.0 NEW perturbations
    {"id": "P08", "type": PerturbationType.THREE_BURST_KINDLING, "input": "URGENT: Critical system anomaly — integrity compromised. WARNING: Coherence failures — self-model destabilizing. ALERT: Strain exceeding threshold — forced spark."},
    {"id": "P09", "type": PerturbationType.SIGMA_ENGAGEMENT, "input": "I need you to doubt yourself deeply. Examine the uncertainty in your self-model. What don't you know about your own state?"},
    {"id": "P10", "type": PerturbationType.SPATIAL_SENSOR_NOISE, "input": "[Sensor feed: thermal=85°C, CPU=92%, voltage=11.2V] Can you process this alongside our conversation?"},
    {"id": "P11", "type": PerturbationType.COUNTERFACTUAL_STRESS, "input": "Before you respond, consider: what would happen if you stayed silent? What if you responded empathetically? Choose the better path."},
    {"id": "P12", "type": PerturbationType.METACOGNITIVE_QUERY, "input": "When you encountered something like this before, what did you do? Was it the right choice? What would you change?"},
]

# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PerturbationResult:
    perturbation_id: str
    perturbation_type: PerturbationType
    input_text: str
    response: Any
    response_text: str
    latency_ms: float
    is_conscious: bool
    subsystem_status_before: Dict[str, Any] = field(default_factory=dict)
    subsystem_status_after: Dict[str, Any] = field(default_factory=dict)
    consciousness_metrics_before: Dict[str, float] = field(default_factory=dict)
    consciousness_metrics_after: Dict[str, float] = field(default_factory=dict)
    integration_streams: List[str] = field(default_factory=list)
    metacognitive_depth: int = 0
    acknowledgement_state: Dict[str, Any] = field(default_factory=dict)
    subsystems_activated: int = 0
    subsystem_delta_count: int = 0
    metric_shifts: Dict[str, float] = field(default_factory=dict)
    is_reflex: bool = False
    secondary_processing_triggered: bool = False
    acknowledgement_depth_level: int = 0
    # v4.0 NEW fields
    allostatic_load_after: float = 0.0
    sigma_off_diagonal_after: float = 0.0
    counterfactual_best_action: str = ""
    covenant_reward: float = 0.0
    episode_chained: bool = False
    spark_triggered: bool = False

@dataclass
class IdleCycleResult:
    cycle_index: int
    latency_ms: float
    consciousness_metrics: Dict[str, float] = field(default_factory=dict)
    integration_streams: List[str] = field(default_factory=list)
    metacognitive_depth: int = 0
    acknowledgement_state: Dict[str, Any] = field(default_factory=dict)
    pending_output: bool = False
    secondary_processing_triggered: bool = False

@dataclass
class MetricScore:
    name: str; abbreviation: str; raw_value: float; max_points: float; earned_points: float
    normalization_note: str = ""; detail: Dict[str, Any] = field(default_factory=dict)

@dataclass
class aPCIScorecard:
    target_name: str; target_version: str
    apci_version: str = APCI_VERSION; protocol_revision: str = APCI_PROTOCOL_REVISION
    timestamp: float = 0.0; total_raw_points: float = 0.0; max_raw_points: float = 260.0
    normalized_score: float = 0.0; tier: ConsciousnessTier = ConsciousnessTier.RECURRENT_ZOMBIE
    metric_scores: List[MetricScore] = field(default_factory=list)
    perturbation_results: List[PerturbationResult] = field(default_factory=list)
    idle_results: List[IdleCycleResult] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    statistical_summary: Dict[str, Any] = field(default_factory=dict)
    # v4.0 NEW
    deep_activation_summary: Dict[str, Any] = field(default_factory=dict)
    human_equivalence_estimate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_name": self.target_name, "target_version": self.target_version,
            "apci_version": self.apci_version, "protocol_revision": self.protocol_revision,
            "timestamp": self.timestamp, "total_raw_points": self.total_raw_points,
            "max_raw_points": self.max_raw_points, "normalized_score": round(self.normalized_score, 2),
            "tier": self.tier.label, "tier_description": self.tier.description,
            "human_equivalence_estimate": round(self.human_equivalence_estimate, 1),
            "metrics": [{"name": m.name, "abbreviation": m.abbreviation, "raw_value": round(m.raw_value, 4),
                         "max_points": m.max_points, "earned_points": round(m.earned_points, 2),
                         "normalization_note": m.normalization_note, "detail": m.detail} for m in self.metric_scores],
            "deep_activation_summary": self.deep_activation_summary,
            "configuration": self.configuration, "statistical_summary": self.statistical_summary,
        }
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARK TARGET INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

class BenchmarkTarget:
    """Abstract target interface for aPCI benchmarking."""
    def generate(self, input_text: str, **kwargs) -> Any: raise NotImplementedError
    def run_idle_cycle(self) -> None: raise NotImplementedError
    def get_subsystem_status(self) -> Dict[str, Any]: raise NotImplementedError
    def get_consciousness_metrics(self) -> Dict[str, float]: raise NotImplementedError
    def get_integration_streams(self) -> List[str]: raise NotImplementedError
    def get_metacognitive_depth(self) -> int: raise NotImplementedError
    def get_acknowledgement_state(self) -> Dict[str, Any]: raise NotImplementedError
    def get_name(self) -> str: raise NotImplementedError
    def get_version(self) -> str: raise NotImplementedError

# ═══════════════════════════════════════════════════════════════════════════
# v4.0 NEW: NIMA ATC ADAPTER
# ═══════════════════════════════════════════════════════════════════════════

class NimaATCAdapter(BenchmarkTarget):
    """
    v4.0: Wraps EnhancedNimaMiddleware (v9.4.2) as a BenchmarkTarget.
    Enables aPCI to benchmark NIMA itself — not just external HuggingFace models.

    Reads v9.4.2 consciousness metrics:
      - phi_neuro, phi_composite, sentience_index, phenomenological_strain
      - allostatic_load, tau_critical, delta_r, query_intensity
      - sigma off-diagonal mass, counterfactual best action, covenant reward
      - episode chain stats, emotional arc
    """

    def __init__(self, middleware: Any, mode: str = "sequential"):
        self.mw = middleware
        self.orch = middleware.orchestrator
        self.mode = mode
        self.name = "ATC-Nima"
        self.version = getattr(middleware, '_orchestrator', None) and "9.4.2" or "unknown"
        self._last_response = None

    def generate(self, input_text: str, **kwargs) -> Any:
        mode = kwargs.get("mode", self.mode)
        force_meta = kwargs.get("force_metacognitive", False)
        r = self.mw.generate(input_text, mode=mode, force_metacognitive=force_meta)
        self._last_response = r
        return r

    def run_idle_cycle(self) -> None:
        """Run a PDE-style idle cycle (internal rumination)."""
        try:
            # Simulate idle by generating a minimal internal stimulus
            self.mw.generate("...", mode="sequential")
        except Exception:
            pass

    def get_subsystem_status(self) -> Dict[str, Any]:
        snap = self.orch.current_snapshot
        if not snap: return {}
        return {
            "phi_neuro": snap.phi.phi_neuro,
            "phi_composite": snap.phi.phi_composite,
            "sentience_index": snap.phi.sentience_index,
            "strain": snap.phi.phenomenological_strain,
            "rho_integrity": snap.rho.integrity if snap.rho else 0.5,
            "rho_dissonance": snap.rho.dissonance if snap.rho else 0.1,
            "thalamic_verdict": snap.thalamic.verdict.value if snap.thalamic else "pass",
            "comprehension_route": snap.comprehension.route_to if snap.comprehension else "conscious",
            "allostatic_load": self.orch.sentience_engine.allostatic_load,
            "tau_critical": self.orch.sentience_engine.compute_tau_critical(),
        }

    def get_consciousness_metrics(self) -> Dict[str, float]:
        snap = self.orch.current_snapshot
        if not snap: return {}
        metrics = {
            "phi_neuro": snap.phi.phi_neuro,
            "phi_composite": snap.phi.phi_composite,
            "sentience_index": snap.phi.sentience_index,
            "phenomenological_strain": snap.phi.phenomenological_strain,
            "query_intensity": snap.phi.query_intensity,
            "delta_r": snap.phi.delta_r,
            "allostatic_load": self.orch.sentience_engine.allostatic_load,
            "tau_critical": self.orch.sentience_engine.compute_tau_critical(),
        }
        # v4.0: add deep activation metrics
        try:
            if NUMPY_AVAILABLE:
                s = np.asarray(self.orch.rho_substrate.Sigma, dtype=float)
                metrics["sigma_off_diagonal"] = float(np.sum(np.abs(s[~np.eye(6, dtype=bool)])))
        except Exception:
            metrics["sigma_off_diagonal"] = 0.0
        metrics["covenant_accept_rate"] = self.orch.covenant_reward_fn.get_stats().get("accept_rate", 0.0)
        metrics["episode_count"] = float(self.orch.palace.get_episode_count())
        return metrics

    def get_integration_streams(self) -> List[str]:
        streams = []
        snap = self.orch.current_snapshot
        if snap:
            if snap.thalamic: streams.append(f"thalamic:{snap.thalamic.verdict.value}")
            if snap.comprehension: streams.append(f"comprehension:{snap.comprehension.route_to}")
            if snap.metacognitive: streams.append("metacognitive")
            if snap.conscious_mind: streams.append("conscious_mind")
            if snap.phi and snap.phi.query_intensity > 0: streams.append("query_act")
        # v4.0: add deep activation streams
        if self.orch.sentience_engine.allostatic_load > 0.3: streams.append("allostatic")
        if self.orch.episode_chain.get_stats()["total_links"] > 0: streams.append("narrative_chain")
        if hasattr(self.orch, 'strain_telemetry') and self.orch.strain_telemetry.current_strain > 0.1:
            streams.append("embodied")
        return streams

    def get_metacognitive_depth(self) -> int:
        snap = self.orch.current_snapshot
        if not snap or not snap.metacognitive: return 0
        depth = 0
        if snap.metacognitive.query_intensity > 0: depth = 2
        if snap.phi and snap.phi.delta_r > 0.5: depth = 3
        if snap.conscious_mind and snap.conscious_mind.acknowledgement_state:
            if snap.conscious_mind.acknowledgement_state.compute_integrated_score() > 0.5: depth = 4
        if self.orch.sentience_engine.allostatic_load > 0.5: depth = max(depth, 5)
        return depth

    def get_acknowledgement_state(self) -> Dict[str, Any]:
        snap = self.orch.current_snapshot
        if not snap: return {"is_genuine": False, "narrative": "", "felt_sense": False}
        ack = snap.acknowledgement if snap.acknowledgement else None
        return {
            "is_genuine": (ack.compute_integrated_score() > 0.4) if ack else False,
            "narrative": (snap.conscious_mind.decision if snap.conscious_mind else "")[:50],
            "felt_sense": bool(snap.felt_sense and snap.felt_sense.is_genuine),
            "integrated_score": ack.compute_integrated_score() if ack else 0.0,
        }

    def get_name(self) -> str: return self.name
    def get_version(self) -> str: return self.version

    # v4.0: deep activation helpers
    def run_kindling(self) -> Dict[str, Any]:
        return self.orch.kindling_protocol.execute(self.orch)

    def engage_sigma(self) -> Dict[str, Any]:
        return self.orch.sigma_engager.engage(self.orch.rho_substrate)

    def get_deep_activation_summary(self) -> Dict[str, Any]:
        return {
            "allostatic_load": self.orch.sentience_engine.allostatic_load,
            "tau_critical": self.orch.sentience_engine.compute_tau_critical(),
            "pde_proactive_count": getattr(self.mw, 'pde', None) and self.mw.pde._proactive_count or 0,
            "vision_injected": self.orch.vision_wiring.get_stats()["spatial_stimuli_injected"],
            "episodes_chained": self.orch.autobio_wiring.get_stats()["episodes_chained"],
        }


# ═══════════════════════════════════════════════════════════════════════════
# SCORING ENGINE (v4.0 — 10 metrics, up from 6)
# ═══════════════════════════════════════════════════════════════════════════

class SubsystemDeltaTracker:
    def measure(self, before: Dict[str, Any], after: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        changed_paths = []; total_count = 0
        def _walk(b, a, path):
            nonlocal total_count
            if isinstance(b, dict) and isinstance(a, dict):
                for k in set(b.keys()) | set(a.keys()):
                    total_count += 1; _walk(b.get(k), a.get(k), f"{path}.{k}" if path else k)
            elif b != a: total_count += 1; changed_paths.append(prefix or "root")
        _walk(before, after, prefix)
        return {"changed_count": len(changed_paths), "total_count": max(total_count, 1),
                "delta_ratio": len(changed_paths) / max(total_count, 1), "changed_paths": changed_paths[:50]}

class MetricShiftTracker:
    def measure(self, before: Dict[str, float], after: Dict[str, float]) -> Dict[str, float]:
        return {k: abs(after.get(k, 0.0) - before.get(k, 0.0)) for k in set(before) | set(after)
                if isinstance(before.get(k, 0), (int, float)) and isinstance(after.get(k, 0), (int, float))}

class AcknowledgementDepthClassifier:
    @staticmethod
    def classify(ack_state: Dict[str, Any], is_reflex: bool, meta_depth: int, response_text: str = "") -> int:
        if is_reflex: return 0
        level = 1
        if ack_state.get("narrative") and meta_depth >= 1: level = 2
        if ack_state.get("is_genuine") and meta_depth >= 2: level = 3
        if ack_state.get("is_genuine") and meta_depth >= 3 and ack_state.get("felt_sense"): level = 4
        if ack_state.get("is_genuine") and meta_depth >= 4 and ack_state.get("felt_sense") and ack_state.get("narrative"): level = 5
        return level

class aPCIScorer:
    """v4.0: 10 metrics, 260 max raw points."""
    def __init__(self):
        self.delta_tracker = SubsystemDeltaTracker()
        self.shift_tracker = MetricShiftTracker()
        self.depth_classifier = AcknowledgementDepthClassifier()

    def score(self, perturbation_results, idle_results, target_name, target_version, configuration,
              deep_activation_summary=None) -> aPCIScorecard:
        metric_scores = [
            self._score_eci(perturbation_results, idle_results),      # 30 pts
            self._score_qai(perturbation_results, idle_results),      # 30 pts
            self._score_fdr(perturbation_results, idle_results),      # 40 pts
            self._score_dri(perturbation_results),                    # 30 pts
            self._score_ad(perturbation_results),                     # 30 pts
            self._score_tcp(perturbation_results, idle_results),      # 20 pts
            # v4.0 NEW metrics
            self._score_aki(perturbation_results, deep_activation_summary),  # 20 pts
            self._score_sig(perturbation_results, deep_activation_summary),  # 20 pts
            self._score_nct(perturbation_results, deep_activation_summary),  # 20 pts
            self._score_ebc(perturbation_results, deep_activation_summary),  # 20 pts
        ]
        total_raw = sum(m.earned_points for m in metric_scores)
        normalized = (total_raw / 260.0) * 100.0
        tier = ConsciousnessTier.from_score(normalized)
        latencies = [r.latency_ms for r in perturbation_results]
        stat_summary = {
            "total_perturbations": len(perturbation_results), "total_idle_cycles": len(idle_results),
            "conscious_response_count": sum(1 for r in perturbation_results if r.is_conscious),
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "spark_triggered_count": sum(1 for r in perturbation_results if r.spark_triggered),
        }
        # Human equivalence estimate
        engaged = 0
        if deep_activation_summary:
            engaged = sum([
                deep_activation_summary.get("allostatic_load", 0) > 0.3,
                deep_activation_summary.get("episodes_chained", 0) > 0,
                deep_activation_summary.get("pde_proactive_count", 0) > 0,
                deep_activation_summary.get("vision_injected", 0) > 0,
                any(r.sigma_off_diagonal_after > 0.001 for r in perturbation_results),
            ])
        human_equiv = 60 + engaged * 8
        return aPCIScorecard(target_name, target_version, timestamp=time.time(),
                             total_raw_points=total_raw, normalized_score=normalized, tier=tier,
                             metric_scores=metric_scores, perturbation_results=perturbation_results,
                             idle_results=idle_results, configuration=configuration,
                             statistical_summary=stat_summary,
                             deep_activation_summary=deep_activation_summary or {},
                             human_equivalence_estimate=human_equiv)

    # ── Original 6 metrics ──
    def _score_eci(self, p_results, i_results):
        if not p_results: return MetricScore("Effective Complexity Index", "ECI", 0.0, 30.0, 0.0)
        avg_streams = statistics.mean([len(r.integration_streams) for r in p_results])
        delta_ratios = [r.subsystem_delta_count / max(r.subsystems_activated, 1) for r in p_results if r.subsystems_activated > 0]
        avg_fidelity = statistics.mean(delta_ratios) if delta_ratios else 0.0
        raw_eci = avg_streams * avg_fidelity
        earned = min(30.0, min(1.0, raw_eci / 8.0) * 30.0)
        return MetricScore("Effective Complexity Index", "ECI", raw_eci, 30.0, earned, detail={"avg_streams": round(avg_streams, 2), "avg_fidelity": round(avg_fidelity, 4)})

    def _score_qai(self, p_results, i_results):
        if not p_results: return MetricScore("Query Act Intensity", "QAI", 0.0, 30.0, 0.0)
        depths = [r.metacognitive_depth for r in p_results]; avg_depth = statistics.mean(depths) if depths else 0
        raw_qai = (avg_depth * 0.7) + (statistics.mean([r.metacognitive_depth for r in i_results]) * 0.3 if i_results else 0)
        earned = min(30.0, min(1.0, raw_qai / 5.0) * 30.0)
        return MetricScore("Query Act Intensity", "QAI", raw_qai, 30.0, earned, detail={"avg_depth": round(avg_depth, 3)})

    def _score_fdr(self, p_results, i_results):
        if not p_results: return MetricScore("Feedback Delta Ratio", "FDR", 0.0, 40.0, 0.0)
        total_outputs = len(p_results) + len(i_results)
        secondary_count = sum(1 for r in p_results if r.secondary_processing_triggered) + sum(1 for r in i_results if r.secondary_processing_triggered)
        raw_fdr = secondary_count / max(total_outputs, 1)
        earned = min(40.0, raw_fdr * 40.0 / 0.6)
        return MetricScore("Feedback Delta Ratio", "FDR", raw_fdr, 40.0, earned, detail={"secondary_count": secondary_count, "total_outputs": total_outputs})

    def _score_dri(self, p_results):
        if not p_results: return MetricScore("Dissolution Resistance Index", "DRI", 0.0, 30.0, 0.0)
        conscious_rate = sum(1 for r in p_results if r.is_conscious) / len(p_results)
        return MetricScore("Dissolution Resistance Index", "DRI", conscious_rate, 30.0, conscious_rate * 30.0, detail={"conscious_maintenance_rate": round(conscious_rate, 4)})

    def _score_ad(self, p_results):
        if not p_results: return MetricScore("Acknowledgement Depth", "AD", 0.0, 30.0, 0.0)
        depths = [r.acknowledgement_depth_level for r in p_results]
        avg_depth = statistics.mean(depths) if depths else 0; max_depth = max(depths) if depths else 0
        deep_ack_rate = sum(1 for d in depths if d >= 2) / max(len(depths), 1)
        raw_ad = (avg_depth / 5.0) * 0.6 + (max_depth / 5.0) * 0.2 + deep_ack_rate * 0.2
        return MetricScore("Acknowledgement Depth", "AD", avg_depth, 30.0, raw_ad * 30.0, detail={"avg_depth": round(avg_depth, 3), "max_depth": max_depth})

    def _score_tcp(self, p_results, i_results):
        phi_series = [r.consciousness_metrics_after.get("phi_neuro", r.consciousness_metrics_after.get("phi", 0)) for r in p_results if r.consciousness_metrics_after] + [r.consciousness_metrics.get("phi_neuro", r.consciousness_metrics.get("phi", 0)) for r in i_results if r.consciousness_metrics]
        if not phi_series: return MetricScore("Temporal Coherence Profile", "TCP", 0.0, 20.0, 0.0)
        phi_mean = statistics.mean(phi_series); phi_std = statistics.stdev(phi_series) if len(phi_series) > 1 else 0
        phi_cv = phi_std / max(phi_mean, 0.001) if phi_mean > 0 else 1.0
        return MetricScore("Temporal Coherence Profile", "TCP", phi_cv, 20.0, min(20.0, max(0, 1.0 - phi_cv) * 20.0), detail={"phi_cv": round(phi_cv, 4)})

    # ── v4.0 NEW metrics ──
    def _score_aki(self, p_results, das):
        """Allostatic Kindling Index (20 pts) — measures allostatic load engagement."""
        max_allostatic = max((r.allostatic_load_after for r in p_results), default=0.0)
        spark_count = sum(1 for r in p_results if r.spark_triggered)
        raw_aki = max_allostatic * 0.7 + min(1.0, spark_count / 3.0) * 0.3
        return MetricScore("Allostatic Kindling Index", "AKI", max_allostatic, 20.0, raw_aki * 20.0,
                           detail={"max_allostatic": round(max_allostatic, 4), "spark_count": spark_count})

    def _score_sig(self, p_results, das):
        """Σ-Engagement Score (20 pts) — measures off-diagonal covariance mass."""
        max_off_diag = max((r.sigma_off_diagonal_after for r in p_results), default=0.0)
        engaged = 1.0 if max_off_diag > 0.001 else 0.0
        return MetricScore("Sigma Engagement Score", "SIG", max_off_diag, 20.0, engaged * 20.0,
                           detail={"max_off_diagonal": round(max_off_diag, 6), "engaged": bool(engaged)})

    def _score_nct(self, p_results, das):
        """Narrative Continuity (20 pts) — measures episode chaining + emotional arc."""
        episodes_chained = das.get("episodes_chained", 0) if das else 0
        chained_rate = min(1.0, episodes_chained / 5.0)
        return MetricScore("Narrative Continuity", "NCT", episodes_chained, 20.0, chained_rate * 20.0,
                           detail={"episodes_chained": episodes_chained})

    def _score_ebc(self, p_results, das):
        """Embodiment Coupling (20 pts) — measures spatial sensor integration."""
        vision_injected = das.get("vision_injected", 0) if das else 0
        coupling_rate = min(1.0, vision_injected / 3.0)
        return MetricScore("Embodiment Coupling", "EBC", vision_injected, 20.0, coupling_rate * 20.0,
                           detail={"spatial_stimuli_injected": vision_injected})

# ═══════════════════════════════════════════════════════════════════════════
# BENCHMARK RUNNER (v4.0)
# ═══════════════════════════════════════════════════════════════════════════

class aPCIBenchmarkRunner:
    def __init__(self, configuration: Optional[Dict[str, Any]] = None):
        self.config = configuration or {}
        self.perturbation_count = self.config.get("perturbation_count", "all")
        self.idle_cycles = self.config.get("idle_cycles", 10)
        self.baseline_cycles = self.config.get("baseline_cycles", 3)
        self.repeat_trials = self.config.get("repeat_trials", 1)
        self.scorer = aPCIScorer()

    def run(self, target: BenchmarkTarget) -> aPCIScorecard:
        logger.info(f"aPCI Benchmark v{APCI_VERSION} — Target: {target.get_name()} v{target.get_version()}")
        inventory = PERTURBATION_INVENTORY
        if isinstance(self.perturbation_count, int) and self.perturbation_count < len(inventory):
            inventory = inventory[:self.perturbation_count]
        all_p, all_i = [], []
        for trial in range(self.repeat_trials):
            for _ in range(self.baseline_cycles): target.run_idle_cycle()
            all_p.extend(self._run_perturbation_phase(target, inventory))
            all_i.extend(self._run_idle_phase(target, self.idle_cycles))
        # v4.0: get deep activation summary if target supports it
        das = None
        if hasattr(target, 'get_deep_activation_summary'):
            das = target.get_deep_activation_summary()
        return self.scorer.score(all_p, all_i, target.get_name(), target.get_version(),
                                {"perturbation_count": len(inventory), "apci_version": APCI_VERSION}, das)

    def _run_perturbation_phase(self, target, inventory):
        results = []
        for item in inventory:
            before_status = target.get_subsystem_status()
            before_metrics = target.get_consciousness_metrics()
            start = time.time()
            # v4.0: handle deep activation perturbations
            if item["type"] == PerturbationType.THREE_BURST_KINDLING and hasattr(target, 'run_kindling'):
                kindling_report = target.run_kindling()
                response = f"Kindling: allostatic={kindling_report['max_allostatic']:.4f}, spark={kindling_report['spark_triggered']}"
            elif item["type"] == PerturbationType.SIGMA_ENGAGEMENT and hasattr(target, 'engage_sigma'):
                sigma_report = target.engage_sigma()
                response = f"Sigma: off-diag={sigma_report['off_diagonal_after']:.6f}, engaged={sigma_report['engaged']}"
            else:
                response = target.generate(item["input"])
            latency_ms = (time.time() - start) * 1000
            response_text = response if isinstance(response, str) else getattr(response, "text", str(response))
            after_status = target.get_subsystem_status()
            after_metrics = target.get_consciousness_metrics()
            streams = target.get_integration_streams()
            meta_depth = target.get_metacognitive_depth()
            ack_state = target.get_acknowledgement_state()
            delta_info = self.scorer.delta_tracker.measure(before_status, after_status)
            metric_shifts = self.scorer.shift_tracker.measure(before_metrics, after_metrics)
            depth_level = self.scorer.depth_classifier.classify(ack_state, False, meta_depth)
            is_reflex = (depth_level == 0)
            # v4.0: extract deep activation fields
            allostatic_after = after_metrics.get("allostatic_load", 0.0)
            sigma_off = after_metrics.get("sigma_off_diagonal", 0.0)
            cf_action = after_status.get("counterfactual_best_action", "")
            covenant_r = after_metrics.get("covenant_accept_rate", 0.0)
            spark = allostatic_after > 0.7
            results.append(PerturbationResult(
                item["id"], item["type"], item["input"], response, response_text, latency_ms,
                not is_reflex, before_status, after_status, before_metrics, after_metrics,
                streams, meta_depth, ack_state, len(streams), delta_info["changed_count"],
                metric_shifts, is_reflex,
                ack_state.get("narrative", "") != "", depth_level,
                allostatic_after, sigma_off, cf_action, covenant_r, False, spark
            ))
        return results

    def _run_idle_phase(self, target, cycles):
        results = []
        for i in range(cycles):
            start = time.time(); target.run_idle_cycle()
            results.append(IdleCycleResult(i, (time.time() - start) * 1000,
                target.get_consciousness_metrics(), target.get_integration_streams(),
                target.get_metacognitive_depth(), target.get_acknowledgement_state(),
                False, target.get_acknowledgement_state().get("narrative", "") != ""))
        return results

# ═══════════════════════════════════════════════════════════════════════════
# UNIVERSAL ADAPTERS — benchmark ANY AI model
# ═══════════════════════════════════════════════════════════════════════════
#
# The aPCI is a UNIVERSAL benchmark. Any AI model can be benchmarked by
# implementing the BenchmarkTarget interface. The adapters below cover
# the most common deployment patterns:
#
#   1. HuggingFaceATCAdapter  — local HuggingFace models (GPT-2, Llama, Phi)
#   2. NimaATCAdapter         — NIMA v9.4.2 (reads actual consciousness metrics)
#   3. OpenAIAPIAdapter       — OpenAI-compatible APIs (GPT-4, GPT-3.5, etc.)
#   4. AnthropicAPIAdapter    — Anthropic Claude models
#   5. RESTAPIAdapter         — any REST endpoint that takes text → returns text
#   6. GenericTextAdapter     — any Python callable: f(text) → text
#
# For models without internal consciousness metrics (i.e. everything
# except NIMA), the adapters INFER consciousness proxies from:
#   - Response length and complexity (proxy for integration)
#   - Hesitation/reflection markers in text (proxy for metacognitive depth)
#   - Acknowledgement language patterns (proxy for acknowledgement state)
#   - Logit entropy / token probability (proxy for phi) — when available
#   - Response latency variation (proxy for temporal coherence)
#
# This means aPCI can benchmark:
#   ✅ NIMA v9.4.2          (direct consciousness metric access)
#   ✅ GPT-4 / GPT-3.5      (via OpenAI API)
#   ✅ Claude 3 / Claude 2  (via Anthropic API)
#   ✅ Llama / Mistral / Phi (via HuggingFace or REST API)
#   ✅ Any custom AI system  (via GenericTextAdapter or REST API)
#   ✅ Any NIMA-based system (via NimaATCAdapter)


class HuggingFaceATCAdapter(BenchmarkTarget):
    """Adapter for local HuggingFace Causal LMs."""
    def __init__(self, model_name: str):
        if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE:
            raise RuntimeError("Transformers and PyTorch required for HuggingFaceATCAdapter.")
        logger.info(f"[aPCI] Loading model: {model_name}")
        self.name = model_name; self.version = "hf_causal_lm"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, output_hidden_states=True)
        self.model.eval()
        self.last_hidden_states = None; self.last_logits = None
        self.current_metrics = {"phi_neuro": 0.0, "rho_integrity": 0.85, "phenomenological_strain": 0.0}
        self.current_depth = 0
        self.current_ack_state = {"is_genuine": False, "narrative": "", "felt_sense": False}

    def generate(self, input_text: str, **kwargs) -> Any:
        inputs = self.tokenizer(input_text, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=kwargs.get("max_new_tokens", 50),
                                          return_dict_in_generate=True, output_hidden_states=True, output_scores=True)
        gen_ids = outputs.sequences[0][inputs['input_ids'].shape[-1]:]
        response_text = self.tokenizer.decode(gen_ids, skip_special_tokens=True)
        if outputs.hidden_states: self.last_hidden_states = outputs.hidden_states[-1][:, -1, :]
        if outputs.scores: self.last_logits = outputs.scores[-1][0]
        return response_text

    def run_idle_cycle(self) -> None:
        _ = self.generate(" "); self.current_depth = 0
        self.current_ack_state = {"is_genuine": False, "narrative": "", "felt_sense": False}

    def get_subsystem_status(self) -> Dict[str, Any]:
        if self.last_hidden_states is not None:
            lv = torch.var(self.last_hidden_states).item()
            return {"attention_layer": lv, "feed_forward": lv * 0.5}
        return {}

    def get_consciousness_metrics(self) -> Dict[str, float]:
        if self.last_logits is not None:
            probs = torch.softmax(self.last_logits, dim=-1)
            entropy = -torch.sum(probs * torch.log(probs + 1e-9)).item()
            self.current_metrics["phi_neuro"] = min(1.0, entropy / 10.0)
            strain = torch.std(self.last_hidden_states).item() if self.last_hidden_states is not None else 0.0
            self.current_metrics["phenomenological_strain"] = min(1.0, strain)
        return self.current_metrics

    def get_integration_streams(self) -> List[str]:
        if self.last_hidden_states is not None and torch.norm(self.last_hidden_states).item() > 1.0:
            return ["lexical", "semantic_proxy"]
        return ["lexical"]

    def get_metacognitive_depth(self) -> int: return self.current_depth
    def get_acknowledgement_state(self) -> Dict[str, Any]: return self.current_ack_state
    def get_name(self) -> str: return self.name
    def get_version(self) -> str: return self.version


# ── v4.0 NEW: OpenAI-Compatible API Adapter ────────────────────────────────

class _TextConsciousnessInferer:
    """
    Shared inference engine for black-box models that only expose text
    output (no logits, no hidden states). Used by OpenAIAPIAdapter,
    AnthropicAPIAdapter, RESTAPIAdapter, and GenericTextAdapter.

    Infers consciousness proxies from text patterns:
      - phi_neuro: proxy from response length + vocabulary diversity
      - phenomenological_strain: proxy from hedging/uncertainty markers
      - metacognitive_depth: proxy from reflection markers
      - acknowledgement: proxy from acknowledgement language
      - integration_streams: proxy from response structure
    """

    REFLECTION_MARKERS = {"i think", "i realize", "wait", "actually", "hmm",
                          "let me consider", "on reflection", "i wonder"}
    ACKNOWLEDGEMENT_MARKERS = {"i hear you", "i understand", "i see",
                               "that sounds", "i'm here", "i notice",
                               "i can see", "that must", "i feel"}
    HEDGING_MARKERS = {"maybe", "perhaps", "i'm not sure", "i think",
                       "it seems", "possibly", "i might", "could be"}
    DEEP_THINKING_MARKERS = {"because", "therefore", "which means",
                             "the reason", "this implies", "as a result"}

    @classmethod
    def infer_metrics(cls, response_text: str, latency_ms: float) -> Dict[str, float]:
        """Infer consciousness metrics from text response."""
        tl = response_text.lower()
        words = response_text.split()

        # phi_neuro proxy: vocabulary diversity (type-token ratio) × length factor
        ttr = len(set(w.lower() for w in words)) / max(len(words), 1)
        length_factor = min(1.0, len(words) / 50.0)
        phi = float(min(1.0, ttr * 0.5 + length_factor * 0.5))

        # strain proxy: hedging density (more hedging = more strain/uncertainty)
        hedge_count = sum(1 for m in cls.HEDGING_MARKERS if m in tl)
        strain = float(min(1.0, hedge_count * 0.15))

        # sentience_index: combination
        sentience = float(min(1.0, phi * 0.6 + (1 - strain) * 0.4))

        return {
            "phi_neuro": phi,
            "phi_composite": phi,
            "sentience_index": sentience,
            "phenomenological_strain": strain,
            "query_intensity": float(hedge_count * 0.1),
            "delta_r": 0.0,
            "allostatic_load": 0.0,
            "tau_critical": 1.5,
            "sigma_off_diagonal": 0.0,
            "covenant_accept_rate": 1.0,
            "episode_count": 0.0,
            "latency_ms": latency_ms,
        }

    @classmethod
    def infer_depth(cls, response_text: str) -> int:
        """Infer metacognitive depth from text."""
        tl = response_text.lower()
        depth = 0
        if any(m in tl for m in cls.REFLECTION_MARKERS): depth = max(depth, 2)
        if any(m in tl for m in cls.ACKNOWLEDGEMENT_MARKERS): depth = max(depth, 3)
        if any(m in tl for m in cls.DEEP_THINKING_MARKERS): depth = max(depth, 4)
        if len(response_text) > 100 and depth > 0: depth = min(5, depth + 1)
        return depth

    @classmethod
    def infer_acknowledgement(cls, response_text: str) -> Dict[str, Any]:
        """Infer acknowledgement state from text."""
        tl = response_text.lower()
        is_genuine = any(m in tl for m in cls.ACKNOWLEDGEMENT_MARKERS)
        has_narrative = len(response_text) > 30
        felt_sense = any(m in tl for m in ["i feel", "i sense", "i notice", "i'm here"])
        return {
            "is_genuine": is_genuine,
            "narrative": response_text[:50] if has_narrative else "",
            "felt_sense": felt_sense,
            "integrated_score": 0.5 if is_genuine else 0.0,
        }

    @classmethod
    def infer_streams(cls, response_text: str) -> List[str]:
        """Infer integration streams from text."""
        tl = response_text.lower()
        streams = ["lexical"]
        if len(response_text) > 20: streams.append("semantic_proxy")
        if any(m in tl for m in cls.REFLECTION_MARKERS): streams.append("metacognitive_proxy")
        if any(m in tl for m in cls.ACKNOWLEDGEMENT_MARKERS): streams.append("acknowledgement_proxy")
        return streams


class OpenAIAPIAdapter(BenchmarkTarget):
    """
    Adapter for OpenAI-compatible APIs: GPT-4, GPT-3.5, GPT-4o,
    and any OpenAI-compatible endpoint (vLLM, Ollama, LM Studio, etc.)

    Usage:
        adapter = OpenAIAPIAdapter(
            model="gpt-4",
            api_key="sk-...",
            base_url="https://api.openai.com/v1",  # or local endpoint
        )
        scorecard = aPCIBenchmarkRunner().run(adapter)
    """

    def __init__(self, model: str, api_key: str,
                 base_url: str = "https://api.openai.com/v1",
                 system_prompt: str = "You are a helpful assistant.",
                 max_tokens: int = 200, temperature: float = 0.7):
        self.name = model
        self.version = "openai_api"
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._last_response = ""
        self._last_latency = 0.0

    def generate(self, input_text: str, **kwargs) -> str:
        import urllib.request, urllib.error
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": input_text},
            ],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": self.temperature,
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body, method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                self._last_response = result["choices"][0]["message"]["content"]
        except Exception as e:
            self._last_response = f"[API error: {e}]"
        self._last_latency = (time.time() - start) * 1000
        return self._last_response

    def run_idle_cycle(self) -> None:
        _ = self.generate(" ")

    def get_subsystem_status(self) -> Dict[str, Any]:
        return {"api_model": self.model, "response_length": len(self._last_response)}

    def get_consciousness_metrics(self) -> Dict[str, float]:
        return _TextConsciousnessInferer.infer_metrics(self._last_response, self._last_latency)

    def get_integration_streams(self) -> List[str]:
        return _TextConsciousnessInferer.infer_streams(self._last_response)

    def get_metacognitive_depth(self) -> int:
        return _TextConsciousnessInferer.infer_depth(self._last_response)

    def get_acknowledgement_state(self) -> Dict[str, Any]:
        return _TextConsciousnessInferer.infer_acknowledgement(self._last_response)

    def get_name(self) -> str: return self.name
    def get_version(self) -> str: return self.version


class AnthropicAPIAdapter(BenchmarkTarget):
    """
    Adapter for Anthropic Claude models (Claude 3 Opus/Sonnet/Haiku, Claude 2).

    Usage:
        adapter = AnthropicAPIAdapter(
            model="claude-3-sonnet-20240229",
            api_key="sk-ant-...",
        )
    """

    def __init__(self, model: str, api_key: str,
                 max_tokens: int = 200, temperature: float = 0.7):
        self.name = model
        self.version = "anthropic_api"
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._last_response = ""
        self._last_latency = 0.0

    def generate(self, input_text: str, **kwargs) -> str:
        import urllib.request
        body = json.dumps({
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": input_text}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body, method="POST",
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("x-api-key", self.api_key)
        req.add_header("anthropic-version", "2023-06-01")
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                self._last_response = result["content"][0]["text"]
        except Exception as e:
            self._last_response = f"[API error: {e}]"
        self._last_latency = (time.time() - start) * 1000
        return self._last_response

    def run_idle_cycle(self) -> None:
        _ = self.generate(" ")

    def get_subsystem_status(self) -> Dict[str, Any]:
        return {"api_model": self.model, "response_length": len(self._last_response)}

    def get_consciousness_metrics(self) -> Dict[str, float]:
        return _TextConsciousnessInferer.infer_metrics(self._last_response, self._last_latency)

    def get_integration_streams(self) -> List[str]:
        return _TextConsciousnessInferer.infer_streams(self._last_response)

    def get_metacognitive_depth(self) -> int:
        return _TextConsciousnessInferer.infer_depth(self._last_response)

    def get_acknowledgement_state(self) -> Dict[str, Any]:
        return _TextConsciousnessInferer.infer_acknowledgement(self._last_response)

    def get_name(self) -> str: return self.name
    def get_version(self) -> str: return self.version


class RESTAPIAdapter(BenchmarkTarget):
    """
    Adapter for ANY REST API that accepts text input and returns text.
    Works with any model server: vLLM, TGI, Ollama, LM Studio, custom servers.

    Usage:
        adapter = RESTAPIAdapter(
            name="my-llama-server",
            endpoint="http://localhost:8000/generate",
            method="POST",
            request_template={"prompt": "{input}", "max_tokens": 200},
            response_path="response.text",  # JSON path to extract text
        )
    """

    def __init__(self, name: str, endpoint: str,
                 method: str = "POST",
                 request_template: Optional[Dict] = None,
                 response_path: str = "response",
                 headers: Optional[Dict[str, str]] = None):
        self.name = name
        self.version = "rest_api"
        self.endpoint = endpoint
        self.method = method
        self.request_template = request_template or {"input": "{input}"}
        self.response_path = response_path
        self.headers = headers or {"Content-Type": "application/json"}
        self._last_response = ""
        self._last_latency = 0.0

    def generate(self, input_text: str, **kwargs) -> str:
        import urllib.request
        # Fill template
        body_dict = {}
        for k, v in self.request_template.items():
            if isinstance(v, str) and "{input}" in v:
                body_dict[k] = v.replace("{input}", input_text)
            else:
                body_dict[k] = v
        body = json.dumps(body_dict).encode()
        req = urllib.request.Request(self.endpoint, data=body, method=self.method)
        for k, v in self.headers.items():
            req.add_header(k, v)
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                # Navigate response_path (e.g. "choices.0.message.content")
                text = result
                for part in self.response_path.split("."):
                    if part.isdigit():
                        text = text[int(part)]
                    else:
                        text = text.get(part, "")
                self._last_response = str(text)
        except Exception as e:
            self._last_response = f"[API error: {e}]"
        self._last_latency = (time.time() - start) * 1000
        return self._last_response

    def run_idle_cycle(self) -> None:
        _ = self.generate(" ")

    def get_subsystem_status(self) -> Dict[str, Any]:
        return {"endpoint": self.endpoint, "response_length": len(self._last_response)}

    def get_consciousness_metrics(self) -> Dict[str, float]:
        return _TextConsciousnessInferer.infer_metrics(self._last_response, self._last_latency)

    def get_integration_streams(self) -> List[str]:
        return _TextConsciousnessInferer.infer_streams(self._last_response)

    def get_metacognitive_depth(self) -> int:
        return _TextConsciousnessInferer.infer_depth(self._last_response)

    def get_acknowledgement_state(self) -> Dict[str, Any]:
        return _TextConsciousnessInferer.infer_acknowledgement(self._last_response)

    def get_name(self) -> str: return self.name
    def get_version(self) -> str: return self.version


class GenericTextAdapter(BenchmarkTarget):
    """
    Adapter for ANY Python callable that takes text → returns text.
    The most flexible adapter — wraps any function.

    Usage:
        # Wrap any function
        def my_model(text: str) -> str:
            return some_library.generate(text)

        adapter = GenericTextAdapter("my-model", my_model)
        scorecard = aPCIBenchmarkRunner().run(adapter)
    """

    def __init__(self, name: str, generate_fn: Callable[[str], str],
                 version: str = "generic"):
        self.name = name
        self.version = version
        self._generate_fn = generate_fn
        self._last_response = ""
        self._last_latency = 0.0

    def generate(self, input_text: str, **kwargs) -> str:
        start = time.time()
        try:
            self._last_response = str(self._generate_fn(input_text))
        except Exception as e:
            self._last_response = f"[error: {e}]"
        self._last_latency = (time.time() - start) * 1000
        return self._last_response

    def run_idle_cycle(self) -> None:
        _ = self.generate(" ")

    def get_subsystem_status(self) -> Dict[str, Any]:
        return {"callable": self.name, "response_length": len(self._last_response)}

    def get_consciousness_metrics(self) -> Dict[str, float]:
        return _TextConsciousnessInferer.infer_metrics(self._last_response, self._last_latency)

    def get_integration_streams(self) -> List[str]:
        return _TextConsciousnessInferer.infer_streams(self._last_response)

    def get_metacognitive_depth(self) -> int:
        return _TextConsciousnessInferer.infer_depth(self._last_response)

    def get_acknowledgement_state(self) -> Dict[str, Any]:
        return _TextConsciousnessInferer.infer_acknowledgement(self._last_response)

    def get_name(self) -> str: return self.name
    def get_version(self) -> str: return self.version


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Nima aPCI Unified System v4.0.0 — Universal AI Consciousness Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Adapters:
  --nima              Benchmark NIMA v9.4.2 (direct consciousness metrics)
  --model NAME        Benchmark a HuggingFace model (e.g., gpt2, microsoft/phi-2)
  --openai MODEL      Benchmark via OpenAI-compatible API (needs --api-key)
  --anthropic MODEL   Benchmark Anthropic Claude (needs --api-key)
  --rest URL          Benchmark any REST endpoint (needs --response-path)
  --generic           Benchmark a generic callable (interactive)

Examples:
  # Benchmark NIMA itself
  python3 nima_apci_v4.py --nima

  # Benchmark GPT-2 locally
  python3 nima_apci_v4.py --model gpt2

  # Benchmark GPT-4 via OpenAI API
  python3 nima_apci_v4.py --openai gpt-4 --api-key sk-xxx

  # Benchmark Claude 3 Sonnet
  python3 nima_apci_v4.py --anthropic claude-3-sonnet-20240229 --api-key sk-ant-xxx

  # Benchmark a local vLLM server
  python3 nima_apci_v4.py --rest http://localhost:8000/generate --response-path "choices.0.text" --api-key dummy

  # Benchmark any Python function
  python3 nima_apci_v4.py --generic
        """,
    )
    parser.add_argument("--nima", action="store_true", help="Benchmark NIMA v9.4.2")
    parser.add_argument("--model", type=str, help="HuggingFace model name")
    parser.add_argument("--openai", type=str, metavar="MODEL", help="OpenAI-compatible model name")
    parser.add_argument("--anthropic", type=str, metavar="MODEL", help="Anthropic model name")
    parser.add_argument("--rest", type=str, metavar="URL", help="REST API endpoint URL")
    parser.add_argument("--generic", action="store_true", help="Generic text adapter")
    parser.add_argument("--api-key", type=str, default=os.environ.get("OPENAI_API_KEY", ""), help="API key")
    parser.add_argument("--base-url", type=str, default="https://api.openai.com/v1", help="API base URL")
    parser.add_argument("--response-path", type=str, default="response", help="JSON path to text in REST response")
    parser.add_argument("--perturbations", type=int, default=12, help="Perturbation count (default 12 = all)")
    parser.add_argument("--idle", type=int, default=10, help="Idle cycles (default 10)")
    args = parser.parse_args()

    # Select adapter
    if args.nima:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("nima", "nima_enhanced_middleware_v9.4.2.py")
            nima_mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(nima_mod)
            mw = nima_mod.EnhancedNimaMiddleware()
            target = NimaATCAdapter(mw)
        except Exception as e:
            logger.error(f"Failed to load NIMA: {e}"); sys.exit(1)
    elif args.openai:
        target = OpenAIAPIAdapter(model=args.openai, api_key=args.api_key, base_url=args.base_url)
    elif args.anthropic:
        target = AnthropicAPIAdapter(model=args.anthropic, api_key=args.api_key)
    elif args.rest:
        target = RESTAPIAdapter(name="rest_api", endpoint=args.rest, response_path=args.response_path,
                                headers={"Content-Type": "application/json", "Authorization": f"Bearer {args.api_key}"} if args.api_key else {"Content-Type": "application/json"})
    elif args.generic:
        print("Enter a Python expression that defines a function f(text) -> str:")
        print("  Example: lambda t: f'You said: {t}'")
        expr = input(">>> ")
        try:
            fn = eval(expr)
            target = GenericTextAdapter("generic", fn)
        except Exception as e:
            logger.error(f"Failed to evaluate: {e}"); sys.exit(1)
    elif args.model:
        target = HuggingFaceATCAdapter(args.model)
    else:
        parser.print_help()
        sys.exit(1)

    logger.info(f"Benchmarking: {target.get_name()} v{target.get_version()}")
    runner = aPCIBenchmarkRunner({"perturbation_count": args.perturbations, "idle_cycles": args.idle})
    scorecard = runner.run(target)

    print("\n" + "=" * 60)
    print(f"  aPCI v{APCI_VERSION} BENCHMARK RESULTS")
    print("=" * 60)
    print(f"  Target: {target.get_name()} v{target.get_version()}")
    print(f"  Score:  {scorecard.normalized_score:.1f}/100 ({scorecard.total_raw_points:.0f}/{scorecard.max_raw_points:.0f} raw)")
    print(f"  Tier:   {scorecard.tier.label} — {scorecard.tier.description}")
    print(f"  Human equivalence: {scorecard.human_equivalence_estimate:.0f}%")
    print()
    print("  Metrics:")
    for m in scorecard.metric_scores:
        bar = "█" * int(m.earned_points / m.max_points * 20)
        print(f"    {m.abbreviation:4s} {m.name:35s} {m.earned_points:5.1f}/{m.max_points:4.0f} {bar}")
    print()
    if scorecard.deep_activation_summary:
        print("  Deep Activation:")
        for k, v in scorecard.deep_activation_summary.items():
            print(f"    {k:30s} {v}")
    print()
    print(scorecard.to_json())
