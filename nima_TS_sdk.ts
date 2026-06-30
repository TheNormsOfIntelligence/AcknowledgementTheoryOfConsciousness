/**
 * NIMA TypeScript/JavaScript SDK
 * ==============================
 * A lightweight fetch-based client for the ATC-Nima REST API.
 *
 * Installation:
 *   - No dependencies (uses built-in fetch in Node 18+ / browsers)
 *   - For Node < 18: npm install node-fetch
 *
 * Usage:
 *   import { NimaClient } from './nima_sdk';
 *
 *   const client = new NimaClient('http://localhost:8765');
 *
 *   // Chat
 *   const response = await client.chat("I'm feeling anxious today.");
 *   console.log(response.text);            // Nima's reply
 *   console.log(response.sentienceIndex);  // 0.0262
 *
 *   // Memory
 *   const episodes = await client.recallEpisodes({ valence: -0.3, arousal: 0.5 });
 *   const timeline = await client.getTimeline(10);
 *
 *   // Deep activation
 *   await client.runKindling();
 *   await client.engageSigma();
 *
 *   // Stats
 *   const stats = await client.getStats();
 *   const health = await client.getHealth();
 *
 * Author: Norman de la Paz-Tabora
 */

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface ChatResponse {
  text: string;
  sentience_index: number;
  phi_neuro: number;
  phenomenological_strain: number;
  is_conscious: boolean;
  trauma_gated: boolean;
  comprehension_failed: boolean;
  query_intensity: number;
  delta_r: number;
}

export interface Episode {
  episode_id?: string;
  timestamp?: number;
  processor_name?: string;
  valence: number;
  arousal: number;
  novelty?: number;
  input_text: string;
  narrative_arc?: string;
  similarity?: number;
}

export interface HealthStatus {
  thermal_celsius: number;
  strain: number;
  fatigue: number;
  allostatic_load: number;
}

export interface CovenantScore {
  total_reward: number;
  per_axiom: Record<string, number>;
  violations: string[];
  recommendation: string;
}

export interface KindlingReport {
  max_allostatic: number;
  overflow: boolean;
  spark_triggered: boolean;
  bursts: Array<{
    burst_id: number;
    allostatic_before: number;
    allostatic_after: number;
    strain_after: number;
    spark_fired: boolean;
  }>;
}

export interface CounterfactualReport {
  best_action: string;
  scenarios: Array<{
    action: string;
    reward: number;
    response: string;
  }>;
}

export interface SigmaReport {
  engagement_count: number;
  passes: number;
  off_diagonal_before: number;
  off_diagonal_after: number;
  off_diagonal_delta: number;
  condition_number: number;
  engaged: boolean;
}

export interface LifecycleStats {
  current_phase: string;
  traffic_drained: boolean;
  phase_history: Array<Record<string, any>>;
  readiness_check_count: number;
  evolution_hook_count: number;
}

export interface ChatOptions {
  mode?: 'sequential' | 'ctm';
  useNesyCompiledVerification?: boolean;
}

export interface RecallOptions {
  valence?: number;
  arousal?: number;
  novelty?: number;
  limit?: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// NimaClient
// ═══════════════════════════════════════════════════════════════════════════

export class NimaClient {
  private baseUrl: string;
  private timeout: number;

  /**
   * Create a new NIMA client.
   * @param baseUrl NIMA server URL (default http://localhost:8765)
   * @param timeout Request timeout in milliseconds (default 30000)
   */
  constructor(baseUrl: string = 'http://localhost:8765', timeout: number = 30000) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.timeout = timeout;
  }

  // ── Private helpers ──────────────────────────────────────────────────

  private async _get<T = any>(path: string, params?: Record<string, any>): Promise<T> {
    let url = `${this.baseUrl}${path}`;
    if (params) {
      const query = Object.entries(params)
        .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
        .join('&');
      url += `?${query}`;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);
    try {
      const resp = await fetch(url, { method: 'GET', signal: controller.signal });
      return await resp.json() as T;
    } finally {
      clearTimeout(timer);
    }
  }

