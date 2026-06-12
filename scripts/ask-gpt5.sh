#!/bin/bash
# Ask GPT-5 via webchat2api for expert guidance
# Usage: bash ask-gpt5.sh "Your question or prompt"
# Model can be overridden with 2nd arg: gpt-5, gpt-5-5, gpt-5-5-thinking

PROMPT="$1"
MODEL="${2:-gpt-5}"

curl -s -X POST http://127.0.0.1:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-api-key: ***" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"$PROMPT\"}
    ]
  }" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['choices'][0]['message']['content'])
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
"
