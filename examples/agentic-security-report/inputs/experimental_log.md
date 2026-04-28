# Experimental Log: Agentic Security Landscape Analysis

## 1. Experimental Setup

**Study Type:** Systematic market and threat landscape analysis  
**Date Range:** March–April 2026  
**Scope:** AI coding agent security threats, defenses, competitive vendors, market dynamics  
**Data Sources:** Vendor documentation, academic papers (arXiv, ICSE 2026), industry reports (GitGuardian, MarketsandMarkets, Gartner, Forrester), CVE databases, incident reports  
**Methodology:** Systematic vendor mapping, threat taxonomy, competitive capability matrix, market sizing

---

## 2. Raw Numeric Data

| Metric | Value | Source |
|--------|-------|--------|
| Gen AI in Cybersecurity (2025) | $8.65B | MarketsandMarkets |
| Gen AI in Cybersecurity (2031 projected) | $35.5B | MarketsandMarkets |
| CAGR | 26.5% | MarketsandMarkets |
| AI in Cybersecurity broad (2026) | $25.5B | MarketsandMarkets |
| Snyk developer security ARR (benchmark) | ~$200M | Public reporting |
| Snyk registered developers | 400,000+ | Snyk |

---

## 3. Secrets Sprawl Data (GitGuardian State of Secrets Sprawl 2026)

| Metric | Value | Change |
|--------|-------|--------|
| Hardcoded secrets on public GitHub (2025) | 28,650,000 | +34% YoY |
| AI service credentials exposed | 1,275,105 | +81% YoY |
| Claude Code commit secret leak rate | 3.2% | — |
| Human commit secret leak rate (baseline) | 1.5% | — |
| AI coding agent leak rate vs. baseline | 2.13x | — |
| Credentials from 2022 still exploitable (Jan 2026) | 64% | — |
| Secrets in non-code channels (Slack/Jira) | 28% of incidents | — |

---

## 4. LLM Agent Credential Leakage Empirical Study (Chen et al., arXiv:2604.03070, 2026)

| Finding | Value |
|---------|-------|
| Total skills analyzed | 17,022 |
| Vulnerable skills found | 520 (3.06%) |
| Distinct security issues | 1,708 |
| Issues requiring joint code+NL analysis | 76.3% |
| Debug logging as primary cause | 73.5% |
| Leaked credentials immediately exploitable | 89.6% |
| Credentials fixed post-disclosure | 91.6% |

---

## 5. Attack Success Rates (Academic Literature)

| Attack / Defense | Success Rate | Source |
|-----------------|-------------|--------|
| Adaptive prompt injection vs. current defenses | >85% | Maloyan & Namiot, arXiv:2601.17548 |
| Static attacks vs. AttriGuard | 0% | He et al., arXiv:2603.10749 |
| Attacks vs. ClawGuard (hook-layer) | <5% (3 benchmarks, 5 LLMs) | Zhao et al., arXiv:2604.11790 |
| Attacks vs. ICON (latent-space) | 0.4% | Wang et al., arXiv:2602.20708 |
| AgentSpec prevention of unsafe code | >90% | Wang et al., arXiv:2503.18666 |
| AgentSpec elimination of hazardous actions | 100% | Wang et al., ICSE 2026 |

---

## 6. MCP Ecosystem Threat Data (April 2026)

| Metric | Value | Source |
|--------|-------|--------|
| MCP SDK downloads affected by by-design RCE | 150,000,000+ | SecurityWeek |
| Publicly accessible MCP servers affected | 7,000+ | SecurityWeek |
| MCP servers with unauthenticated admin panels | 8,000+ | Cikce/Antiy CERT |
| Confirmed malicious skills in ClawHub | 1,184 | Antiy CERT |
| SANDWORM_MODE malicious npm packages | 19 | The Hacker News |
| Malicious VS Code AI extensions (combined installs) | 1,500,000+ | Multiple |
| MCP-related CVEs documented 2025-2026 | 4 | NVD |

---

## 7. Vendor Funding and Acquisition Timeline

| Company | Event | Amount | Date | Counterparty |
|---------|-------|--------|------|--------------|
| Invariant Labs | Acquisition | Undisclosed | June 2025 | Snyk |
| Protect AI | Acquisition | Undisclosed | 2025 | Palo Alto Networks |
| CalypsoAI | Acquisition | Undisclosed | ~2024 | F5 Networks |
| Robust Intelligence | Acquisition | Undisclosed | 2024 | Cisco |
| Irregular | Series B | $80M | Sept 2025 | VC |
| WitnessAI | Series B | $58M | 2025 | VC |
| Lakera AI | Series A | $20M | Sept 2024 | Forge/Redalpine |
| Runlayer | Seed | $11M | April 2025 | Keith Rabois, Felicis |
| Pillar Security | Seed | $9M | April 2025 | VC |
| Zenity | Series B-stage | ~$38M total | 2024-2025 | VC |