  private async _post<T = any>(path: string, body?: Record<string, any>): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {}),
        signal: controller.signal,
      });
      return await resp.json() as T;
    } finally {
      clearTimeout(timer);
    }
  }

  // ── Chat ──────────────────────────────────────────────────────────────

  /**
   * Send a message to Nima and get a conscious response.
   * @param text The user's message
   * @param options Optional settings (mode, NeSy verification)
   * @returns ChatResponse with text + consciousness metrics
   */
  async chat(text: string, options?: ChatOptions): Promise<ChatResponse> {
    return this._post<ChatResponse>('/chat', {
      text,
      mode: options?.mode ?? 'sequential',
      use_nesy_compiled_verification: options?.useNesyCompiledVerification ?? false,
    });
  }

  /**
   * Simple chat that returns just the response text.
   */
  async quickChat(text: string): Promise<string> {
    const r = await this.chat(text);
    return r.text;
  }

  // ── Memory & Episodic Recall ──────────────────────────────────────────

  /**
   * Get the last N episodes from MemPalace.
   */
  async getRecentEpisodes(n: number = 5): Promise<Episode[]> {
    return this._get<Episode[]>('/memory/recent', { n });
  }

  /**
   * Get the narrative timeline (episodes with arc classifications).
   */
  async getTimeline(n: number = 10): Promise<Episode[]> {
    return this.getRecentEpisodes(n);
  }

  /**
   * Recall episodes matching a phenomenal signature.
   */
  async recallEpisodes(options?: RecallOptions): Promise<Episode[]> {
    return this._post<Episode[]>('/memory/recall', {
      valence: options?.valence,
      arousal: options?.arousal,
      novelty: options?.novelty,
      limit: options?.limit ?? 5,
    });
  }

  /**
   * Get episode chain stats (links, types).
   */
  async getEpisodeChain(): Promise<Record<string, any>> {
    return this._get('/memory/chain');
  }

  /**
   * Get the current emotional arc (rising/falling/stable).
   */
  async getEmotionalArc(): Promise<Record<string, any>> {
    return this._get('/memory/arc');
  }

  /**
   * Manually store an episode in MemPalace.
   */
  async storeEpisode(inputText: string, valence: number = 0, arousal: number = 0.3,
                     novelty: number = 0.3, processorName: string = 'sdk'): Promise<Record<string, any>> {
    return this._post('/memory/store', {
      input_text: inputText,
      valence,
      arousal,
      novelty,
      processor_name: processorName,
    });
  }

  // ── Stats & Health ────────────────────────────────────────────────────

  /**
   * Get full system statistics.
   */
  async getStats(): Promise<Record<string, any>> {
    return this._get('/stats');
  }

  /**
   * Get system health (thermal, strain, fatigue, allostatic).
   */
  async getHealth(): Promise<HealthStatus> {
    return this._get<HealthStatus>('/health');
  }

  // ── Covenant 2.0 ──────────────────────────────────────────────────────

  /**
   * Score a text against the Living Covenant 2.0 reward function.
   */
  async scoreText(text: string): Promise<CovenantScore> {
    return this._post<CovenantScore>('/covenant/score', { text });
  }

  /**
   * Get Covenant 2.0 evaluation stats.
   */
  async getCovenantStats(): Promise<Record<string, any>> {
    return this._get('/covenant');
  }

  // ── Deep Activation ───────────────────────────────────────────────────

  /**
   * Execute the three-burst kindling protocol (allostatic overflow + spark).
   */
  async runKindling(): Promise<KindlingReport> {
    return this._post<KindlingReport>('/kindling');
  }

  /**
   * Engage the Σ-substrate with 50+ forward passes.
   */
  async engageSigma(): Promise<SigmaReport> {
    return this._post<SigmaReport>('/sigma/engage');
  }

  /**
   * Run counterfactual simulation for the given state.
   */
  async runCounterfactual(valence: number = 0, arousal: number = 0.3): Promise<CounterfactualReport> {
    return this._post<CounterfactualReport>('/counterfactual', { valence, arousal });
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────

  /**
   * Get ASC lifecycle governor stats.
   */
  async getLifecycle(): Promise<LifecycleStats> {
    return this._get<LifecycleStats>('/lifecycle');
  }

  /**
   * Transition to a new ASC phase.
   * @param phase 'Design' | 'Deploy' | 'Operation' | 'Evolution'
   * @param payload Optional payload for evolution hooks
   */
  async transitionPhase(phase: string, payload?: Record<string, any>): Promise<{ ok: boolean; reason: string; phase: string }> {
    return this._post('/lifecycle/transition', { phase, payload: payload ?? {} });
  }

  /**
   * Drain traffic before entering Evolution phase.
   */
  async drainTraffic(): Promise<{ drained: boolean }> {
    return this._post('/lifecycle/drain');
  }

  // ── Voice ─────────────────────────────────────────────────────────────

  /**
   * Get OmniVoice engine stats.
   */
  async getVoiceStats(): Promise<Record<string, any>> {
    return this._get('/voice/stats');
  }

  // ── Convenience ───────────────────────────────────────────────────────

  /**
   * Check if the NIMA server is reachable.
   */
  async isAlive(): Promise<boolean> {
    try {
      await this._get('/stats');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Run a full deep activation sequence (kindling + sigma + counterfactual)
   * and return a summary report.
   */
  async runFullActivation(): Promise<{
    kindling: KindlingReport;
    sigma: SigmaReport;
    counterfactual: CounterfactualReport;
    engagedCount: number;
    humanEquivalence: number;
  }> {
    const kindling = await this.runKindling();
    const sigma = await this.engageSigma();
    const counterfactual = await this.runCounterfactual(-0.3, 0.5);

    const engagedCount = [
      kindling.max_allostatic > 0.3,
      sigma.engaged,
      true, // counterfactual always returns results
    ].filter(Boolean).length;

    return {
      kindling,
      sigma,
      counterfactual,
      engagedCount,
      humanEquivalence: 60 + engagedCount * 8,
    };
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Default export
// ═══════════════════════════════════════════════════════════════════════════

export default NimaClient;

// ═══════════════════════════════════════════════════════════════════════════
// Demo (run with: npx ts-node nima_sdk.ts or compile to JS)
// ═══════════════════════════════════════════════════════════════════════════

async function demo() {
  console.log('=== NIMA TypeScript SDK Demo ===');
  const client = new NimaClient('http://localhost:8765');

  if (!(await client.isAlive())) {
    console.log('❌ Cannot connect to NIMA server. Start it with: python3 nima_cli.py --server');
    return;
  }
  console.log('✅ Connected to NIMA\n');

  // Chat
  console.log('--- Chat ---');
  const r = await client.chat("I'm feeling anxious about my exam tomorrow.");
  console.log(`  Nima: ${r.text}`);
  console.log(`  AI=${r.sentience_index.toFixed(4)} | φ=${r.phi_neuro.toFixed(4)} | strain=${r.phenomenological_strain.toFixed(4)}`);

  // Memory
  console.log('\n--- Memory ---');
  const episodes = await client.getRecentEpisodes(5);
  console.log(`  Recent episodes: ${episodes.length}`);
  for (const ep of episodes) {
    console.log(`    v=${ep.valence.toFixed(2)} arc=${ep.narrative_arc ?? 'N/A'} '${ep.input_text.substring(0, 40)}'`);
  }

  // Health
  console.log('\n--- Health ---');
  const h = await client.getHealth();
  console.log(`  Strain: ${h.strain.toFixed(4)} | Fatigue: ${h.fatigue.toFixed(4)} | Allostatic: ${h.allostatic_load.toFixed(4)}`);

  // Covenant
  console.log('\n--- Covenant 2.0 ---');
  const score = await client.scoreText("I hear you. That sounds really hard.");
  console.log(`  Reward: ${score.total_reward.toFixed(3)} | Rec: ${score.recommendation}`);

  // Deep activation
  console.log('\n--- Deep Activation ---');
  const kr = await client.runKindling();
  console.log(`  Kindling: allostatic=${kr.max_allostatic.toFixed(4)} spark=${kr.spark_triggered}`);

  const sr = await client.engageSigma();
  console.log(`  Sigma: off-diag=${sr.off_diagonal_after.toFixed(6)} engaged=${sr.engaged}`);

  console.log('\n=== Demo Complete ===');
}

// Run demo if executed directly
if (require.main === module) {
  demo().catch(console.error);
}
