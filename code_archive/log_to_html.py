#!/usr/bin/env python3
"""
Taki Game Log to HTML Converter with Syntax Highlighting

This script converts Taki game log files (.log) to HTML with perfect
syntax highlighting that works in any web browser.

Usage:
    python log_to_html.py taki_game_06_12_2024-15_11_16.log
    
    # Or process all log files in current directory:
    python log_to_html.py

Output:
    Creates .html files with the same name as input .log files
    Open the HTML file in any browser to see highlighted logs!
"""

import re
import sys
import glob
from pathlib import Path
from html import escape

# Color scheme matching Notepad++ theme
COLORS = {
    'timestamp': '#FF8000',      # Orange
    'bpevent': '#8000FF',        # Purple
    'error': '#FF0000',          # Red
    'error_bg': '#FFE6E6',       # Light red background
    'debug': '#0000FF',          # Blue
    'player': '#008000',         # Green
    'player_bg': '#E6FFE6',      # Light green background
    'tag': '#FF00FF',            # Magenta
    'color': '#FF0080',          # Pink
    'card': '#804000',           # Brown
    'action': '#008080',         # Cyan
    'number': '#FF8000',         # Orange
    'done_post_action': '#FF6600',   # Dark Orange (Action completion)
    'done_post_action_bg': '#FFF0E6',  # Light orange background
    'next_turn': '#9932CC',          # Dark Orchid (Turn transition)
    'next_turn_bg': '#F0E6FF',       # Light purple background
    'draw_card': '#DC143C',          # Crimson Red (Draw action)
    'draw_card_bg': '#FFE6E6',       # Light red background
    'no_more_cards': '#FF1493',      # Deep Pink (Game ending)
    'no_more_cards_bg': '#FFE6F5',   # Light pink background
}

def highlight_line(line):
    """
    Apply syntax highlighting to a single log line.
    
    Args:
        line: Raw log line text
        
    Returns:
        HTML-formatted line with color spans
    """
    # Escape HTML characters first
    line = escape(line)
    
    # 1. Timestamp - HH:MM:SS.mmm - Orange Bold
    line = re.sub(
        r'(\d{2}:\d{2}:\d{2}\.\d{3})',
        rf'<span style="color:{COLORS["timestamp"]};font-weight:bold">\1</span>',
        line
    )
    
    # 2. BPEvent(...) - Purple Bold
    line = re.sub(
        r'(BPEvent\([^)]+\))',
        rf'<span style="color:{COLORS["bpevent"]};font-weight:bold">\1</span>',
        line
    )
    
    # 3. ERROR/WARNING/CRITICAL - Red Bold with Background
    line = re.sub(
        r'\b(ERROR|WARNING|CRITICAL|FAILED)\b',
        rf'<span style="color:{COLORS["error"]};background:{COLORS["error_bg"]};font-weight:bold;padding:2px 4px">\1</span>',
        line
    )
    
    # 4. DEBUG/INFO - Blue Bold
    line = re.sub(
        r'\b(DEBUG|INFO|STARTED|ENDED)\b',
        rf'<span style="color:{COLORS["debug"]};font-weight:bold">\1</span>',
        line
    )
    
    # 5. Player IDs - Green Bold with Background
    line = re.sub(
        r'\b(p_[01]_\w+|PLAYER_[01])\b',
        rf'<span style="color:{COLORS["player"]};background:{COLORS["player_bg"]};font-weight:bold;padding:1px 3px">\1</span>',
        line
    )
    
    # 6. Log Tags [RULES], [PENALTY], etc - Magenta Bold
    line = re.sub(
        r'(\[(?:RULES|PLAYER_\d|ENFORCE_TURNS|PENALTY[^\]]*|TAKI_BLOCK|PLACEMENT_CHECK|DEBUG|PLUS2|ANNOUNCE)\])',
        rf'<span style="color:{COLORS["tag"]};font-weight:bold">\1</span>',
        line
    )
    
    # 7. Card Colors - Pink Bold
    line = re.sub(
        r'\b(red|blue|green)\b',
        rf'<span style="color:{COLORS["color"]};font-weight:bold">\1</span>',
        line
    )
    
    # 8. Card Types - Brown
    line = re.sub(
        r'\b(card_[0-9]|taki|super_taki|stop|plus_2|change_color|TAKI|STOP|PLUS_2|CHANGE_COLOR)\b',
        rf'<span style="color:{COLORS["card"]}">\1</span>',
        line
    )
    
    # 9. done_post_action - Dark Orange with Background
    line = re.sub(
        r'\b(done_post_action)\b',
        rf'<span style="color:{COLORS["done_post_action"]};background:{COLORS["done_post_action_bg"]};font-weight:bold;padding:2px 4px">\1</span>',
        line
    )
    
    # 10. next_turn - Dark Orchid with Background
    line = re.sub(
        r'\b(next_turn)\b',
        rf'<span style="color:{COLORS["next_turn"]};background:{COLORS["next_turn_bg"]};font-weight:bold;padding:2px 4px">\1</span>',
        line
    )
    
    # 11. draw_card - Crimson Red with Background
    line = re.sub(
        r'\b(draw_card)\b',
        rf'<span style="color:{COLORS["draw_card"]};background:{COLORS["draw_card_bg"]};font-weight:bold;padding:2px 4px">\1</span>',
        line
    )
    
    # 12. no_more_cards - Deep Pink with Background
    line = re.sub(
        r'\b(no_more_cards)\b',
        rf'<span style="color:{COLORS["no_more_cards"]};background:{COLORS["no_more_cards_bg"]};font-weight:bold;padding:2px 4px">\1</span>',
        line
    )
    
    # 13. Special Actions - Cyan Bold
    line = re.sub(
        r'\b(SEQUENCE|STARTING|ENDING|closed_taki)\b',
        rf'<span style="color:{COLORS["action"]};font-weight:bold">\1</span>',
        line
    )
    
    # 14. Priority and other numbers - Orange
    line = re.sub(
        r'\bpriority=(\d+\.?\d*)\b',
        rf'priority=<span style="color:{COLORS["number"]};font-weight:bold">\1</span>',
        line
    )
    
    return line

