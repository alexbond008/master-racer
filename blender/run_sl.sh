#!/bin/sh
# usage: ./run_sl.sh build_x.py
cd "$(dirname "$0")" && /opt/homebrew/bin/blender -b --python "$1" 2>&1 | grep -E "^\[|Error|Traceback|line [0-9]+|Exception"
