#!/usr/bin/env python3
"""
CAPABILITY REGISTRY v2.0 — The Limitless Edition
Unified router mapping 200+ capabilities across 10 domains.

Usage:
  python3 capability_registry.py list              — list all capabilities
  python3 capability_registry.py search <query>    — search by keyword
  python3 capability_registry.py run <cap_id> [args] — execute a capability
  python3 capability_registry.py stats             — capability statistics
  python3 capability_registry.py status            — system readiness check
"""

import sys
import json
import time
import subprocess
import os
from pathlib import Path

BASE = str(Path(__file__).parent / "capabilities")
PY = "/Users/dannygomez/hermes-agent/venv/bin/python3"

CAPABILITIES = {
    # ═══════════════════════════════════════════════════════════════
    # DESKTOP CONTROL (20 caps)
    # ═══════════════════════════════════════════════════════════════
    "mouse_move": {"script": "desktop_control.py", "cmd": "mouse_move", "category": "desktop", "desc": "Move mouse to coordinates"},
    "mouse_click": {"script": "desktop_control.py", "cmd": "click", "category": "desktop", "desc": "Click mouse button"},
    "mouse_drag": {"script": "desktop_control.py", "cmd": "drag", "category": "desktop", "desc": "Drag from A to B"},
    "key_type": {"script": "desktop_control.py", "cmd": "type_text", "category": "desktop", "desc": "Type text via keyboard"},
    "key_press": {"script": "desktop_control.py", "cmd": "key_press", "category": "desktop", "desc": "Press key combo"},
    "app_launch": {"script": "desktop_control.py", "cmd": "app_launch", "category": "desktop", "desc": "Launch an application"},
    "app_switch": {"script": "desktop_control.py", "cmd": "app_switch", "category": "desktop", "desc": "Switch to application"},
    "app_quit": {"script": "desktop_control.py", "cmd": "app_quit", "category": "desktop", "desc": "Quit application"},
    "app_list": {"script": "desktop_control.py", "cmd": "app_list", "category": "desktop", "desc": "List running apps"},
    "window_move": {"script": "desktop_control.py", "cmd": "window_move", "category": "desktop", "desc": "Move window position"},
    "window_resize": {"script": "desktop_control.py", "cmd": "window_resize", "category": "desktop", "desc": "Resize window"},
    "window_list": {"script": "desktop_control.py", "cmd": "window_list", "category": "desktop", "desc": "List all windows"},
    "screenshot": {"script": "desktop_control.py", "cmd": "screenshot", "category": "desktop", "desc": "Capture screen"},
    "screenshot_region": {"script": "desktop_control.py", "cmd": "screenshot_region", "category": "desktop", "desc": "Capture screen region"},
    "clipboard_read": {"script": "desktop_control.py", "cmd": "clipboard_read", "category": "desktop", "desc": "Read clipboard"},
    "clipboard_write": {"script": "desktop_control.py", "cmd": "clipboard_write", "category": "desktop", "desc": "Write to clipboard"},
    "notification": {"script": "desktop_control.py", "cmd": "notify", "category": "desktop", "desc": "Send system notification"},
    "volume_set": {"script": "desktop_control.py", "cmd": "volume", "category": "desktop", "desc": "Set system volume"},
    "brightness_set": {"script": "desktop_control.py", "cmd": "brightness", "category": "desktop", "desc": "Set display brightness"},
    "ocr_screen": {"script": "desktop_control.py", "cmd": "ocr", "category": "desktop", "desc": "OCR screen text"},

    # ═══════════════════════════════════════════════════════════════
    # SCREEN VISION (6 caps) — Integrated screenshot+vision pipeline
    # ═══════════════════════════════════════════════════════════════
    "screen_capture": {"script": "screen_vision.py", "cmd": "capture", "category": "screen_vision", "desc": "Screenshot to canonical path for vision analysis"},
    "screen_ocr": {"script": "screen_vision.py", "cmd": "ocr", "category": "screen_vision", "desc": "Screenshot + full OCR text extraction"},
    "screen_describe": {"script": "screen_vision.py", "cmd": "describe", "category": "screen_vision", "desc": "Screenshot + prepare for vision_analyze"},
    "screen_find": {"script": "screen_vision.py", "cmd": "find", "category": "screen_vision", "desc": "Find specific text on screen via OCR"},
    "screen_monitor": {"script": "screen_vision.py", "cmd": "monitor", "category": "screen_vision", "desc": "Watch screen for changes over time"},
    "screen_last": {"script": "screen_vision.py", "cmd": "last", "category": "screen_vision", "desc": "Get last captured screen info"},

    # ═══════════════════════════════════════════════════════════════
    # PERCEPTION (16 caps) — NEW WAVE 2
    # ═══════════════════════════════════════════════════════════════
    "color_pick": {"script": "perception_tool.py", "cmd": "color", "category": "perception", "desc": "Sample pixel color at coordinates"},
    "color_palette": {"script": "perception_tool.py", "cmd": "palette", "category": "perception", "desc": "Extract dominant colors from screen"},
    "screen_diff": {"script": "perception_tool.py", "cmd": "diff", "category": "perception", "desc": "Compare two screenshots"},
    "screen_monitor": {"script": "perception_tool.py", "cmd": "monitor", "category": "perception", "desc": "Monitor screen for changes"},
    "gps_location": {"script": "perception_tool.py", "cmd": "location", "category": "perception", "desc": "Get GPS coordinates"},
    "ambient_sound": {"script": "perception_tool.py", "cmd": "sound", "category": "perception", "desc": "Record and classify ambient sound"},
    "table_extract": {"script": "perception_tool.py", "cmd": "table", "category": "perception", "desc": "Extract table structure from image"},
    "chart_read": {"script": "perception_tool.py", "cmd": "chart", "category": "perception", "desc": "Analyze chart/graph image"},
    "handwriting_detect": {"script": "perception_tool.py", "cmd": "handwriting", "category": "perception", "desc": "Detect handwriting vs print"},
    "font_identify": {"script": "perception_tool.py", "cmd": "font", "category": "perception", "desc": "Identify font characteristics"},
    "monitor_list": {"script": "perception_tool.py", "cmd": "monitors", "category": "perception", "desc": "List connected displays"},
    "screenshot_monitor": {"script": "perception_tool.py", "cmd": "screenshot_monitor", "category": "perception", "desc": "Capture specific display"},
    "barcode_scan": {"script": "perception_tool.py", "cmd": "barcode_scan", "category": "perception", "desc": "Scan barcode from camera"},
    "document_scan": {"script": "perception_tool.py", "cmd": "doc_scan", "category": "perception", "desc": "Scan document to PDF"},
    "ocr_stream": {"script": "perception_tool.py", "cmd": "ocr_stream", "category": "perception", "desc": "Continuous OCR stream"},
    "screen_find_text": {"script": "perception_tool.py", "cmd": "find_text", "category": "perception", "desc": "Search for text on screen"},

    # ═══════════════════════════════════════════════════════════════
    # IMAGE (10 caps)
    # ═══════════════════════════════════════════════════════════════
    "img_resize": {"script": "image_tool.py", "cmd": "resize", "category": "image", "desc": "Resize image"},
    "img_crop": {"script": "image_tool.py", "cmd": "crop", "category": "image", "desc": "Crop image"},
    "img_rotate": {"script": "image_tool.py", "cmd": "rotate", "category": "image", "desc": "Rotate image"},
    "img_filter": {"script": "image_tool.py", "cmd": "filter", "category": "image", "desc": "Apply filter"},
    "img_convert": {"script": "image_tool.py", "cmd": "convert", "category": "image", "desc": "Convert format"},
    "img_metadata": {"script": "image_tool.py", "cmd": "metadata", "category": "image", "desc": "Read EXIF metadata"},
    "img_composite": {"script": "image_tool.py", "cmd": "composite", "category": "image", "desc": "Composite images"},
    "img_thumbnail": {"script": "image_tool.py", "cmd": "thumbnail", "category": "image", "desc": "Generate thumbnail"},
    "img_annotate": {"script": "image_tool.py", "cmd": "annotate", "category": "image", "desc": "Add text annotation"},
    "img_watermark": {"script": "image_tool.py", "cmd": "watermark", "category": "image", "desc": "Add watermark"},

    # ═══════════════════════════════════════════════════════════════
    # AUDIO (12 caps)
    # ═══════════════════════════════════════════════════════════════
    "audio_convert": {"script": "audio_tool.py", "cmd": "convert", "category": "audio", "desc": "Convert audio format"},
    "audio_trim": {"script": "audio_tool.py", "cmd": "trim", "category": "audio", "desc": "Trim audio clip"},
    "audio_merge": {"script": "audio_tool.py", "cmd": "merge", "category": "audio", "desc": "Merge audio files"},
    "audio_normalize": {"script": "audio_tool.py", "cmd": "normalize", "category": "audio", "desc": "Normalize audio levels"},
    "audio_record": {"script": "audio_tool.py", "cmd": "record", "category": "audio", "desc": "Record from microphone"},
    "audio_transcribe": {"script": "audio_tool.py", "cmd": "transcribe", "category": "audio", "desc": "Speech to text (Whisper)"},
    "audio_tts": {"script": "audio_tool.py", "cmd": "tts", "category": "audio", "desc": "Text to speech"},
    "audio_extract": {"script": "audio_tool.py", "cmd": "extract", "category": "audio", "desc": "Extract audio from video"},
    "audio_speed": {"script": "audio_tool.py", "cmd": "speed", "category": "audio", "desc": "Change playback speed"},
    "audio_volume": {"script": "audio_tool.py", "cmd": "volume", "category": "audio", "desc": "Adjust volume"},
    "audio_reverse": {"script": "audio_tool.py", "cmd": "reverse", "category": "audio", "desc": "Reverse audio"},
    "audio_spectrogram": {"script": "audio_tool.py", "cmd": "spectrogram", "category": "audio", "desc": "Generate spectrogram"},

    # ═══════════════════════════════════════════════════════════════
    # VIDEO (10 caps)
    # ═══════════════════════════════════════════════════════════════
    "video_convert": {"script": "video_tool.py", "cmd": "convert", "category": "video", "desc": "Convert video format"},
    "video_trim": {"script": "video_tool.py", "cmd": "trim", "category": "video", "desc": "Trim video clip"},
    "video_merge": {"script": "video_tool.py", "cmd": "merge", "category": "video", "desc": "Merge video files"},
    "video_frames": {"script": "video_tool.py", "cmd": "frames", "category": "video", "desc": "Extract frames"},
    "video_gif": {"script": "video_tool.py", "cmd": "gif", "category": "video", "desc": "Video to GIF"},
    "video_speed": {"script": "video_tool.py", "cmd": "speed", "category": "video", "desc": "Change video speed"},
    "video_reverse": {"script": "video_tool.py", "cmd": "reverse", "category": "video", "desc": "Reverse video"},
    "video_concat": {"script": "video_tool.py", "cmd": "concat", "category": "video", "desc": "Concatenate videos"},
    "video_record": {"script": "video_tool.py", "cmd": "record", "category": "video", "desc": "Record screen"},
    "video_metadata": {"script": "video_tool.py", "cmd": "metadata", "category": "video", "desc": "Read video metadata"},

    # ═══════════════════════════════════════════════════════════════
    # DOCUMENT (12 caps)
    # ═══════════════════════════════════════════════════════════════
    "pdf_create": {"script": "pdf_tool.py", "cmd": "create", "category": "document", "desc": "Create PDF from text"},
    "pdf_merge": {"script": "pdf_tool.py", "cmd": "merge", "category": "document", "desc": "Merge PDFs"},
    "pdf_split": {"script": "pdf_tool.py", "cmd": "split", "category": "document", "desc": "Split PDF"},
    "pdf_extract_text": {"script": "pdf_tool.py", "cmd": "extract_text", "category": "document", "desc": "Extract text from PDF"},
    "pdf_encrypt": {"script": "pdf_tool.py", "cmd": "encrypt", "category": "document", "desc": "Encrypt PDF"},
    "pdf_decrypt": {"script": "pdf_tool.py", "cmd": "decrypt", "category": "document", "desc": "Decrypt PDF"},
    "pdf_rotate": {"script": "pdf_tool.py", "cmd": "rotate", "category": "document", "desc": "Rotate PDF pages"},
    "pdf_watermark": {"script": "pdf_tool.py", "cmd": "watermark", "category": "document", "desc": "Add watermark to PDF"},
    "qr_generate": {"script": "qr_tool.py", "cmd": "generate", "category": "document", "desc": "Generate QR code"},
    "qr_read": {"script": "qr_tool.py", "cmd": "read", "category": "document", "desc": "Read QR code"},
    "md_to_html": {"script": "creative_tool.py", "cmd": "md_to_html", "category": "document", "desc": "Markdown to HTML"},
    "md_to_pdf": {"script": "creative_tool.py", "cmd": "md_to_pdf", "category": "document", "desc": "Markdown to PDF"},

    # ═══════════════════════════════════════════════════════════════
    # APPLE ECOSYSTEM (14 caps)
    # ═══════════════════════════════════════════════════════════════
    "messages_send": {"script": "apple_control.py", "cmd": "message_send", "category": "apple", "desc": "Send iMessage/SMS"},
    "messages_read": {"script": "apple_control.py", "cmd": "message_read", "category": "apple", "desc": "Read recent messages"},
    "calendar_add": {"script": "apple_control.py", "cmd": "calendar_add", "category": "apple", "desc": "Add calendar event"},
    "calendar_list": {"script": "apple_control.py", "cmd": "calendar_list", "category": "apple", "desc": "List calendar events"},
    "calendar_delete": {"script": "apple_control.py", "cmd": "calendar_delete", "category": "apple", "desc": "Delete calendar event"},
    "reminders_add": {"script": "apple_control.py", "cmd": "reminder_add", "category": "apple", "desc": "Add reminder"},
    "reminders_list": {"script": "apple_control.py", "cmd": "reminder_list", "category": "apple", "desc": "List reminders"},
    "reminders_complete": {"script": "apple_control.py", "cmd": "reminder_complete", "category": "apple", "desc": "Complete reminder"},
    "notes_create": {"script": "apple_control.py", "cmd": "note_create", "category": "apple", "desc": "Create note"},
    "notes_list": {"script": "apple_control.py", "cmd": "note_list", "category": "apple", "desc": "List notes"},
    "notes_read": {"script": "apple_control.py", "cmd": "note_read", "category": "apple", "desc": "Read note content"},
    "contacts_search": {"script": "apple_control.py", "cmd": "contact_search", "category": "apple", "desc": "Search contacts"},
    "findmy_locate": {"script": "apple_control.py", "cmd": "findmy", "category": "apple", "desc": "Locate Apple devices"},
    "facetime": {"script": "comm_tool.py", "cmd": "facetime", "category": "apple", "desc": "Start FaceTime audio call"},

    # ═══════════════════════════════════════════════════════════════
    # COMMUNICATION (18 caps) — NEW WAVE 2
    # ═══════════════════════════════════════════════════════════════
    "email_list": {"script": "comm_tool.py", "cmd": "email_list", "category": "comm", "desc": "List recent emails"},
    "email_read": {"script": "comm_tool.py", "cmd": "email_read", "category": "comm", "desc": "Read email content"},
    "email_send": {"script": "comm_tool.py", "cmd": "email_send", "category": "comm", "desc": "Send email"},
    "email_search": {"script": "comm_tool.py", "cmd": "email_search", "category": "comm", "desc": "Search emails"},
    "email_folders": {"script": "comm_tool.py", "cmd": "email_folders", "category": "comm", "desc": "List email folders"},
    "facetime_video": {"script": "comm_tool.py", "cmd": "facetime_video", "category": "comm", "desc": "Start FaceTime video call"},
    "airdrop_send": {"script": "comm_tool.py", "cmd": "airdrop", "category": "comm", "desc": "Send file via AirDrop"},
    "bluetooth_status": {"script": "comm_tool.py", "cmd": "bluetooth", "category": "comm", "desc": "Check Bluetooth status"},
    "bluetooth_devices": {"script": "comm_tool.py", "cmd": "bt_devices", "category": "comm", "desc": "List Bluetooth devices"},
    "bluetooth_toggle": {"script": "comm_tool.py", "cmd": "bt_toggle", "category": "comm", "desc": "Toggle Bluetooth on/off"},
    "wifi_status": {"script": "comm_tool.py", "cmd": "wifi", "category": "comm", "desc": "Check WiFi status"},
    "wifi_scan": {"script": "comm_tool.py", "cmd": "wifi_scan", "category": "comm", "desc": "Scan WiFi networks"},
    "wifi_connect": {"script": "comm_tool.py", "cmd": "wifi_connect", "category": "comm", "desc": "Connect to WiFi"},
    "printer_list": {"script": "comm_tool.py", "cmd": "printers", "category": "comm", "desc": "List printers"},
    "print_file": {"script": "comm_tool.py", "cmd": "print", "category": "comm", "desc": "Print a file"},
    "print_queue": {"script": "comm_tool.py", "cmd": "print_queue", "category": "comm", "desc": "Check print queue"},
    "vpn_list": {"script": "comm_tool.py", "cmd": "vpn_list", "category": "comm", "desc": "List VPN connections"},
    "webhook_post": {"script": "comm_tool.py", "cmd": "webhook", "category": "comm", "desc": "POST to any webhook"},

    # ═══════════════════════════════════════════════════════════════
    # COGNITION (24 caps) — NEW WAVE 2
    # ═══════════════════════════════════════════════════════════════
    "stats_describe": {"script": "cognition_tool.py", "cmd": "describe", "category": "cognition", "desc": "Descriptive statistics"},
    "stats_correlate": {"script": "cognition_tool.py", "cmd": "correlate", "category": "cognition", "desc": "Pearson correlation"},
    "stats_ttest": {"script": "cognition_tool.py", "cmd": "ttest", "category": "cognition", "desc": "T-test (one/two sample)"},
    "sentiment": {"script": "cognition_tool.py", "cmd": "sentiment", "category": "cognition", "desc": "Sentiment analysis"},
    "ner_extract": {"script": "cognition_tool.py", "cmd": "ner", "category": "cognition", "desc": "Named entity recognition"},
    "chem_molar_mass": {"script": "cognition_tool.py", "cmd": "molar_mass", "category": "cognition", "desc": "Calculate molar mass"},
    "chem_dilution": {"script": "cognition_tool.py", "cmd": "dilution", "category": "cognition", "desc": "Dilution calculator"},
    "dose_weight": {"script": "cognition_tool.py", "cmd": "dose_weight", "category": "cognition", "desc": "Weight-based dosage"},
    "dose_bsa": {"script": "cognition_tool.py", "cmd": "dose_bsa", "category": "cognition", "desc": "BSA-based dosage"},
    "dose_pediatric": {"script": "cognition_tool.py", "cmd": "dose_pediatric", "category": "cognition", "desc": "Pediatric dosage"},
    "crcl": {"script": "cognition_tool.py", "cmd": "crcl", "category": "cognition", "desc": "Creatinine clearance (Cockcroft-Gault)"},
    "bmi": {"script": "cognition_tool.py", "cmd": "bmi", "category": "cognition", "desc": "BMI calculator"},
    "currency_convert": {"script": "cognition_tool.py", "cmd": "currency", "category": "cognition", "desc": "Currency conversion"},
    "timezone_convert": {"script": "cognition_tool.py", "cmd": "tz_convert", "category": "cognition", "desc": "Timezone conversion"},
    "diagram_mermaid": {"script": "cognition_tool.py", "cmd": "diagram", "category": "cognition", "desc": "Generate Mermaid diagram"},
    "diagram_tree": {"script": "cognition_tool.py", "cmd": "tree", "category": "cognition", "desc": "ASCII directory tree"},
    "code_count": {"script": "cognition_tool.py", "cmd": "code_count", "category": "cognition", "desc": "Lines of code by language"},

    # ═══════════════════════════════════════════════════════════════
    # DATA (12 caps)
    # ═══════════════════════════════════════════════════════════════
    "xlsx_create": {"script": "data_tool.py", "cmd": "xlsx_create", "category": "data", "desc": "Create Excel spreadsheet"},
    "xlsx_read": {"script": "data_tool.py", "cmd": "xlsx_read", "category": "data", "desc": "Read Excel spreadsheet"},
    "math_solve": {"script": "data_tool.py", "cmd": "math", "category": "data", "desc": "Solve math expression"},
    "unit_convert": {"script": "data_tool.py", "cmd": "unit", "category": "data", "desc": "Unit conversion"},
    "translate": {"script": "data_tool.py", "cmd": "translate", "category": "data", "desc": "Translate text"},
    "rss_read": {"script": "data_tool.py", "cmd": "rss", "category": "data", "desc": "Read RSS feed"},
    "db_query_sqlite": {"script": "data_tool.py", "cmd": "db", "category": "data", "desc": "Query SQLite database"},
    "json_validate": {"script": "data_tool.py", "cmd": "json_validate", "category": "data", "desc": "Validate JSON"},
    "csv_parse": {"script": "data_tool.py", "cmd": "csv", "category": "data", "desc": "Parse CSV data"},
    "hash_compute": {"script": "data_tool.py", "cmd": "hash", "category": "data", "desc": "Compute file hash"},
    "diff_text": {"script": "data_tool.py", "cmd": "diff", "category": "data", "desc": "Diff two texts"},
    "sort_data": {"script": "data_tool.py", "cmd": "sort", "category": "data", "desc": "Sort data"},

    # ═══════════════════════════════════════════════════════════════
    # SYSTEM (12 caps)
    # ═══════════════════════════════════════════════════════════════
    "file_watch": {"script": "sys_tool.py", "cmd": "watch", "category": "system", "desc": "Watch file changes"},
    "process_list": {"script": "sys_tool.py", "cmd": "ps", "category": "system", "desc": "List processes"},
    "process_kill": {"script": "sys_tool.py", "cmd": "kill", "category": "system", "desc": "Kill process"},
    "docker_ps": {"script": "sys_tool.py", "cmd": "docker_ps", "category": "system", "desc": "List Docker containers"},
    "docker_run": {"script": "sys_tool.py", "cmd": "docker_run", "category": "system", "desc": "Run Docker container"},
    "docker_stop": {"script": "sys_tool.py", "cmd": "docker_stop", "category": "system", "desc": "Stop Docker container"},
    "backup_create": {"script": "sys_tool.py", "cmd": "backup", "category": "system", "desc": "Create backup archive"},
    "disk_usage": {"script": "sys_tool.py", "cmd": "disk", "category": "system", "desc": "Disk usage analysis"},
    "battery_status": {"script": "sys_tool.py", "cmd": "battery", "category": "system", "desc": "Battery status"},
    "network_info": {"script": "sys_tool.py", "cmd": "network", "category": "system", "desc": "Network interfaces"},
    "cron_list": {"script": "sys_tool.py", "cmd": "cron", "category": "system", "desc": "List cron jobs"},
    "service_check": {"script": "sys_tool.py", "cmd": "service", "category": "system", "desc": "Check service status"},

    # ═══════════════════════════════════════════════════════════════
    # INTEGRATION (26 caps) — NEW WAVE 2
    # ═══════════════════════════════════════════════════════════════
    "ssh_exec": {"script": "integration_tool.py", "cmd": "ssh_exec", "category": "integration", "desc": "Execute command via SSH"},
    "ssh_upload": {"script": "integration_tool.py", "cmd": "ssh_upload", "category": "integration", "desc": "Upload file via SCP"},
    "ssh_download": {"script": "integration_tool.py", "cmd": "ssh_download", "category": "integration", "desc": "Download file via SCP"},
    "ssh_tunnel": {"script": "integration_tool.py", "cmd": "ssh_tunnel", "category": "integration", "desc": "Create SSH tunnel"},
    "ws_send": {"script": "integration_tool.py", "cmd": "ws_send", "category": "integration", "desc": "Send WebSocket message"},
    "ws_listen": {"script": "integration_tool.py", "cmd": "ws_listen", "category": "integration", "desc": "Listen on WebSocket"},
    "api_check": {"script": "integration_tool.py", "cmd": "api_check", "category": "integration", "desc": "Check API health"},
    "api_batch_check": {"script": "integration_tool.py", "cmd": "api_batch", "category": "integration", "desc": "Batch API health check"},
    "s3_upload": {"script": "integration_tool.py", "cmd": "s3_upload", "category": "integration", "desc": "Upload to S3"},
    "s3_download": {"script": "integration_tool.py", "cmd": "s3_download", "category": "integration", "desc": "Download from S3"},
    "s3_list": {"script": "integration_tool.py", "cmd": "s3_list", "category": "integration", "desc": "List S3 bucket"},
    "secret_get": {"script": "integration_tool.py", "cmd": "secret_get", "category": "integration", "desc": "Get from Keychain"},
    "secret_set": {"script": "integration_tool.py", "cmd": "secret_set", "category": "integration", "desc": "Store in Keychain"},
    "cert_info": {"script": "integration_tool.py", "cmd": "cert_info", "category": "integration", "desc": "SSL certificate info"},
    "cert_generate": {"script": "integration_tool.py", "cmd": "cert_gen", "category": "integration", "desc": "Generate self-signed cert"},
    "dns_lookup": {"script": "integration_tool.py", "cmd": "dns", "category": "integration", "desc": "DNS lookup"},
    "dns_reverse": {"script": "integration_tool.py", "cmd": "dns_reverse", "category": "integration", "desc": "Reverse DNS lookup"},
    "gh_actions_list": {"script": "integration_tool.py", "cmd": "gh_actions", "category": "integration", "desc": "List GitHub Actions"},
    "gh_actions_trigger": {"script": "integration_tool.py", "cmd": "gh_trigger", "category": "integration", "desc": "Trigger GitHub Action"},
    "db_query": {"script": "integration_tool.py", "cmd": "db_query", "category": "integration", "desc": "Query database"},
    "db_tables": {"script": "integration_tool.py", "cmd": "db_tables", "category": "integration", "desc": "List database tables"},
    "net_ports": {"script": "integration_tool.py", "cmd": "ports", "category": "integration", "desc": "Show listening ports"},
    "net_ping": {"script": "integration_tool.py", "cmd": "ping", "category": "integration", "desc": "Ping host"},
    "net_traceroute": {"script": "integration_tool.py", "cmd": "traceroute", "category": "integration", "desc": "Traceroute to host"},
    "net_port_scan": {"script": "integration_tool.py", "cmd": "port_scan", "category": "integration", "desc": "Scan ports"},
    "net_speed_test": {"script": "integration_tool.py", "cmd": "speed_test", "category": "integration", "desc": "Network speed test"},

    # ═══════════════════════════════════════════════════════════════
    # CREATIVE (18 caps) — NEW WAVE 2
    # ═══════════════════════════════════════════════════════════════
    "synth_tone": {"script": "creative_tool.py", "cmd": "tone", "category": "creative", "desc": "Generate pure tone WAV"},
    "synth_melody": {"script": "creative_tool.py", "cmd": "melody", "category": "creative", "desc": "Generate melody from notes"},
    "synth_chord": {"script": "creative_tool.py", "cmd": "chord", "category": "creative", "desc": "Generate chord WAV"},
    "ascii_text": {"script": "creative_tool.py", "cmd": "ascii_text", "category": "creative", "desc": "ASCII art text"},
    "ascii_fonts": {"script": "creative_tool.py", "cmd": "ascii_fonts", "category": "creative", "desc": "List ASCII art fonts"},
    "cowsay": {"script": "creative_tool.py", "cmd": "cowsay", "category": "creative", "desc": "Cowsay ASCII art"},
    "diagram_plantuml": {"script": "creative_tool.py", "cmd": "plantuml", "category": "creative", "desc": "PlantUML diagram"},
    "diagram_graphviz": {"script": "creative_tool.py", "cmd": "graphviz", "category": "creative", "desc": "Graphviz DOT diagram"},
    "diagram_ascii_flow": {"script": "creative_tool.py", "cmd": "ascii_flow", "category": "creative", "desc": "ASCII flowchart"},
    "presentation_create": {"script": "creative_tool.py", "cmd": "presentation", "category": "creative", "desc": "Create presentation"},
    "gif_create": {"script": "creative_tool.py", "cmd": "gif_create", "category": "creative", "desc": "Create animated GIF"},
    "gif_from_video": {"script": "creative_tool.py", "cmd": "gif_from_video", "category": "creative", "desc": "Extract GIF from video"},
    "video_from_images": {"script": "creative_tool.py", "cmd": "video_from_images", "category": "creative", "desc": "Create timelapse video"},
    "image_pattern": {"script": "creative_tool.py", "cmd": "pattern", "category": "creative", "desc": "Generate pattern image"},
    "image_composite": {"script": "creative_tool.py", "cmd": "composite", "category": "creative", "desc": "Combine images"},
    "color_theme": {"script": "creative_tool.py", "cmd": "color_theme", "category": "creative", "desc": "Generate color theme"},
}

