import argparse
import json
import os
import time
from collections import Counter
from datetime import datetime

from openai import OpenAI


LOG_LEVELS = {"ERROR", "CRITICAL"}
LOG_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

REQUIRED_FIELDS = {
    "severity",
    "likely_cause",
    "suggested_action",
    "needs_human",
}

VALID_SEVERITIES = {"low", "medium", "high"}

CACHE_FILE = ".triage_cache.json"


def parse_log_file(log_file):
    error_counts = Counter()

    with open(log_file, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            parts = line.split(maxsplit=3)

            if len(parts) != 4:
                continue

            date = parts[0]
            time_part = parts[1]
            level = parts[2]
            message = parts[3]

            timestamp = f"{date} {time_part}"

            try:
                datetime.strptime(timestamp, LOG_TIMESTAMP_FORMAT)
            except ValueError:
                continue

            if level not in LOG_LEVELS:
                continue

            error_counts[message] += 1

    return error_counts


def validate_result(result):
    try:
        data = json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None

    if set(data.keys()) != REQUIRED_FIELDS:
        return None

    if data["severity"] not in VALID_SEVERITIES:
        return None

    if not isinstance(data["likely_cause"], str):
        return None

    if not isinstance(data["suggested_action"], str):
        return None

    if not isinstance(data["needs_human"], bool):
        return None

    return data


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

    except (json.JSONDecodeError, OSError):
        print(
            "Warning: Cache file could not be read. "
            "Starting with empty cache."
        )

    return {}


def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(cache, file, indent=2)

    except OSError as error:
        print(f"Warning: Could not save cache: {error}")


def ask_model(client, message, count):
    prompt = f"""
You are an experienced software operations engineer.

Analyze this log error and return a triage judgement.

Error message:
{message}

Occurrence count:
{count}

Return ONLY valid JSON with exactly these four fields:

{{
  "severity": "low" | "medium" | "high",
  "likely_cause": "one sentence",
  "suggested_action": "one sentence",
  "needs_human": true | false
}}

Do not include Markdown, code fences, explanations, or any other fields.
"""

    # Initial attempt + 3 retries.
    # Wait 1 second, then 2 seconds, then 4 seconds.
    retry_delays = [1, 2, 4]

    for attempt in range(4):
        try:
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a software log triage assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    },
                ],
            )

            result = response.choices[0].message.content

            validated_result = validate_result(result)

            if validated_result is None:
                print(
                    "Model returned invalid JSON or is missing "
                    "one or more required fields."
                )
                return None

            return validated_result

        except Exception as error:
            if attempt == 3:
                raise error

            delay = retry_delays[attempt]

            print(
                f"API call failed (attempt {attempt + 1}/4). "
                f"Retrying in {delay} seconds..."
            )

            time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(
        description="AI Log Triage Assistant"
    )

    parser.add_argument(
        "log_file",
        help="Path to the log file"
    )

    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of top errors to triage (default: 3)"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore cached results and call the API again"
    )

    args = parser.parse_args()

    if args.top <= 0:
        parser.error("--top must be greater than 0")

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print(
            "Error: OPENAI_API_KEY is not set. "
            "Please set the OPENAI_API_KEY environment variable "
            "before running the AI triage."
        )
        return

    client = OpenAI(api_key=api_key)

    try:
        error_counts = parse_log_file(args.log_file)
    except FileNotFoundError:
        print(f"Error: File '{args.log_file}' not found.")
        return
    except OSError as error:
        print(f"Error reading '{args.log_file}': {error}")
        return

    top_errors = error_counts.most_common(args.top)

    if not top_errors:
        print("No ERROR or CRITICAL entries found.")
        return

    cache = load_cache()

    api_calls = 0
    cache_hits = 0

    results = []

    for message, count in top_errors:

        if not args.no_cache and message in cache:
            result = cache[message]
            cache_hits += 1

        else:
            try:
                result = ask_model(client, message, count)
                api_calls += 1

                if result is not None:
                    cache[message] = result
                    save_cache(cache)

            except Exception as error:
                result = None
                api_calls += 1
                print(f"\nAI error for {message}: {error}")

        results.append((message, count, result))

    # Group results by severity.
    severity_order = ["high", "medium", "low"]

    grouped_results = {
        severity: []
        for severity in severity_order
    }

    unavailable_results = []

    for message, count, result in results:
        if result is None:
            unavailable_results.append((message, count))
        else:
            grouped_results[result["severity"]].append(
                (message, count, result)
            )

    print(
        f"\nTriage report: {args.log_file} "
        f"({len(error_counts)} unique errors, top {len(top_errors)} shown)"
    )

    for severity in severity_order:
        severity_results = grouped_results[severity]

        if not severity_results:
            continue

        print(f"\n{severity.upper()}")

        for message, count, result in severity_results:
            print(f"  {message}    {count} occurrences")
            print(f"    Likely cause: {result['likely_cause']}")
            print(f"    Action: {result['suggested_action']}")
            print(
                f"    Needs human: "
                f"{'yes' if result['needs_human'] else 'no'}"
            )

    if unavailable_results:
        print("\nUNAVAILABLE")

        for message, count in unavailable_results:
            print(f"  {message}    {count} occurrences")
            print("    AI result unavailable.")

    print(f"\nAPI calls: {api_calls}")
    print(f"From cache: {cache_hits}")


if __name__ == "__main__":
    main()