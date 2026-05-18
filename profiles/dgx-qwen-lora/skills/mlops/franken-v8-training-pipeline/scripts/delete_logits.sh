#!/bin/bash
# Delete batch logits after training to free disk space
# Usage: ./delete_logits.sh batch_1|batch_2|batch_3

BATCH=$1

if [ -z "$BATCH" ]; then
    echo "Usage: $0 batch_1|batch_2|batch_3"
    exit 1
fi

LOGITS_DIR="/data/SpecForge/custom_dflash/${BATCH}_logits"

if [ ! -d "$LOGITS_DIR" ]; then
    echo "Directory $LOGITS_DIR does not exist"
    exit 1
fi

# Get size before delete
SIZE=$(du -sh "$LOGITS_DIR" | cut -f1)
FILE_COUNT=$(ls "$LOGITS_DIR"/*.pt 2>/dev/null | wc -l)

echo "Deleting $BATCH logits..."
echo "  Directory: $LOGITS_DIR"
echo "  Size: $SIZE"
echo "  Files: $FILE_COUNT"

# Safety: only delete .pt files, not the directory itself
rm -rf "$LOGITS_DIR"/*.pt
rmdir "$LOGITS_DIR" 2>/dev/null

echo "Done! Freed ~$SIZE"
echo ""
df -h /data | grep -v Filesystem