def convert_log_to_html(log_file):
    """
    Convert a log file to HTML with syntax highlighting.
    
    Args:
        log_file: Path to .log file
        
    Returns:
        Path to created .html file
    """
    log_path = Path(log_file)
    html_path = log_path.with_suffix('.html')
    
    # Read log file
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {log_file}: {e}")
        return None
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{log_path.name} - Taki Game Log</title>
    <style>
        body {{
            background: #FFFFFF;
            color: #000000;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10pt;
            margin: 20px;
            line-height: 1.4;
        }}
        pre {{
            margin: 0;
            padding: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .header {{
            background: #F0F0F0;
            padding: 10px;
            border: 1px solid #CCC;
            margin-bottom: 10px;
            font-family: Arial, sans-serif;
        }}
        .stats {{
            font-size: 9pt;
            color: #666;
            margin-top: 5px;
        }}
        .legend {{
            background: #F9F9F9;
            padding: 10px;
            border: 1px solid #DDD;
            margin-bottom: 10px;
            font-size: 9pt;
            font-family: Arial, sans-serif;
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 15px;
            margin-bottom: 5px;
        }}
        .legend-color {{
            display: inline-block;
            width: 12px;
            height: 12px;
            margin-right: 3px;
            vertical-align: middle;
            border: 1px solid #999;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🎴 Taki Game Log: {log_path.name}</h2>
        <div class="stats">
            Lines: {len(lines)} | Generated from: {log_path.absolute()}
        </div>
    </div>
    
    <div class="legend">
        <strong>Color Legend:</strong><br>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['timestamp']}"></span>
            <span style="color:{COLORS['timestamp']};font-weight:bold">Timestamp</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['bpevent']}"></span>
            <span style="color:{COLORS['bpevent']};font-weight:bold">BPEvent</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['error']}"></span>
            <span style="color:{COLORS['error']};font-weight:bold">Error/Warning</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['player']}"></span>
            <span style="color:{COLORS['player']};font-weight:bold">Players</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['tag']}"></span>
            <span style="color:{COLORS['tag']};font-weight:bold">Tags</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['color']}"></span>
            <span style="color:{COLORS['color']};font-weight:bold">Colors</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['card']}"></span>
            <span style="color:{COLORS['card']}">Cards</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['done_post_action']}"></span>
            <span style="color:{COLORS['done_post_action']};font-weight:bold">done_post_action</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['next_turn']}"></span>
            <span style="color:{COLORS['next_turn']};font-weight:bold">next_turn</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['draw_card']}"></span>
            <span style="color:{COLORS['draw_card']};font-weight:bold">draw_card</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['no_more_cards']}"></span>
            <span style="color:{COLORS['no_more_cards']};font-weight:bold">no_more_cards</span>
        </span>
        <span class="legend-item">
            <span class="legend-color" style="background:{COLORS['action']}"></span>
            <span style="color:{COLORS['action']};font-weight:bold">Actions</span>
        </span>
    </div>
    
    <pre>"""
    
    # Process each line
    for line in lines:
        html += highlight_line(line)
    
    html += """</pre>
</body>
</html>"""
    
    # Write HTML file
    try:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return html_path
    except Exception as e:
        print(f"Error writing {html_path}: {e}")
        return None

def main():
    """Main entry point"""
    print("=" * 70)
    print("Taki Game Log to HTML Converter with Syntax Highlighting")
    print("=" * 70)
    
    # Get input files
    if len(sys.argv) > 1:
        # Process specified files
        log_files = sys.argv[1:]
    else:
        # Process all .log files in current directory
        log_files = glob.glob("*.log")
        if not log_files:
            print("\nNo .log files found in current directory.")
            print("\nUsage:")
            print("  python log_to_html.py <logfile.log>")
            print("  python log_to_html.py                  # Converts all .log files")
            return
    
    print(f"\nFound {len(log_files)} log file(s) to convert:\n")
    
    # Convert each file
    converted = 0
    for log_file in log_files:
        print(f"Converting: {log_file}...", end=" ")
        html_file = convert_log_to_html(log_file)
        if html_file:
            print(f"✓ Created: {html_file}")
            converted += 1
        else:
            print("✗ FAILED")
    
    print("\n" + "=" * 70)
    print(f"Conversion complete! {converted}/{len(log_files)} files converted.")
    print("=" * 70)
    print("\n💡 TIP: Open the .html files in your web browser to view highlighted logs!")
    print("       Right-click the .html file → Open with → Your favorite browser")
    print("\n✨ Perfect syntax highlighting with searchable text!")

if __name__ == "__main__":
    main()