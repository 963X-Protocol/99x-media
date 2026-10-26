#!/usr/bin/env bash
# One-time setup on a fresh machine. Safe to re-run.
set -e
cd "$(dirname "$0")"
python3 -c "import kokoro_onnx, soundfile, scipy, playwright" 2>/dev/null || \
  pip install --quiet --break-system-packages kokoro-onnx soundfile scipy playwright
mkdir -p models
base=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -s models/kokoro-v1.0.onnx ] || curl -sSL -o models/kokoro-v1.0.onnx "$base/kokoro-v1.0.onnx"
[ -s models/voices-v1.0.bin ]  || curl -sSL -o models/voices-v1.0.bin  "$base/voices-v1.0.bin"
ls -la models
echo "setup ok"
