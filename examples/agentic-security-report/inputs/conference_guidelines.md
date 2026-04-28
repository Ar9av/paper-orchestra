# Technical Report Guidelines: Prismor Agentic Security White Paper 2026

## Document Type
This is a technical industry white paper / research report, not a traditional academic conference submission. The output should be a professional, self-contained document suitable for: enterprise security buyers, investors, security researchers, and developer teams evaluating AI coding agent security tooling.

## Length and Structure
- Target length: 12-16 pages (including figures, tables, and references)
- All sections listed below are mandatory
- Abstract: 250-350 words
- Every major claim must be supported with data from experimental_log.md or cited literature
- Tables and figures are encouraged — aim for 4-6 figures and 3-5 tables

## Mandatory Sections (in order)

1. Abstract: problem statement, approach, key findings, main contribution (250-350 words)
2. Introduction: why AI coding agents create a new attack surface; why existing security controls fail; threat landscape summary with key statistics
3. Threat Landscape and Related Work: documented incidents (2025-2026), academic research on runtime enforcement, MCP security, secrets leakage; position relative to existing work
4. Architecture Defense-in-Depth for AI Coding Agents: full technical description of Warden, Cloak, Sweep; system diagram required
5. Competitive Analysis: quantitative coverage matrix; competitive map positioning; differentiation analysis
6. Evaluation: OWASP LLM Top 10 coverage; empirical secret leakage data comparison; competitor coverage matrix analysis
7. Market Opportunity and Strategic Roadmap: market sizing; target customer segments; monetization model; product roadmap priorities
8. Conclusion: summary of contributions; open problems; future directions
9. References: all cited works in consistent bibliography format

## Style Guidelines
- Writing tone: authoritative, evidence-driven, direct. Not marketing copy. Not academic jargon.
- Tables must use professional formatting with clear column headers
- Use numbered sections (1, 2, 3...) and numbered subsections (2.1, 2.2...)
- All statistics must be attributed to their source inline
- Figures should include: system architecture diagram, competitive map, coverage matrix heatmap, market growth chart, threat incident timeline
- Use LaTeX booktabs for all tables
- Captions required for all figures and tables

## LaTeX Formatting Requirements
- Document class: article, 11pt
- Page margins: 1 inch all sides
- Column layout: single column
- Citation style: numeric IEEE-style bibliography
- Hyperlinks: colored, using hyperref package
- Use booktabs for tables
- Use tikz or pgfplots for diagrams where possible

## Cutoff Date
April 28, 2026. Do not include references to papers or events after this date.
