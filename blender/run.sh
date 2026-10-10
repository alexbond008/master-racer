#!/bin/bash
# usage: ./run.sh <id> [views]   -> builds <id>.py and renders previews
cd ~/Projects/master-racer/blender
/opt/homebrew/bin/blender -b --python $1.py 2>&1 | grep -E "TRIANGLES|Error|error|Traceback|File \"|exported|decal|Warn"
/opt/homebrew/bin/blender -b --python small_cars_preview.py -- $1 ${2:-front34,rear34,side,top} 2>&1 | grep -E "SIZE|TRIS|BBOX"
