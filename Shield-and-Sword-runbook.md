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