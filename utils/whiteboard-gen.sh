#!/usr/bin/env bash
# whiteboard-gen.sh — turn a diagram CONTENT description into a photoreal
# glass-whiteboard illustration (the "Karpathy board" style) via Nano Banana.
#
# The STYLE preamble below is LOCKED — it encodes the look we settled on
# (glass board, black marker, hand-drawn icons, disciplined accents). You only
# supply the CONTENT (what to draw). See the CONTENT-GUIDE.md that ships beside
# this script in the consuming repo's whiteboard-generation skill for how to
# author good CONTENT (xact.ai: .claude/skills/whiteboard-generation/).
#
# Usage:
#   export GEMINI_API_KEY=...            # or have ~/.gemini_key present
#   ./whiteboard-gen.sh CONTENT_FILE [OUT.jpg]
#   ./whiteboard-gen.sh - [OUT.jpg]      # read CONTENT from stdin
#
# Env:
#   GEMINI_MODEL   default gemini-3-pro-image (Nano Banana Pro — best text/icons).
#                  Fallbacks: gemini-2.5-flash-image (cheaper, garbles dense text).
#
# Requires: curl, jq, base64
set -euo pipefail

CONTENT_FILE="${1:?Usage: whiteboard-gen.sh CONTENT_FILE [OUT.jpg]  (use - for stdin)}"
OUT="${2:-whiteboard.jpg}"
MODEL="${GEMINI_MODEL:-gemini-3-pro-image}"

# --- API key: env var, else ~/.gemini_key (line "GEMINI_API_KEY=...") ---
if [ -z "${GEMINI_API_KEY:-}" ] && [ -f "$HOME/.gemini_key" ]; then
  set -a; . "$HOME/.gemini_key"; set +a
fi
: "${GEMINI_API_KEY:?Set GEMINI_API_KEY or create ~/.gemini_key (https://aistudio.google.com/apikey)}"

# --- read the variable CONTENT ---
if [ "$CONTENT_FILE" = "-" ]; then CONTENT="$(cat)"; else CONTENT="$(cat "$CONTENT_FILE")"; fi
[ -n "$CONTENT" ] || { echo "CONTENT is empty" >&2; exit 1; }

# --- LOCKED STYLE PREAMBLE (do not edit casually; this is the house style) ---
read -r -d '' STYLE <<'EOF' || true
A photorealistic photograph of a real glass whiteboard mounted on a plain light
wall, held by four brushed-metal standoff bolts at the corners, with a soft,
subtle glass reflection (not a bright window glare). The glass has a faint cool
mint tint.

STYLE — the most important part. Everything is drawn BY HAND in black dry-erase
marker, in the confident, even, slightly imperfect PRINTING of a skilled software
architect: consistent thin-to-medium line weight, hand-drawn (slightly wobbly)
rectangles and arrows with small hand-drawn triangular arrowheads, and simple
black line-art ICONS next to the elements. NOT a rounded cartoon / Comic-Sans
font, NOT digitally perfect shapes — it must look genuinely marker-drawn by a
person. Lettering: the title in neat mixed-case Title Case, section labels in
block CAPITALS, small detail labels in lowercase. Render every word accurately,
correctly spelled, well spaced.

COLOR is used sparingly, for meaning only — about 90% of the board is black
marker. Reserve each accent colour for exactly ONE meaning and use no more than
three accents total (typically: BLUE for the main forward flow, TEAL for a
skip/branch path, ORANGE for a loop or back-edge). No decorative colour, and no
ornamental "hero" object that does not carry meaning.

Landscape 16:9, a balanced composition that fills the board, uncluttered, with
generous spacing.

Now draw this specific diagram:
EOF

CLOSER="Keep the palette disciplined and the marker handwriting neat and legible; give each component a small hand-drawn icon; spell every word correctly."

PROMPT="${STYLE}

${CONTENT}

${CLOSER}"

echo "Model: $MODEL  →  $OUT"
RESP=$(curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/interactions" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg m "$MODEL" --arg p "$PROMPT" '{
        model: $m,
        input: [ {type:"text", text:$p} ],
        response_format: { type:"image", mime_type:"image/jpeg", aspect_ratio:"16:9", image_size:"2K" }
      }')")

DATA=$(printf '%s' "$RESP" | jq -r '
  (.steps[]?.content[]? | select(.type=="image" or .data!=null) | .data)
  // .output_image.data
  // (.candidates[]?.content.parts[]? | .inlineData.data // .inline_data.data)
  // empty' | head -n1)

if [ -z "${DATA:-}" ]; then
  echo "No image in response. Raw JSON (first 2KB) so you can adjust the jq path or read the error:" >&2
  printf '%s\n' "$RESP" | head -c 2000 >&2
  exit 1
fi

printf '%s' "$DATA" | base64 -d > "$OUT"
echo "Wrote $OUT ($(wc -c < "$OUT") bytes)"