def run(cap_id, args=None):
    """Execute a capability by ID."""
    if cap_id not in CAPABILITIES:
        return {"status": "error", "error": "Unknown capability: " + cap_id,
                "available": len(CAPABILITIES)}
    
    cap = CAPABILITIES[cap_id]
    script = os.path.join(BASE, cap["script"])
    cmd_parts = [PY, script, cap["cmd"]]
    if args:
        cmd_parts.extend(args)
    
    start = time.time()
    try:
        r = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=30)
        elapsed = round((time.time() - start) * 1000)
        try:
            result = json.loads(r.stdout)
            result["elapsed_ms"] = elapsed
            result["capability"] = cap_id
            return result
        except:
            return {"status": "raw", "capability": cap_id, "output": r.stdout[:2000],
                    "elapsed_ms": elapsed}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "capability": cap_id}
    except Exception as e:
        return {"status": "error", "capability": cap_id, "error": str(e)}

def search(query):
    """Search capabilities by keyword."""
    q = query.lower()
    matches = []
    for cid, cap in CAPABILITIES.items():
        searchable = "{} {} {} {}".format(cid, cap["desc"], cap["category"], cap["cmd"]).lower()
        if q in searchable:
            matches.append({"id": cid, "desc": cap["desc"], "category": cap["category"]})
    return matches

