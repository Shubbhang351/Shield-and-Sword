# 🚨 CRITICAL AI AGENT MANDATE (READ FIRST)

> **ATTENTION ALL AI CODING AGENTS (Aider, OpenCode, Codex, Claude, Gemini, etc.):**
> 1. **Mandatory Protocol:** You MUST read this entire document (`Shield-and-Sword-runbook.md`) before executing any workspace instructions.
> 2. **Auto-Update Requirement:** After implementing any code, modifying files, fixing bugs, or changing project architecture, you MUST immediately update this runbook.
> 3. **Logging Duty:** Log all created/modified files, summarize newly added logic, and update the progress checkboxes in **Section 5** before concluding your task.

---

# 📖 Shield & Sword — Technical Runbook & Progress Tracker

This document serves as the single source of truth for technical setup, environment configuration, issue resolution logs, operational workflows, and active project progress for **Project Shield & Sword**.

---

## 1. System Architecture & Environment

* **Operating System:** Windows 11 (PowerShell)
* **Global Python:** 3.13
* **Tool Isolation Manager:** `uv` (Managing Python 3.12 isolated environments)
* **Local LLM Engine:** Ollama (`qwen2.5-coder:latest`)
* **Cloud LLM Engine:** Google AI Studio (`gemini-1.5-pro`, `gemini-1.5-flash`)
* **CLI Coding Agents:**
  * `aider-chat` (Integrated with local Ollama)
  * `opencode` (Integrated with Gemini APIs)

---

## 2. Environment Setup & Toolchain Installation

### Step 1: Install `uv` Package Manager
```powershell
pip install uv
```

### Step 2: Running Commands with `uv`
```powershell
# Run python commands or unit tests via uv in Python 3.12/3.13 environment:
uv run --python 3.12 python -m unittest discover -s tests -p "test_*.py"
```

---

## 3. Project Structure & Architecture Map

```
Shield-and-Sword/
├── README.md
├── Shield-and-Sword-runbook.md
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── models.py           # Core dataclasses: Transaction, EmailPayload, RiskEvaluation, RiskSeverity, RiskAction
│   ├── rules/
│   │   ├── __init__.py         # Public statistical rule API
│   │   ├── base.py             # Abstract rule interface
│   │   ├── engine.py           # Rule registration and score aggregation
│   │   └── transaction_rules.py # Deterministic transaction anomaly rules
│   ├── llm/
│   │   └── __init__.py         # Ollama & Gemini LLM agent wrappers
│   └── pipeline/
│       └── __init__.py         # Hybrid risk engine orchestration pipeline
└── tests/
    ├── __init__.py
    ├── test_models.py          # Unit tests for core data models
    └── test_rules.py           # Unit tests for transaction rules and engine
```

---

## 4. Change Log & Implementation Summary

### Initial Project Scaffolding & Core Models
* **Date:** 2026-10-04
* **Agent:** `opencode`

#### Files Created / Modified
* **`src/__init__.py`**: Package initialization file.
* **`src/core/__init__.py`**: Package initialization file.
* **`src/core/models.py`**:
  * Implemented `Transaction` dataclass with attributes: `transaction_id`, `user_id`, `amount`, `currency`, `timestamp` (UTC default), `ip_address`, `merchant_category`, `location`, with strict runtime type/value validation in `__post_init__`.
  * Implemented `EmailPayload` dataclass with attributes: `payload_id`, `sender`, `subject`, `body_text`, `headers` (dict), with header case-insensitive lookup helper (`header()`).
  * Implemented `RiskSeverity` string enum (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with `from_score(score: float)` mapping.
  * Implemented `RiskAction` string enum (`ALLOW`, `REVIEW`, `BLOCK`).
  * Implemented `RiskEvaluation` dataclass (`entity_id`, `rule_score`, `llm_score`, `final_score`, `action`, `triggered_rules`, `summary`) with score range validation (0-100), weighted score blending (`RULE_SCORE_WEIGHT = 0.6`), dynamic `severity` property, and `to_dict()` JSON-serializable output method.
* **`src/rules/__init__.py`**: Subpackage initializer for deterministic statistical rules.
* **`src/llm/__init__.py`**: Subpackage initializer for LLM integration modules.
* **`src/pipeline/__init__.py`**: Subpackage initializer for execution pipeline orchestration.
* **`tests/__init__.py`**: Test package initializer.
* **`tests/test_models.py`**: Standard library `unittest` test suite covering dataclass creation, validation checks, risk severity bounds, and score calculations. Passed 100%.

---

### Layer 1 Statistical Transaction Rule Engine
* **Date:** 2026-10-04
* **Agent:** Codex

#### Files Created / Modified
* **`src/rules/base.py`**: Added the abstract `BaseRule` contract and standardized rule result builder.
* **`src/rules/transaction_rules.py`**: Added configurable high-amount, high-risk-category, and suspicious-location/IP-CIDR rules. Jurisdiction matching uses caller-supplied exact labels and CIDRs; it does not perform geolocation.
* **`src/rules/engine.py`**: Added rule registration, result validation, triggered-rule detail collection, and a 0–100 aggregate score cap.
* **`src/rules/__init__.py`**: Exported the base interface, concrete rules, and engine.
* **`tests/test_rules.py`**: Added tests for clean and fraud-like transactions, threshold boundaries, case-insensitive categories, configured IP ranges, and duplicate registration. The standard-library unittest suite passed on Python 3.13 (12 tests).
* **`Shield-and-Sword-runbook.md`**: Updated the architecture map, implementation log, and Milestone 2 progress.

## 5. Project Milestones & Progress Tracker

- [x] **Milestone 1: Project Scaffolding & Core Data Models**
  - [x] Create project directory structure (`src/core`, `src/rules`, `src/llm`, `src/pipeline`, `tests`)
  - [x] Add package `__init__.py` files across all `src` subdirectories and `tests`
  - [x] Implement core models in `src/core/models.py` (`Transaction`, `EmailPayload`, `RiskSeverity`, `RiskAction`, `RiskEvaluation`)
  - [x] Write and verify unit test suite in `tests/test_models.py`
  - [x] Update `Shield-and-Sword-runbook.md` with implementation log & structure map

- [ ] **Milestone 2: Statistical Rule Engine (`src/rules/`)**
  - [x] Implement deterministic rule base for transaction anomaly detection
  - [ ] Implement email header and text keyword heuristic rule layer
  - [x] Write unit tests for rule layer evaluation

- [ ] **Milestone 3: Local & Cloud LLM Integration (`src/llm/`)**
  - [ ] Implement Ollama client wrapper for local offline inference (`qwen2.5-coder`)
  - [ ] Implement Gemini API client wrapper for cloud synthesis (`gemini-1.5-pro` / `gemini-1.5-flash`)
  - [ ] Build structured prompt templates for payload analysis

- [ ] **Milestone 4: Hybrid Risk Pipeline (`src/pipeline/`)**
  - [ ] Implement pipeline orchestrator combining rule scores and LLM scores
  - [ ] Define disposition logic (`ALLOW`, `REVIEW`, `BLOCK`)
  - [ ] Integration testing across rules, LLMs, and pipeline
