#!/bin/bash
#
# Playback multiple rig recordings simultaneously
# Usage: ./playback_all_rigs.sh <recording_directory> [speed] [--loop]
#

if [ "$#" -lt 1 ]; then
    echo "Usage: ./playback_all_rigs.sh <recording_directory> [speed] [--loop]"
    echo ""
    echo "Examples:"
    echo "  ./playback_all_rigs.sh recordings/lan_session"
    echo "  ./playback_all_rigs.sh recordings/lan_session 2.0"
    echo "  ./playback_all_rigs.sh recordings/lan_session 1.0 --loop"
    exit 1
fi

RECORDING_DIR="$1"
SPEED="${2:-1.0}"
LOOP_FLAG=""

if [ "$3" = "--loop" ]; then
    LOOP_FLAG="--loop"
fi

# Find recording files
RIG_A_FILE=$(ls "$RECORDING_DIR"/rig_port20777_*.packets 2>/dev/null | head -n 1)
RIG_B_FILE=$(ls "$RECORDING_DIR"/rig_port20778_*.packets 2>/dev/null | head -n 1)

if [ -z "$RIG_A_FILE" ] && [ -z "$RIG_B_FILE" ]; then
    echo "❌ No recording files found in $RECORDING_DIR"
    echo "   Looking for: rig_port20777_*.packets or rig_port20778_*.packets"
    exit 1
fi

echo "🎬 Playing back recordings from: $RECORDING_DIR"
echo "⚡ Speed: ${SPEED}x"
if [ -n "$LOOP_FLAG" ]; then
    echo "🔁 Loop: enabled"
fi
echo ""

# Start playback processes
PIDS=()

if [ -n "$RIG_A_FILE" ]; then
    echo "▶️  Starting RIG A playback: $(basename "$RIG_A_FILE")"
    python3 scripts/playback_udp_packets.py --input "$RIG_A_FILE" --port 20777 --speed "$SPEED" $LOOP_FLAG &
    PIDS+=($!)
fi

if [ -n "$RIG_B_FILE" ]; then
    echo "▶️  Starting RIG B playback: $(basename "$RIG_B_FILE")"
    python3 scripts/playback_udp_packets.py --input "$RIG_B_FILE" --port 20778 --speed "$SPEED" $LOOP_FLAG &
    PIDS+=($!)
fi

echo ""
echo "✅ Playback started for ${#PIDS[@]} rig(s)"
echo "📊 View dashboard at: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop playback"

# Handle Ctrl+C
trap 'echo ""; echo "⏹️  Stopping playback..."; for pid in ${PIDS[@]}; do kill $pid 2>/dev/null; done; exit 0' INT TERM

# Wait for all processes
wait