def list_all():
    """Group capabilities by category."""
    categories = {}
    for cid, cap in CAPABILITIES.items():
        cat = cap["category"]
        categories.setdefault(cat, []).append({"id": cid, "desc": cap["desc"]})
    return categories

def stats():
    """Get capability statistics."""
    categories = {}
    for cap in CAPABILITIES.values():
        categories[cap["category"]] = categories.get(cap["category"], 0) + 1
    
    # Check which scripts exist
    scripts = set(cap["script"] for cap in CAPABILITIES.values())
    scripts_ok = sum(1 for s in scripts if Path(BASE).joinpath(s).exists())
    
    return {
        "total_capabilities": len(CAPABILITIES),
        "total_categories": len(categories),
        "scripts_available": len(scripts),
        "scripts_exist": scripts_ok,
        "by_category": categories,
    }

def status():
    """Full system readiness check."""
    s = stats()
    results = {"registry": s}
    
    # Quick test each script
    tested = {}
    scripts = set(cap["script"] for cap in CAPABILITIES.values())
    for script in sorted(scripts):
        path = Path(BASE).joinpath(script)
        if path.exists():
            # Try help command
            r = subprocess.run([PY, str(path), "help"], capture_output=True, text=True, timeout=5)
            tested[script] = "ok" if r.returncode == 0 else "help_failed"
        else:
            tested[script] = "missing"
    
    results["script_health"] = tested
    results["ready"] = all(v == "ok" for v in tested.values())
    return results

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    if action == "list":
        cats = list_all()
        for cat, caps in sorted(cats.items()):
            print("\n=== {} ({} caps) ===".format(cat.upper(), len(caps)))
            for c in caps:
                print("  {} — {}".format(c["id"], c["desc"]))
    
    elif action == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        results = search(query)
        print(json.dumps(results, indent=2))
    
    elif action == "run":
        cap_id = sys.argv[2]
        args = sys.argv[3:]
        result = run(cap_id, args)
        print(json.dumps(result, indent=2))
    
    elif action == "stats":
        print(json.dumps(stats(), indent=2))
    
    elif action == "status":
        print(json.dumps(status(), indent=2))
    
    else:
        print(json.dumps({
            "usage": "capability_registry.py <list|search|run|stats|status>",
            "total_capabilities": len(CAPABILITIES),
        }, indent=2))
