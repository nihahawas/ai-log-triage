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
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Set the API key

The application reads the API key from the `OPENAI_API_KEY` environment variable.

PowerShell:

```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

The API key should never be placed directly in the source code or committed to GitHub.

To verify that the variable is set without displaying the key:

```powershell
if ($env:OPENAI_API_KEY) { Write-Host "API key is set" } else { Write-Host "API key is not set" }
```

## Usage

Run the application with the default top 3 errors:

```powershell
python triage.py app.log
```

Analyze the top 5 errors:

```powershell
python triage.py app.log --top 5
```

Bypass the cache and call the API again:

```powershell
python triage.py app.log --no-cache
```

## How It Works

1. The log file is parsed and `ERROR` and `CRITICAL` entries are identified.
2. Identical error messages are grouped and counted.
3. The most frequent errors are selected. The default is 3.
4. Each unique error and its occurrence count are sent to the language model.
5. The model is asked to return exactly four JSON fields:
   - `severity`
   - `likely_cause`
   - `suggested_action`
   - `needs_human`
6. The response is validated before being used.
7. Results are grouped by severity, with HIGH shown first.
8. Successful results are stored in `.triage_cache.json`.
9. The report displays the number of API calls and cache hits.

## Caching

Successful AI results are stored locally in:

```text
.triage_cache.json
```

When the same error message is encountered again, the cached result is used instead of making another API call.

This reduces unnecessary API usage and makes repeated runs faster.

To bypass the cache:

```powershell
python triage.py app.log --no-cache
```

The cache file is excluded from Git using `.gitignore`.

## Error Handling

The application handles several failure cases:

### Missing API key

If `OPENAI_API_KEY` is not set, the program prints a clear error message and exits without attempting an API call.

### API failure

Failed API requests are retried with increasing delays:

```text
1 second
2 seconds
4 seconds
```

If all attempts fail, that error is reported as unavailable and processing continues for the remaining errors.

### Invalid model response

If the model returns invalid JSON or does not contain exactly the required fields, the result is treated as unavailable instead of crashing the application.

### Missing log file

If the specified log file does not exist, the program prints an error message and exits cleanly.

## Example Output

A successful run produces a report similar to:

```text
Triage report: app.log (8 unique errors, top 3 shown)

HIGH
  DatabaseTimeout: connection lost    18 occurrences
    Likely cause: Connection pool exhausted under load.
    Action: Check pool size and database health.
    Needs human: yes

MEDIUM
  PaymentGateway: request timed out    12 occurrences
    Likely cause: Upstream provider latency or throttling.
    Action: Check provider status and review timeout settings.
    Needs human: no

LOW
  ValidationError: missing field "amount"    7 occurrences
    Likely cause: A required request field was not provided.
    Action: Validate the request payload before processing.
    Needs human: no

API calls: 3
From cache: 0
```

When the API is unavailable, the application continues and reports unavailable results:

```text
UNAVAILABLE
  DatabaseTimeout: connection lost    18 occurrences
    AI result unavailable.

API calls: 3
From cache: 0
```

## Testing

The application was tested against the required failure and usage scenarios.

### Normal execution

```powershell
python triage.py app.log
```

The application parsed the log, selected the top 3 errors, attempted AI triage, and produced a final report.

### Top N option

```powershell
python triage.py app.log --top 5
```

The application correctly displayed the top 5 errors.

### No-cache option

```powershell
python triage.py app.log --no-cache
```

The application bypassed the local cache and attempted fresh API calls.

### API failure

The API returned a `429 insufficient_quota` response during testing. The application:

- Retried failed requests
- Waited 1, 2, and 4 seconds between attempts
- Marked failed results as unavailable
- Continued processing without crashing
- Printed the API call count

This confirmed that API failure handling works as intended.

### Cache protection

The cache file is excluded from version control through `.gitignore`.

## Project Structure

```text
ai-log-triage/
├── triage.py
├── requirements.txt
├── README.md
├── .gitignore
└── app.log
```

`app.log` is used as a local test log file and is excluded from Git.

## Dependencies

The project uses the OpenAI Python SDK.

Dependencies are listed in:

```text
requirements.txt
```

Install them with:

```powershell
pip install -r requirements.txt
```

## Security

The API key is loaded from the `OPENAI_API_KEY` environment variable.

The following files are excluded from Git:

```text
.env
.triage_cache.json
```

API keys must never be committed to the repository or included directly in source code.

## Author

Niha Hawas

GitHub: https://github.com/nihahawas