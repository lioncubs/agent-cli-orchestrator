#!/bin/bash
# Export Mermaid diagrams to PNG format
# Requires: npm install -g @mermaid-js/mermaid-cli

set -e

MERMAID_DIR="docs/diagrams/mermaid"
PNG_DIR="docs/diagrams/png"

# Create PNG directory if it doesn't exist
mkdir -p "$PNG_DIR"

echo "🎨 Exporting Mermaid diagrams to PNG..."
echo "========================================="

# Check if mmdc is installed
if ! command -v mmdc &> /dev/null; then
    echo "❌ Error: mermaid-cli (mmdc) is not installed"
    echo ""
    echo "To install, run:"
    echo "  npm install -g @mermaid-js/mermaid-cli"
    echo ""
    echo "Or using npx (no installation needed):"
    echo "  npx -p @mermaid-js/mermaid-cli mmdc --version"
    exit 1
fi

# Count total diagrams
total_files=$(find "$MERMAID_DIR" -name "*.mmd" | wc -l)
current=0

# Export each .mmd file to PNG
for file in "$MERMAID_DIR"/*.mmd; do
    if [ -f "$file" ]; then
        current=$((current + 1))
        filename=$(basename "$file" .mmd)
        
        echo "[$current/$total_files] Exporting: $filename.mmd"
        
        # Export with transparent background and 2x scale for high resolution
        mmdc -i "$file" \
             -o "$PNG_DIR/$filename.png" \
             -s 2 \
             -b transparent \
             -t neutral
        
        echo "  ✅ Created: $PNG_DIR/$filename.png"
    fi
done

echo ""
echo "========================================="
echo "✨ Successfully exported $total_files diagrams!"
echo ""
echo "📁 Output directory: $PNG_DIR"
echo ""
echo "Exported diagrams:"
ls -lh "$PNG_DIR"/*.png 2>/dev/null || echo "  (No PNG files found - check for errors above)"
