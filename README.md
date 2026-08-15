# AI Log Triage Assistant

A Python command-line tool that analyzes application logs, finds the most frequent `ERROR` and `CRITICAL` messages, and uses a language model to generate a triage report.

## Features

- Parses `ERROR` and `CRITICAL` log entries
- Groups identical error messages by frequency
- Supports selecting the top N errors with `--top`
- Sends unique errors and their occurrence counts to the OpenAI API
- Returns severity, likely cause, suggested action, and whether human review is needed
- Retries failed API calls with increasing delays
- Handles missing API keys without crashing
- Handles API failures without stopping the whole run
- Handles invalid JSON or incomplete model responses
- Caches successful AI results locally to avoid repeated API calls
- Supports `--no-cache` to bypass the cache
- Groups results by severity: HIGH, MEDIUM, LOW
- Reports API calls and cached results at the end of every run

## Requirements

- Python 3.12 or later
- OpenAI API key

## Setup

### 1. Clone the repository

```powershell
git clone https://github.com/nihahawas/ai-log-triage.git
cd ai-log-triage