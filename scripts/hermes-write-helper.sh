#!/bin/bash
# hermes-write-helper.sh
# Usage: hermes-write-helper.sh <path> <content_as_base64>
# Decodes base64 content and writes to file. No heredoc issues.
# Works with ANY content including thinking tags, backslashes, unicode.

PATH_ARG="$1"
B64_CONTENT="$2"
MODE="${3:-w}"  # w=overwrite, a=append

if [[ -z "$PATH_ARG" ]] || [[ -z "$B64_CONTENT" ]]; then
    echo "Usage: hermes-write-helper.sh <path> <base64_content> [w|a]"
    exit 1
fi

# Create parent directory
mkdir -p "$(dirname "$PATH_ARG")"

# Decode and write
if [[ "$MODE" == "a" ]]; then
    echo "$B64_CONTENT" | base64 -d >> "$PATH_ARG"
else
    echo "$B64_CONTENT" | base64 -d > "$PATH_ARG"
fi

SIZE=$(wc -c < "$PATH_ARG")
echo "Wrote ${SIZE} bytes to ${PATH_ARG}"
