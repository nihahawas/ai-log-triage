import argparse
from collections import Counter
from datetime import datetime


LOG_LEVELS = {"ERROR", "CRITICAL"}
LOG_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


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
            time = parts[1]
            level = parts[2]
            message = parts[3]

            timestamp = f"{date} {time}"

            # Validate timestamp.
            try:
                datetime.strptime(timestamp, LOG_TIMESTAMP_FORMAT)
            except ValueError:
                continue

            # Validate log level.
            if level not in LOG_LEVELS:
                continue

            error_counts[message] += 1

    return error_counts


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

    args = parser.parse_args()

    if args.top <= 0:
        parser.error("--top must be greater than 0")

    try:
        error_counts = parse_log_file(args.log_file)
    except FileNotFoundError:
        print(f"Error: File '{args.log_file}' not found.")
        return
    except OSError as error:
        print(f"Error reading '{args.log_file}': {error}")
        return

    top_errors = error_counts.most_common(args.top)

    print("Top Errors:")

    if not top_errors:
        print("No ERROR or CRITICAL entries found.")
        return

    for message, count in top_errors:
        print(f"{count}x {message}")


if __name__ == "__main__":
    main()