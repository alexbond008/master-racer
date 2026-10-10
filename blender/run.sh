#!/bin/bash
# usage: run.sh <id> [views...]   (builds build_<id>.py then renders previews)
cd "$(dirname "$0")"
id=$1; shift
blender -b --python build_$id.py 2>&1 | grep -E "tris|exported|Error|Traceback|File|rror" 
blender -b --python mr_preview.py -- $id "$@" 2>&1 | grep -E "IMPORTED|OBJECTS|MATS|Error|Traceback"