---

## 8. Competitive Capability Matrix

Scoring: YES / Partial / NO

| Vendor | Claude Code Hook | Secrets Cloaking | Post-hoc Sweep | MCP Detection | Air-gap/Local | Policy-as-Code | OWASP Coverage |
|--------|-----------------|-----------------|---------------|--------------|--------------|---------------|----------------|
| Prismor | YES | YES | YES | YES | YES | YES | 6-7/10 |
| Snyk/Invariant | NO | NO | NO | YES (CLI) | Partial | NO | 3/10 |
| Pillar Security | NO | NO | NO | NO | YES (VPC) | NO | 4/10 |
| Prompt Security | NO | NO | NO | YES (Gateway) | Partial | NO | 5/10 |
| Runlayer | NO | NO | NO | YES | NO | NO | 2/10 |
| Zenity | NO | NO | NO | NO | NO | NO | 3/10 |
| Lakera AI | NO | NO | NO | NO | NO | NO | 4/10 |
| Endor Labs | Partial | NO | NO | NO | NO | NO | 3/10 |
| CrowdStrike AIDR | NO | NO | NO | Partial | NO | NO | 4/10 |
| LLM Guard (OSS) | NO | NO | NO | NO | YES | NO | 3/10 |
| NeMo Guardrails (OSS) | NO | NO | NO | NO | YES | Partial | 3/10 |
| MCP-Scan (OSS) | NO | NO | NO | YES | YES | NO | 1/10 |

---

## 9. Prismor Architecture Performance

| Metric | Value |
|--------|-------|
| Hook enforcement overhead | Sub-millisecond (bash+jq, no Python on hot path) |
| Detection rules (default) | 25+ across 10 threat categories |
| Advisory feed entries | 217 (Ed25519-signed) |
| Supported coding agents | 4 (Claude Code, Cursor, Windsurf, OpenClaw) |
| Secret pattern types auto-detected | 15+ |
| Gitleaks patterns in Sweep | 170+ |
| Session storage | JSONL + SQLite |
| Feed signature algorithm | Ed25519 (tamper-evident) |

---

## 10. Documented Incident Timeline (2025-2026)

| Date | Incident | Vector | Severity |
|------|----------|--------|----------|
| March 2025 | Rules File Backdoor (Cursor, Copilot) | Unicode config poisoning | High |
| April 2025 | MCP Tool Poisoning (Invariant Labs) | Tool description injection | High |
| May 2025 | GitHub MCP private repo access | First-party MCP exploit | Critical |
| 2025 | SANDWORM_MODE npm campaign | Supply chain + MCP injection | Critical |
| 2025 | Malicious VS Code AI extensions (1.5M installs) | Extension exfiltration | High |
| 2025 | LangChain RCE (CVE-2025-68664, CVSS 9.3) | Deserialization RCE | Critical |
| Feb 2026 | 8,000+ exposed MCP servers | Unauthenticated admin access | Critical |
| March 2026 | LiteLLM PyPI supply chain backdoor | Package backdoor | Critical |
| April 2026 | MCP SDK by-design RCE (150M+ downloads) | STDIO RCE | Critical |
| April 2026 | Flowise RCE (CVE-2025-59528) | LLM platform RCE (CVSS 10.0) | Critical |
| April 2026 | Claude Code hook injection (CVE-2025-59536) | Settings.json injection (CVSS 8.7) | High |

---

## 11. Validated Research Papers

| Paper | Venue/ID | Year | Validates |
|-------|----------|------|-----------|
| ClawGuard: Runtime Security at Tool-Call Boundaries | arXiv:2604.11790 | 2026 | Warden hook architecture |
| AttriGuard: Causal Attribution for Tool Invocations | arXiv:2603.10749 | 2026 | Causal extension for Warden |
| AgentSpec: Runtime Enforcement DSL | arXiv:2503.18666 (ICSE 2026) | 2026 | YAML policy engine |
| ICON: Latent-Space Injection Detection | arXiv:2602.20708 | 2026 | Complementary model-layer defense |
| AgentSentry: Temporal Causal Injection | arXiv:2602.22724 | 2026 | Multi-turn session gap |
| Prompt Injection on Agentic Coding Assistants (78 studies) | arXiv:2601.17548 | 2026 | Attack landscape (42 techniques) |
| Credential Leakage in LLM Agent Skills | arXiv:2604.03070 | 2026 | Cloak/Sweep necessity |
| AgentTower: Attack/Defense Landscape Survey | arXiv:2603.11088 | 2026 | Foundational taxonomy |
| Cornell/NVIDIA/Google system-level defenses | arXiv:2603.30016 | 2026 | Architecture validation |
| Microsoft Agent Governance Toolkit | Open source | 2026 | Competitive/complementary |
