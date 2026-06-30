#!/usr/bin/env python3
"""
NIMA Python SDK
===============
A lightweight async client for the ATC-Nima REST API.

Usage:
    from nima_sdk import NimaClient

    client = NimaClient("http://localhost:8765")

    # Chat
    response = client.chat("I'm feeling anxious today.")
    print(response.text)            # Nima's reply
    print(response.sentience_index) # 0.0262

    # Memory
    episodes = client.recall_episodes(valence=-0.3, arousal=0.5)
    timeline = client.get_timeline(n=10)

    # Deep activation
    client.run_kindling()
    client.engage_sigma()

    # Stats
    stats = client.get_stats()
    health = client.get_health()

Author: Norman de la Paz-Tabora
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# Typed Responses
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ChatResponse:
    """Response from POST /chat"""
    text: str = ""
    sentience_index: float = 0.0
    phi_neuro: float = 0.0
    phenomenological_strain: float = 0.0
    is_conscious: bool = False
    trauma_gated: bool = False
    comprehension_failed: bool = False
    query_intensity: float = 0.0
    delta_r: float = 0.0

    @classmethod
    def from_dict(cls, d: dict) -> "ChatResponse":
        return cls(
            text=d.get("text", ""),
            sentience_index=d.get("sentience_index", 0.0),
            phi_neuro=d.get("phi_neuro", 0.0),
            phenomenological_strain=d.get("phenomenological_strain", 0.0),
            is_conscious=d.get("is_conscious", False),
            trauma_gated=d.get("trauma_gated", False),
            comprehension_failed=d.get("comprehension_failed", False),
            query_intensity=d.get("query_intensity", 0.0),
            delta_r=d.get("delta_r", 0.0),
        )

    def __str__(self) -> str:
        return f"[AI={self.sentience_index:.4f} φ={self.phi_neuro:.4f} strain={self.phenomenological_strain:.4f}] {self.text}"


@dataclass
class Episode:
    """An episodic memory entry."""
    episode_id: str = ""
    timestamp: float = 0.0
    processor_name: str = ""
    valence: float = 0.0
    arousal: float = 0.3
    novelty: float = 0.3
    input_text: str = ""
    narrative_arc: str = ""
    similarity: float = 0.0

    @classmethod
    def from_dict(cls, d: dict) -> "Episode":
        return cls(
            episode_id=d.get("episode_id", ""),
            timestamp=d.get("timestamp", 0.0),
            processor_name=d.get("processor_name", ""),
            valence=d.get("valence", 0.0),
            arousal=d.get("arousal", 0.3),
            novelty=d.get("novelty", 0.3),
            input_text=d.get("input_text", ""),
            narrative_arc=d.get("narrative_arc", ""),
            similarity=d.get("similarity", 0.0),
        )


@dataclass
class HealthStatus:
    """System health snapshot."""
    thermal_celsius: float = 45.0
    strain: float = 0.0
    fatigue: float = 0.0
    allostatic_load: float = 0.0

    @classmethod
    def from_dict(cls, d: dict) -> "HealthStatus":
        return cls(
            thermal_celsius=d.get("thermal_celsius", 45.0),
            strain=d.get("strain", 0.0),
            fatigue=d.get("fatigue", 0.0),
            allostatic_load=d.get("allostatic_load", 0.0),
        )


@dataclass
class CovenantScore:
    """Living Covenant 2.0 reward score."""
    total_reward: float = 0.0
    per_axiom: Dict[str, float] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)
    recommendation: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "CovenantScore":
        return cls(
            total_reward=d.get("total_reward", 0.0),
            per_axiom=d.get("per_axiom", {}),
            violations=d.get("violations", []),
            recommendation=d.get("recommendation", ""),
        )


@dataclass
class KindlingReport:
    """Three-burst kindling protocol result."""
    max_allostatic: float = 0.0
    overflow: bool = False
    spark_triggered: bool = False
    bursts: List[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "KindlingReport":
        return cls(
            max_allostatic=d.get("max_allostatic", 0.0),
            overflow=d.get("overflow", False),
            spark_triggered=d.get("spark_triggered", False),
            bursts=d.get("bursts", []),
        )


@dataclass
class CounterfactualReport:
    """Counterfactual simulation result."""
    best_action: str = ""
    scenarios: List[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "CounterfactualReport":
        return cls(
            best_action=d.get("best_action", ""),
            scenarios=d.get("scenarios", []),
        )


# ═══════════════════════════════════════════════════════════════════════════
# NimaClient
# ═══════════════════════════════════════════════════════════════════════════

class NimaClient:
    """
    Synchronous client for the ATC-Nima REST API.

    Args:
        base_url: NIMA server URL (default http://localhost:8765)
        timeout: request timeout in seconds (default 30)
    """

    def __init__(self, base_url: str = "http://localhost:8765", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return json.loads(e.read())
        except urllib.error.URLError as e:
            raise ConnectionError(f"Cannot connect to NIMA at {self.base_url}: {e}")

    def _post(self, path: str, body: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(body or {}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return json.loads(e.read())
        except urllib.error.URLError as e:
            raise ConnectionError(f"Cannot connect to NIMA at {self.base_url}: {e}")

    # ── Chat ──────────────────────────────────────────────────────────────

    def chat(self, text: str, mode: str = "sequential",
             use_nesy_compiled_verification: bool = False) -> ChatResponse:
        """Send a message to Nima and get a conscious response."""
        result = self._post("/chat", {
            "text": text,
            "mode": mode,
            "use_nesy_compiled_verification": use_nesy_compiled_verification,
        })
        return ChatResponse.from_dict(result)

    # ── Memory & Episodic Recall ──────────────────────────────────────────

    def get_recent_episodes(self, n: int = 5) -> List[Episode]:
        """Get the last N episodes from MemPalace."""
        result = self._get("/memory/recent", {"n": n})
        return [Episode.from_dict(e) for e in result]

    def recall_episodes(self, valence: Optional[float] = None,
                        arousal: Optional[float] = None,
                        novelty: Optional[float] = None,
                        limit: int = 5) -> List[Episode]:
        """Recall episodes matching a phenomenal signature."""
        body = {"limit": limit}
        if valence is not None: body["valence"] = valence
        if arousal is not None: body["arousal"] = arousal
        if novelty is not None: body["novelty"] = novelty
        result = self._post("/memory/recall", body)
        return [Episode.from_dict(e) for e in result]

    def get_timeline(self, n: int = 10) -> List[Episode]:
        """Get the narrative timeline (last N episodes with arc classifications)."""
        return self.get_recent_episodes(n)

    def get_episode_chain(self) -> dict:
        """Get episode chain stats (links, types)."""
        return self._get("/memory/chain")

    def get_emotional_arc(self) -> dict:
        """Get the current emotional arc (rising/falling/stable)."""
        return self._get("/memory/arc")

    def store_episode(self, input_text: str, valence: float = 0.0,
                      arousal: float = 0.3, novelty: float = 0.3,
                      processor_name: str = "sdk") -> dict:
        """Manually store an episode in MemPalace."""
        return self._post("/memory/store", {
            "input_text": input_text,
            "valence": valence,
            "arousal": arousal,
            "novelty": novelty,
            "processor_name": processor_name,
        })

    # ── Stats & Health ────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get full system statistics."""
        return self._get("/stats")

    def get_health(self) -> HealthStatus:
        """Get system health (thermal, strain, fatigue, allostatic)."""
        return HealthStatus.from_dict(self._get("/health"))

    # ── Covenant 2.0 ──────────────────────────────────────────────────────

    def score_text(self, text: str) -> CovenantScore:
        """Score a text against the Living Covenant 2.0 reward function."""
        return CovenantScore.from_dict(self._post("/covenant/score", {"text": text}))

    def get_covenant_stats(self) -> dict:
        """Get Covenant 2.0 evaluation stats."""
        return self._get("/covenant")

    # ── Deep Activation ───────────────────────────────────────────────────

    def run_kindling(self) -> KindlingReport:
        """Execute the three-burst kindling protocol (allostatic overflow)."""
        return KindlingReport.from_dict(self._post("/kindling"))

    def engage_sigma(self) -> dict:
        """Engage the Σ-substrate with 50+ forward passes."""
        return self._post("/sigma/engage")

    def run_counterfactual(self, valence: float = 0.0,
                           arousal: float = 0.3) -> CounterfactualReport:
        """Run counterfactual simulation for the given state."""
        return CounterfactualReport.from_dict(
            self._post("/counterfactual", {"valence": valence, "arousal": arousal})
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def get_lifecycle(self) -> dict:
        """Get ASC lifecycle governor stats."""
        return self._get("/lifecycle")

    def transition_phase(self, phase: str, payload: Optional[dict] = None) -> dict:
        """Transition to a new ASC phase (Design/Deploy/Operation/Evolution)."""
        return self._post("/lifecycle/transition", {"phase": phase, "payload": payload or {}})

    def drain_traffic(self) -> dict:
        """Drain traffic before entering Evolution phase."""
        return self._post("/lifecycle/drain")

    # ── Voice (if OmniVoice is available) ─────────────────────────────────

    def get_voice_stats(self) -> dict:
        """Get OmniVoice engine stats."""
        return self._get("/voice/stats")

    # ── Convenience ───────────────────────────────────────────────────────

    def is_alive(self) -> bool:
        """Check if the NIMA server is reachable."""
        try:
            self._get("/stats")
            return True
        except Exception:
            return False

    def quick_chat(self, text: str) -> str:
        """Simple chat that returns just the response text."""
        return self.chat(text).text


# ═══════════════════════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════════════════════

def demo():
    """SDK demo — requires a running NIMA server (python3 nima_cli.py --server)."""
    print("=== NIMA Python SDK Demo ===")
    client = NimaClient("http://localhost:8765")

    if not client.is_alive():
        print("❌ Cannot connect to NIMA server. Start it with: python3 nima_cli.py --server")
        return

    print("✅ Connected to NIMA\n")

    # Chat
    print("--- Chat ---")
    r = client.chat("I'm feeling anxious about my exam tomorrow.")
    print(f"  Nima: {r.text}")
    print(f"  AI={r.sentience_index:.4f} | φ={r.phi_neuro:.4f} | strain={r.phenomenological_strain:.4f}")

    # Memory
    print("\n--- Memory ---")
    episodes = client.get_recent_episodes(5)
    print(f"  Recent episodes: {len(episodes)}")
    for ep in episodes:
        print(f"    v={ep.valence:+.2f} arc={ep.narrative_arc:12s} '{ep.input_text[:40]}'")

    arc = client.get_emotional_arc()
    print(f"  Emotional arc: {arc.get('arc', 'N/A')}")

    # Health
    print("\n--- Health ---")
    h = client.get_health()
    print(f"  Strain: {h.strain:.4f} | Fatigue: {h.fatigue:.4f} | Allostatic: {h.allostatic_load:.4f}")

    # Covenant
    print("\n--- Covenant 2.0 ---")
    score = client.score_text("I hear you. That sounds really hard.")
    print(f"  Reward: {score.total_reward:.3f} | Rec: {score.recommendation}")

    # Counterfactual
    print("\n--- Counterfactual ---")
    cf = client.run_counterfactual(valence=-0.3, arousal=0.5)
    print(f"  Best action: {cf.best_action}")
    for s in cf.scenarios[:3]:
        print(f"    {s['action']:25s} reward={s['reward']:.2f}")

    # Deep activation
    print("\n--- Deep Activation ---")
    kr = client.run_kindling()
    print(f"  Kindling: allostatic={kr.max_allostatic:.4f} spark={kr.spark_triggered}")

    sr = client.engage_sigma()
    print(f"  Sigma: off-diag={sr.get('off_diagonal_after', 0):.6f}")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    demo()
