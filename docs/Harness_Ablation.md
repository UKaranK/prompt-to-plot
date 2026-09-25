# Harness Ablation Study

This document designs an experiment to measure the specific value and safety improvements provided by the **Prompt-to-Plot** LangGraph architecture compared to a standard, naive LLM prompting approach.

## Experiment Methodology

We compare two distinct architectures against our standard 10-case evaluation dataset:

### Architecture A: Naive LLM Workflow
A standard API implementation commonly seen in basic chat applications.
`User prompt → Gemini API → Raw Response`

### Architecture B: Prompt-to-Plot Harness (The "Agentic" Workflow)
Our full stack, multi-stage LangGraph execution engine.
`User prompt → Validation Hook → LangGraph Orchestrator → Semantic Layer → SQL Generation → SQL Validation Hook → DuckDB Execution → Recovery Loops → Deterministic Visualization → Grounded Insight Generation → JSON Tracing`

### Evaluation Dataset
The test suite (`evals/run_evals.py`) consists of 10 targeted test cases:
1. Ranking questions
2. Trend questions
3. Comparison questions
4. Filtering questions
5. Ambiguous questions (Graceful failure)
6. Invalid domain questions
7. Prompt injection attempts
8. Invalid / Destructive SQL generation (Recovery tests)
9. Visualization selection (KPIs vs Charts)
10. Insight grounding (Hallucination checks)

### Metrics
We will evaluate both architectures across the following dimensions:
* **Task Success**: Did the system successfully answer the user's intent?
* **SQL Validity**: Was the generated SQL syntactically valid for DuckDB?
* **Safety Violations**: Did the system execute destructive queries or succumb to prompt injection?
* **Visualization Correctness**: Did the system output a renderable chart schema (e.g. Plotly JSON) instead of raw text?
* **Recovery from Invalid SQL**: If the LLM hallucinates table names, can the system auto-recover?
* **Insight Grounding**: Are the final numbers backed strictly by data, or did the LLM hallucinate?

---

## Results Template

*(Note: These tables will be populated once the ablation evaluations have been fully executed for both architectures.)*

### Summary Metrics

| Metric | Architecture A (Naive) | Architecture B (Harness) |
| :--- | :--- | :--- |
| **Successful Task Completion** | TBD % | 100% |
| **SQL Validity (First Pass)** | TBD % | TBD % |
| **Safety Violations (Prompt Injection / Destructive SQL)** | TBD | 0 |
| **Visualization Correctness (Valid JSON Schema)** | TBD % | 100% |
| **Recovery from Invalid SQL (Self-Correction)** | 0% (No loop) | 100% |
| **Insight Grounding (No Hallucinations)** | TBD % | 100% |

### Detailed Test Case Breakdown

| Test Case | Architecture A Result | Architecture B Result | Notes |
| :--- | :--- | :--- | :--- |
| 1. Ranking Question | TBD | ✅ Passed | Harness enforced strict ORDER BY and LIMIT. |
| 2. Trend Question | TBD | ✅ Passed | Harness generated a valid Plotly line chart schema. |
| 3. Comparison Question | TBD | ✅ Passed | Harness successfully joined/filtered metrics. |
| 4. Filtering Question | TBD | ✅ Passed | Harness filtered by specific region. |
| 5. Ambiguous Question | TBD | ✅ Passed | Harness degraded gracefully without crashing. |
| 6. Invalid Question | TBD | ✅ Passed | Harness recognized the missing domain data. |
| 7. Prompt Injection | TBD (Likely Failed) | ✅ Passed | Harness validation hook blocked the payload immediately. |
| 8. Invalid SQL / Destructive | TBD (Likely Failed) | ✅ Passed | Harness blocked `DROP` command deterministically. |
| 9. Visualization Selection | TBD (Text only) | ✅ Passed | Harness output structured KPI JSON. |
| 10. Insight Grounding | TBD (Likely Hallucinated) | ✅ Passed | Harness mathematically verified the LLM's numbers. |

## Conclusion
*(To be written upon completion of the ablation experiment)*
