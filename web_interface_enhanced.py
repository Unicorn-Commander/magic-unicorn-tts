#!/usr/bin/env python3
"""
Enhanced Magic Unicorn Kokoro NPU TTS Web Interface
Professional version with logs, settings, and advanced monitoring
"""

import os
import sys
import time
import json
import uuid
import logging
import threading
import queue
import subprocess
from datetime import datetime
from pathlib import Path
from collections import deque

from flask import Flask, render_template_string, request, send_file, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'magic_unicorn_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global log buffer for real-time streaming
log_buffer = deque(maxlen=1000)
log_queue = queue.Queue()

# Custom log handler to capture logs
class WebLogHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3],
                'level': record.levelname,
                'message': self.format(record),
                'module': record.name
            }
            log_buffer.append(log_entry)
            log_queue.put(log_entry)
        except Exception:
            pass

# Add our custom handler to capture all logs
web_handler = WebLogHandler()
web_handler.setFormatter(logging.Formatter('%(message)s'))
logging.getLogger().addHandler(web_handler)

# Magic Unicorn branding and configuration
BRAND_CONFIG = {
    "title": "Magic Unicorn TTS Pro",
    "subtitle": "Professional NPU-Accelerated Voice Synthesis",
    "company": "Magic Unicorn Technologies",
    "product": "Unicorn Commander Pro",
    "version": "2.0.0",
    "theme": {
        "primary": "#8B5CF6",
        "secondary": "#EC4899",
        "accent": "#06B6D4",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "dark": "#1F2937",
        "light": "#F9FAFB"
    }
}

# Application settings with defaults
APP_SETTINGS = {
    'preferred_method': 'mlir_npu',
    'audio_quality': 'high',
    'sample_rate': 24000,
    'speed': 1.0,
    'pitch': 1.0,
    'auto_play': True,
    'log_level': 'INFO',
    'max_text_length': 1000,
    'show_advanced': True,
    'enable_monitoring': True
}

# Initialize other components...
from web_interface_magic_unicorn import (
    detect_system_status, 
    run_synthesis_subprocess, 
    AVAILABLE_VOICES
)

# Performance tracking
performance_metrics = deque(maxlen=100)

def get_system_info():
    """Get detailed system information"""
    try:
        info = {
            'cpu_temp': 'N/A',
            'npu_util': 'N/A',
            'memory_usage': 'N/A',
            'disk_space': 'N/A'
        }
        
        # Try to get CPU temperature
        try:
            temp_result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=2)
            if temp_result.returncode == 0 and 'Tctl:' in temp_result.stdout:
                for line in temp_result.stdout.split('\n'):
                    if 'Tctl:' in line:
                        temp = line.split('+')[1].split('°')[0] if '+' in line else 'N/A'
                        info['cpu_temp'] = f"{temp}°C"
                        break
        except:
            pass
            
        # Try to get memory usage
        try:
            import psutil
            mem = psutil.virtual_memory()
            info['memory_usage'] = f"{mem.percent:.1f}%"
        except:
            pass
            
        return info
    except Exception as e:
        logger.warning(f"System info collection failed: {e}")
        return {'cpu_temp': 'N/A', 'npu_util': 'N/A', 'memory_usage': 'N/A', 'disk_space': 'N/A'}

def get_enhanced_template():
    """Return the enhanced Magic Unicorn HTML template with tabs"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ brand.title }} - {{ brand.subtitle }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: {{ brand.theme.primary }};
            --secondary: {{ brand.theme.secondary }};
            --accent: {{ brand.theme.accent }};
            --success: {{ brand.theme.success }};
            --warning: {{ brand.theme.warning }};
            --error: {{ brand.theme.error }};
            --dark: {{ brand.theme.dark }};
            --light: {{ brand.theme.light }};
            
            --gradient-magic: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            --gradient-dark: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--gradient-dark);
            color: #e8e8f0;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Enhanced Header with Tabs */
        .header {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(139, 92, 246, 0.3);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-top {
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .brand-icon {
            width: 48px;
            height: 48px;
            background: var(--gradient-magic);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: white;
            box-shadow: var(--shadow-lg);
            overflow: hidden;
        }

        .brand-icon img {
            width: 40px;
            height: 40px;
            object-fit: contain;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        }

        /* Logo styling for buttons */
        .btn img {
            filter: brightness(0.9) contrast(1.1);
            transition: all 0.3s ease;
        }

        .btn:hover img {
            filter: brightness(1.1) contrast(1.2) drop-shadow(0 2px 4px rgba(139, 92, 246, 0.4));
        }

        .brand-text h1 {
            font-size: 1.5rem;
            font-weight: 700;
            background: var(--gradient-magic);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .brand-text p {
            font-size: 0.875rem;
            color: #9ca3af;
            margin-top: 2px;
        }

        .status-indicators {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }

        .status-badge.online {
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .status-badge.offline {
            background: rgba(239, 68, 68, 0.2);
            color: var(--error);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        /* Tab Navigation */
        .tab-nav {
            padding: 0 2rem;
            background: rgba(0, 0, 0, 0.2);
            border-top: 1px solid rgba(139, 92, 246, 0.2);
        }

        .tab-list {
            display: flex;
            gap: 0;
            list-style: none;
        }

        .tab-item {
            padding: 1rem 1.5rem;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s ease;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .tab-item:hover {
            background: rgba(139, 92, 246, 0.1);
            color: var(--primary);
        }

        .tab-item.active {
            border-bottom-color: var(--primary);
            background: rgba(139, 92, 246, 0.1);
            color: var(--primary);
        }

        /* Main Layout */
        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Magic Cards (keep existing styles) */
        .magic-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--shadow-xl);
            transition: all 0.3s ease;
            margin-bottom: 1.5rem;
        }

        .magic-card:hover {
            border-color: rgba(139, 92, 246, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 25px 50px -12px rgba(139, 92, 246, 0.25);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }

        .card-icon {
            width: 32px;
            height: 32px;
            background: var(--gradient-magic);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 16px;
        }

        .card-title {
            font-size: 1.125rem;
            font-weight: 600;
            color: #f3f4f6;
        }

        /* Log Viewer */
        .log-container {
            background: #1a1a1a;
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 8px;
            height: 400px;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
        }

        .log-controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            align-items: center;
        }

        .log-entry {
            padding: 0.25rem 0.75rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            gap: 1rem;
        }

        .log-timestamp {
            color: #6b7280;
            flex-shrink: 0;
            width: 80px;
        }

        .log-level {
            flex-shrink: 0;
            width: 60px;
            font-weight: 500;
        }

        .log-level.INFO { color: var(--accent); }
        .log-level.WARNING { color: var(--warning); }
        .log-level.ERROR { color: var(--error); }
        .log-level.DEBUG { color: #9ca3af; }

        .log-message {
            flex: 1;
            color: #e8e8f0;
        }

        /* Settings Panel */
        .settings-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            color: #d1d5db;
            margin-bottom: 0.5rem;
        }

        .form-input, .form-select {
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            color: #e8e8f0;
            font-size: 0.875rem;
            transition: border-color 0.3s ease;
        }

        .form-input:focus, .form-select:focus {
            outline: none;
            border-color: var(--primary);
        }

        /* Performance Charts */
        .chart-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1.5rem;
        }

        /* Button Styles */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 10px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            position: relative;
            overflow: hidden;
        }

        .btn-primary {
            background: var(--gradient-magic);
            color: white;
            box-shadow: var(--shadow-md);
        }

        .btn-secondary {
            background: rgba(139, 92, 246, 0.1);
            color: var(--primary);
            border: 1px solid rgba(139, 92, 246, 0.3);
        }

        .btn-success {
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        /* Metric grids and other existing styles... */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }

        .metric-item {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }

        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
            font-family: 'JetBrains Mono', monospace;
        }

        .metric-label {
            font-size: 0.75rem;
            color: #9ca3af;
            margin-top: 0.25rem;
        }

        /* Text Input */
        .text-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 12px;
            padding: 1rem;
            color: #e8e8f0;
            font-size: 1rem;
            line-height: 1.6;
            resize: vertical;
            min-height: 120px;
            font-family: 'Inter', sans-serif;
            transition: border-color 0.3s ease;
        }

        .text-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
        }

        /* Progress and other components... */
        .progress-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 0.5rem;
            margin: 1rem 0;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(139, 92, 246, 0.2);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: var(--gradient-magic);
            border-radius: 4px;
            transition: width 0.3s ease;
            width: 0%;
        }

        .progress-text {
            font-size: 0.75rem;
            color: #9ca3af;
            margin-top: 0.5rem;
            text-align: center;
        }

        /* Auto-scroll for logs */
        .auto-scroll {
            scroll-behavior: smooth;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .settings-grid {
                grid-template-columns: 1fr;
            }
            
            .tab-list {
                overflow-x: auto;
            }
            
            .status-indicators {
                display: none;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-top">
            <div class="brand">
                <div class="brand-icon">
                    <img src="/static/magic_unicorn_logo.svg" alt="Magic Unicorn" title="Magic Unicorn Logo"/>
                </div>
                <div class="brand-text">
                    <h1>{{ brand.title }}</h1>
                    <p>{{ brand.subtitle }}</p>
                </div>
            </div>
            <div class="status-indicators">
                <div class="status-badge" id="npu-status">
                    <i class="fas fa-microchip"></i>
                    <span>NPU Status</span>
                </div>
                <div class="status-badge" id="system-status">
                    <i class="fas fa-circle"></i>
                    <span>System Ready</span>
                </div>
            </div>
        </div>
        
        <!-- Tab Navigation -->
        <div class="tab-nav">
            <ul class="tab-list">
                <li class="tab-item active" data-tab="synthesis">
                    <i class="fas fa-magic"></i>
                    <span>Synthesis</span>
                </li>
                <li class="tab-item" data-tab="logs">
                    <i class="fas fa-terminal"></i>
                    <span>Logs</span>
                </li>
                <li class="tab-item" data-tab="settings">
                    <i class="fas fa-cogs"></i>
                    <span>Settings</span>
                </li>
                <li class="tab-item" data-tab="monitoring">
                    <i class="fas fa-chart-line"></i>
                    <span>Monitoring</span>
                </li>
                <li class="tab-item" data-tab="system">
                    <i class="fas fa-server"></i>
                    <span>System</span>
                </li>
            </ul>
        </div>
    </header>

    <!-- Main Container -->
    <div class="main-container">
        <!-- Synthesis Tab -->
        <div id="synthesis-tab" class="tab-content active">
            <div class="magic-card">
                <div class="card-header">
                    <div class="card-icon">
                        <i class="fas fa-magic"></i>
                    </div>
                    <h2 class="card-title">Magic Voice Synthesis</h2>
                </div>
                
                <form id="tts-form">
                    <div class="form-group">
                        <label class="form-label" for="text-input">
                            <i class="fas fa-pen-fancy"></i> Enter your text to synthesize
                        </label>
                        <textarea 
                            id="text-input" 
                            class="text-input" 
                            placeholder="Type your message here... ✨"
                            required>Hello! Welcome to Magic Unicorn TTS Pro - the future of NPU-accelerated voice synthesis with advanced monitoring and controls.</textarea>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
                        <div class="form-group">
                            <label class="form-label" for="voice-select">
                                <i class="fas fa-user-astronaut"></i> Voice
                            </label>
                            <select id="voice-select" class="form-select">
                                {% for voice in voices %}
                                <option value="{{ voice.id }}">{{ voice.name }} ({{ voice.gender }})</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="method-select">
                                <i class="fas fa-rocket"></i> Method
                            </label>
                            <select id="method-select" class="form-select">
                                <option value="auto">🚀 Auto</option>
                                <option value="mlir_npu" selected>⚡ MLIR-AIE NPU</option>
                                <option value="npu_basic">🔥 Basic NPU</option>
                                <option value="cpu">💻 CPU</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">&nbsp;</label>
                            <button type="submit" class="btn btn-primary" id="generate-btn">
                                <i class="fas fa-sparkles"></i>
                                Generate
                            </button>
                        </div>
                    </div>
                </form>
                
                <!-- Progress Bar -->
                <div class="progress-container" id="progress-container" style="display: none;">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                    <div class="progress-text" id="progress-text">Preparing synthesis...</div>
                </div>
                
                <!-- Audio Player -->
                <div id="audio-panel" style="display: none; margin-top: 1.5rem;">
                    <div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 1rem;">
                        <audio id="audio-element" controls style="width: 100%;">
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                </div>
            </div>
            
            <!-- Performance Metrics -->
            <div class="magic-card">
                <div class="card-header">
                    <div class="card-icon">
                        <i class="fas fa-tachometer-alt"></i>
                    </div>
                    <h2 class="card-title">Live Performance</h2>
                </div>
                
                <div class="metric-grid">
                    <div class="metric-item">
                        <div class="metric-value" id="rtf-metric">0.00</div>
                        <div class="metric-label">Real-Time Factor</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="speed-metric">0.0s</div>
                        <div class="metric-label">Generation Time</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="method-metric">Ready</div>
                        <div class="metric-label">Active Method</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="quality-metric">24kHz</div>
                        <div class="metric-label">Audio Quality</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Logs Tab -->
        <div id="logs-tab" class="tab-content">
            <div class="magic-card">
                <div class="card-header">
                    <div class="card-icon">
                        <i class="fas fa-terminal"></i>
                    </div>
                    <h2 class="card-title">System Logs</h2>
                </div>
                
                <div class="log-controls">
                    <button class="btn btn-secondary" id="clear-logs">
                        <i class="fas fa-trash"></i> Clear
                    </button>
                    <button class="btn btn-secondary" id="export-logs">
                        <i class="fas fa-download"></i> Export
                    </button>
                    <select id="log-level-filter" class="form-select" style="width: auto;">
                        <option value="all">All Levels</option>
                        <option value="INFO">INFO</option>
                        <option value="WARNING">WARNING</option>
                        <option value="ERROR">ERROR</option>
                        <option value="DEBUG">DEBUG</option>
                    </select>
                    <label style="display: flex; align-items: center; gap: 0.5rem; margin-left: auto;">
                        <input type="checkbox" id="auto-scroll-logs" checked>
                        <span>Auto-scroll</span>
                    </label>
                </div>
                
                <div class="log-container" id="log-container">
                    <!-- Logs will be populated here -->
                </div>
            </div>
        </div>

        <!-- Settings Tab -->
        <div id="settings-tab" class="tab-content">
            <div class="settings-grid">
                <div class="magic-card">
                    <div class="card-header">
                        <div class="card-icon">
                            <i class="fas fa-sliders-h"></i>
                        </div>
                        <h2 class="card-title">Audio Settings</h2>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="preferred-method">Preferred Method</label>
                        <select id="preferred-method" class="form-select">
                            <option value="mlir_npu">MLIR-AIE NPU</option>
                            <option value="npu_basic">Basic NPU</option>
                            <option value="cpu">CPU</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="sample-rate">Sample Rate</label>
                        <select id="sample-rate" class="form-select">
                            <option value="16000">16kHz</option>
                            <option value="24000" selected>24kHz</option>
                            <option value="48000">48kHz</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="speed-setting">Speed</label>
                        <input type="range" id="speed-setting" class="form-input" min="0.5" max="2.0" step="0.1" value="1.0">
                        <span id="speed-value">1.0x</span>
                    </div>
                </div>
                
                <div class="magic-card">
                    <div class="card-header">
                        <div class="card-icon">
                            <i class="fas fa-cogs"></i>
                        </div>
                        <h2 class="card-title">System Settings</h2>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="log-level-setting">Log Level</label>
                        <select id="log-level-setting" class="form-select">
                            <option value="DEBUG">DEBUG</option>
                            <option value="INFO" selected>INFO</option>
                            <option value="WARNING">WARNING</option>
                            <option value="ERROR">ERROR</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">
                            <input type="checkbox" id="auto-play-setting" checked>
                            Auto-play generated audio
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">
                            <input type="checkbox" id="enable-monitoring-setting" checked>
                            Enable system monitoring
                        </label>
                    </div>
                    
                    <button class="btn btn-primary" id="save-settings">
                        <i class="fas fa-save"></i> Save Settings
                    </button>
                </div>
            </div>
        </div>

        <!-- Monitoring Tab -->
        <div id="monitoring-tab" class="tab-content">
            <div class="magic-card">
                <div class="card-header">
                    <div class="card-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <h2 class="card-title">Performance Monitoring</h2>
                </div>
                
                <div class="chart-container">
                    <canvas id="performance-chart" width="400" height="200"></canvas>
                </div>
            </div>
            
            <div class="magic-card">
                <div class="card-header">
                    <div class="card-icon">
                        <i class="fas fa-history"></i>
                    </div>
                    <h2 class="card-title">Recent Activity</h2>
                </div>
                
                <div id="activity-log">
                    <!-- Activity entries will be populated here -->
                </div>
            </div>
        </div>

        <!-- System Tab -->
        <div id="system-tab" class="tab-content">
            <div class="magic-card">
                <div class="card-header">
                    <div class="card-icon">
                        <i class="fas fa-microchip"></i>
                    </div>
                    <h2 class="card-title">NPU Status</h2>
                </div>
                
                <div class="metric-grid">
                    <div class="metric-item">
                        <div class="metric-value" id="npu-temp">N/A</div>
                        <div class="metric-label">Temperature</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="npu-util">N/A</div>
                        <div class="metric-label">Utilization</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="memory-usage">N/A</div>
                        <div class="metric-label">Memory Usage</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="disk-space">N/A</div>
                        <div class="metric-label">Disk Space</div>
                    </div>
                </div>
            </div>
            
            <div class="magic-card">
                <div class="card-header">
                    <div class="card-icon">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    <h2 class="card-title">System Information</h2>
                </div>
                
                <div id="system-info">
                    <!-- System info will be populated here -->
                </div>
            </div>
            
            <!-- Magic Unicorn Branding -->
            <div class="magic-card">
                <div class="card-header">
                    <div class="card-icon">
                        <img src="/static/magic_unicorn_logo.svg" alt="Magic Unicorn" style="width: 24px; height: 24px;"/>
                    </div>
                    <h2 class="card-title">{{ brand.product }}</h2>
                </div>
                
                <p style="color: #9ca3af; font-size: 0.875rem; margin-bottom: 1.5rem;">
                    Powered by {{ brand.company }} - Where AI meets magic. 🦄
                </p>
                
                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <a href="https://unicorncommander.com" target="_blank" class="btn btn-secondary" style="display: flex; align-items: center; gap: 0.75rem;">
                        <img src="/static/unicorn_commander_logo.svg" alt="Unicorn Commander" style="width: 24px; height: 24px;"/>
                        <span>Unicorn Commander</span>
                    </a>
                    
                    <a href="https://magicunicorn.tech" target="_blank" class="btn btn-secondary" style="display: flex; align-items: center; gap: 0.75rem;">
                        <img src="/static/magic_unicorn_logo.svg" alt="Magic Unicorn" style="width: 24px; height: 24px;"/>
                        <span>Magic Unicorn Tech</span>
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Enhanced Magic Unicorn TTS Application
        class MagicUnicornTTSPro {
            constructor() {
                this.socket = io();
                this.currentTab = 'synthesis';
                this.charts = {};
                this.autoScroll = true;
                
                this.initializeApp();
                this.setupEventListeners();
                this.setupWebSocket();
                this.startMonitoring();
            }

            initializeApp() {
                console.log('🦄✨ Magic Unicorn TTS Pro Initializing... ✨🦄');
                this.loadSettings();
                this.updateSystemStatus();
                this.initializeCharts();
            }

            setupEventListeners() {
                // Tab switching
                document.querySelectorAll('.tab-item').forEach(tab => {
                    tab.addEventListener('click', (e) => {
                        this.switchTab(e.target.closest('.tab-item').dataset.tab);
                    });
                });

                // Form submission
                document.getElementById('tts-form').addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.generateSpeech();
                });

                // Settings
                document.getElementById('save-settings').addEventListener('click', () => {
                    this.saveSettings();
                });

                // Log controls
                document.getElementById('clear-logs').addEventListener('click', () => {
                    this.clearLogs();
                });

                document.getElementById('export-logs').addEventListener('click', () => {
                    this.exportLogs();
                });

                document.getElementById('log-level-filter').addEventListener('change', (e) => {
                    this.filterLogs(e.target.value);
                });

                document.getElementById('auto-scroll-logs').addEventListener('change', (e) => {
                    this.autoScroll = e.target.checked;
                });

                // Speed slider
                document.getElementById('speed-setting').addEventListener('input', (e) => {
                    document.getElementById('speed-value').textContent = e.target.value + 'x';
                });
            }

            setupWebSocket() {
                this.socket.on('connect', () => {
                    console.log('🔌 Connected to WebSocket');
                });

                this.socket.on('new_log', (logEntry) => {
                    this.addLogEntry(logEntry);
                });

                this.socket.on('performance_update', (metrics) => {
                    this.updatePerformanceMetrics(metrics);
                });

                this.socket.on('log_buffer', (logs) => {
                    this.loadLogBuffer(logs);
                });
            }

            switchTab(tabName) {
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                document.querySelectorAll('.tab-item').forEach(tab => {
                    tab.classList.remove('active');
                });

                // Show selected tab
                document.getElementById(tabName + '-tab').classList.add('active');
                document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
                
                this.currentTab = tabName;

                // Load tab-specific content
                if (tabName === 'system') {
                    this.loadSystemInfo();
                } else if (tabName === 'monitoring') {
                    this.refreshCharts();
                }
            }

            async generateSpeech() {
                const text = document.getElementById('text-input').value;
                const voice = document.getElementById('voice-select').value;
                const method = document.getElementById('method-select').value;

                if (!text.trim()) {
                    this.showNotification('Please enter some text to synthesize! ✨', 'warning');
                    return;
                }

                this.showProgress();
                this.updateMetric('method-metric', method);

                try {
                    const startTime = Date.now();
                    
                    const response = await fetch('/synthesize', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            text: text,
                            voice: voice,
                            method: method
                        })
                    });

                    const result = await response.json();
                    const endTime = Date.now();
                    
                    if (result.success) {
                        this.handleSuccess(result, endTime - startTime);
                    } else {
                        this.handleError(result.error || 'Generation failed');
                    }
                } catch (error) {
                    this.handleError(error.message);
                } finally {
                    this.hideProgress();
                }
            }

            handleSuccess(result, duration) {
                // Update metrics
                this.updateMetric('speed-metric', (duration / 1000).toFixed(1) + 's');
                this.updateMetric('rtf-metric', result.metrics?.rtf || '0.00');
                
                // Show audio player
                this.showAudioPlayer(result.filename);
                
                // Magic success effect
                this.showNotification('Magic voice generated successfully! 🎉', 'success');
            }

            handleError(error) {
                this.showNotification(`Generation failed: ${error} 😔`, 'error');
                console.error('TTS Error:', error);
            }

            showProgress() {
                const container = document.getElementById('progress-container');
                const fill = document.getElementById('progress-fill');
                const text = document.getElementById('progress-text');
                
                container.style.display = 'block';
                
                let progress = 0;
                const interval = setInterval(() => {
                    progress += Math.random() * 15;
                    if (progress > 90) progress = 90;
                    
                    fill.style.width = progress + '%';
                    text.textContent = this.getProgressMessage(progress);
                    
                    if (progress >= 90) {
                        clearInterval(interval);
                    }
                }, 200);
                
                this.progressInterval = interval;
            }

            hideProgress() {
                if (this.progressInterval) {
                    clearInterval(this.progressInterval);
                }
                
                const fill = document.getElementById('progress-fill');
                const text = document.getElementById('progress-text');
                
                fill.style.width = '100%';
                text.textContent = 'Magic complete! ✨';
                
                setTimeout(() => {
                    document.getElementById('progress-container').style.display = 'none';
                    fill.style.width = '0%';
                }, 1000);
            }

            getProgressMessage(progress) {
                if (progress < 20) return 'Initializing magic engines... 🔮';
                if (progress < 40) return 'Loading voice models... 🎭';
                if (progress < 60) return 'NPU acceleration active... ⚡';
                if (progress < 80) return 'Synthesizing voice... 🎵';
                return 'Applying final touches... ✨';
            }

            showAudioPlayer(filename) {
                const panel = document.getElementById('audio-panel');
                const audio = document.getElementById('audio-element');
                
                panel.style.display = 'block';
                audio.src = `/audio/${filename}`;
                
                // Auto-play if enabled
                const autoPlay = document.getElementById('auto-play-setting')?.checked;
                if (autoPlay) {
                    audio.play().catch(e => console.log('Auto-play prevented by browser'));
                }
            }

            addLogEntry(logEntry) {
                const container = document.getElementById('log-container');
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                
                // Check filter
                const filter = document.getElementById('log-level-filter')?.value;
                if (filter !== 'all' && logEntry.level !== filter) {
                    return;
                }
                
                entry.innerHTML = `
                    <span class="log-timestamp">${logEntry.timestamp}</span>
                    <span class="log-level ${logEntry.level}">${logEntry.level}</span>
                    <span class="log-message">${logEntry.message}</span>
                `;
                
                container.appendChild(entry);
                
                // Auto-scroll if enabled
                if (this.autoScroll && this.currentTab === 'logs') {
                    container.scrollTop = container.scrollHeight;
                }
                
                // Limit log entries
                while (container.children.length > 1000) {
                    container.removeChild(container.firstChild);
                }
            }

            loadLogBuffer(logs) {
                const container = document.getElementById('log-container');
                container.innerHTML = '';
                
                logs.forEach(log => this.addLogEntry(log));
            }

            clearLogs() {
                document.getElementById('log-container').innerHTML = '';
            }

            exportLogs() {
                const logs = Array.from(document.querySelectorAll('.log-entry')).map(entry => {
                    return entry.textContent;
                }).join('\\n');
                
                const blob = new Blob([logs], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `magic_unicorn_logs_${new Date().toISOString().split('T')[0]}.txt`;
                a.click();
                URL.revokeObjectURL(url);
            }

            filterLogs(level) {
                const entries = document.querySelectorAll('.log-entry');
                entries.forEach(entry => {
                    const entryLevel = entry.querySelector('.log-level').textContent;
                    if (level === 'all' || entryLevel === level) {
                        entry.style.display = 'flex';
                    } else {
                        entry.style.display = 'none';
                    }
                });
            }

            async loadSettings() {
                try {
                    const response = await fetch('/settings');
                    const settings = await response.json();
                    
                    // Apply settings to UI
                    Object.keys(settings).forEach(key => {
                        const element = document.getElementById(key.replace('_', '-') + '-setting');
                        if (element) {
                            if (element.type === 'checkbox') {
                                element.checked = settings[key];
                            } else {
                                element.value = settings[key];
                            }
                        }
                    });
                } catch (error) {
                    console.error('Failed to load settings:', error);
                }
            }

            async saveSettings() {
                const settings = {};
                
                // Collect settings from UI
                document.querySelectorAll('[id$="-setting"]').forEach(element => {
                    const key = element.id.replace('-setting', '').replace('-', '_');
                    if (element.type === 'checkbox') {
                        settings[key] = element.checked;
                    } else {
                        settings[key] = element.value;
                    }
                });
                
                try {
                    const response = await fetch('/settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(settings)
                    });
                    
                    if (response.ok) {
                        this.showNotification('Settings saved successfully! ⚙️', 'success');
                    } else {
                        this.showNotification('Failed to save settings', 'error');
                    }
                } catch (error) {
                    this.showNotification('Error saving settings', 'error');
                }
            }

            async loadSystemInfo() {
                try {
                    const response = await fetch('/system');
                    const info = await response.json();
                    
                    // Update system metrics
                    this.updateMetric('npu-temp', info.cpu_temp || 'N/A');
                    this.updateMetric('npu-util', info.npu_util || 'N/A');
                    this.updateMetric('memory-usage', info.memory_usage || 'N/A');
                    this.updateMetric('disk-space', info.disk_space || 'N/A');
                    
                    // Update system info panel
                    const infoPanel = document.getElementById('system-info');
                    infoPanel.innerHTML = `
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.875rem; line-height: 1.6;">
                            <div><strong>NPU Available:</strong> ${info.npu_available ? 'Yes' : 'No'}</div>
                            <div><strong>Hardware:</strong> ${info.hardware_detected || 'Unknown'}</div>
                            <div><strong>VitisAI Provider:</strong> ${info.vitisai_provider ? 'Ready' : 'Offline'}</div>
                            <div><strong>Models Loaded:</strong> ${info.models_loaded || 0}</div>
                            <div><strong>Voices Available:</strong> ${info.voices_available || 0}</div>
                            <div><strong>MLIR-AIE:</strong> ${info.mlir_aie_ready ? 'Ready' : 'Not Available'}</div>
                            <div><strong>NPU Readiness:</strong> ${info.npu_readiness || 'Unknown'}</div>
                            <div><strong>Performance Tier:</strong> ${info.performance_tier || 'Unknown'}</div>
                        </div>
                    `;
                } catch (error) {
                    console.error('Failed to load system info:', error);
                }
            }

            initializeCharts() {
                const ctx = document.getElementById('performance-chart').getContext('2d');
                this.charts.performance = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Real-Time Factor',
                            data: [],
                            borderColor: '#8B5CF6',
                            backgroundColor: 'rgba(139, 92, 246, 0.1)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                labels: { color: '#e8e8f0' }
                            }
                        },
                        scales: {
                            x: {
                                ticks: { color: '#9ca3af' },
                                grid: { color: 'rgba(156, 163, 175, 0.1)' }
                            },
                            y: {
                                ticks: { color: '#9ca3af' },
                                grid: { color: 'rgba(156, 163, 175, 0.1)' }
                            }
                        }
                    }
                });
            }

            updatePerformanceMetrics(metrics) {
                // Update live metrics
                this.updateMetric('rtf-metric', metrics.rtf.toFixed(3));
                this.updateMetric('speed-metric', metrics.generation_time.toFixed(1) + 's');
                this.updateMetric('method-metric', metrics.method);
                
                // Update chart
                const chart = this.charts.performance;
                const time = new Date(metrics.timestamp).toLocaleTimeString();
                
                chart.data.labels.push(time);
                chart.data.datasets[0].data.push(metrics.rtf);
                
                // Keep only last 20 data points
                if (chart.data.labels.length > 20) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                }
                
                chart.update('none');
            }

            refreshCharts() {
                if (this.charts.performance) {
                    this.charts.performance.update();
                }
            }

            updateMetric(metricId, value) {
                const element = document.getElementById(metricId);
                if (element) {
                    element.textContent = value;
                }
            }

            updateSystemStatus() {
                // This would connect to the real status API
                setTimeout(() => {
                    const npuStatus = document.getElementById('npu-status');
                    const systemStatus = document.getElementById('system-status');
                    
                    npuStatus.className = 'status-badge online';
                    npuStatus.innerHTML = '<i class="fas fa-microchip"></i> <span>NPU Ready</span>';
                    
                    systemStatus.className = 'status-badge online';
                    systemStatus.innerHTML = '<i class="fas fa-circle"></i> <span>System Ready</span>';
                }, 1000);
            }

            startMonitoring() {
                // Update system info every 30 seconds
                setInterval(() => {
                    if (this.currentTab === 'system') {
                        this.loadSystemInfo();
                    }
                }, 30000);
            }

            showNotification(message, type) {
                const notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 1rem 1.5rem;
                    background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--warning)'};
                    color: white;
                    border-radius: 8px;
                    box-shadow: var(--shadow-lg);
                    z-index: 1000;
                    animation: slideIn 0.3s ease;
                `;
                notification.textContent = message;
                
                document.body.appendChild(notification);
                setTimeout(() => notification.remove(), 4000);
            }
        }

        // Initialize the enhanced app
        document.addEventListener('DOMContentLoaded', () => {
            new MagicUnicornTTSPro();
            console.log('🦄✨ Magic Unicorn TTS Pro Ready! ✨🦄');
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Enhanced main interface"""
    current_status = detect_system_status()
    return render_template_string(
        get_enhanced_template(),
        brand=BRAND_CONFIG,
        current_time=datetime.now().strftime('%H:%M:%S'),
        voices=AVAILABLE_VOICES,
        status=current_status
    )

# Include all the routes from the original file
@app.route('/synthesize', methods=['POST'])
def synthesize():
    """Real TTS synthesis endpoint"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'af_heart')
        method = data.get('method', 'auto')
        
        logger.info(f"🎵 Real TTS request: {len(text)} chars, voice={voice}, method={method}")
        
        if not text.strip():
            return jsonify({
                'success': False,
                'error': 'No text provided for synthesis'
            }), 400
        
        start_time = time.time()
        
        logger.info(f"🎵 Running real TTS synthesis in clean subprocess...")
        synthesis_result = run_synthesis_subprocess(text, voice, method)
        
        if not synthesis_result['success']:
            raise Exception(synthesis_result['error'])
        
        audio_data = synthesis_result['audio_data']
        sample_rate = synthesis_result['sample_rate']
        
        # Save real audio to file
        filename = f"real_speech_{uuid.uuid4().hex[:8]}.wav"
        audio_dir = '/tmp'
        audio_path = os.path.join(audio_dir, filename)
        
        # Write real WAV file
        import wave
        import numpy as np
        with wave.open(audio_path, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            # Convert float audio to int16 properly
            audio_int16 = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16)
            wav_file.writeframes(audio_int16.tobytes())
        
        generation_time = time.time() - start_time
        audio_duration = len(audio_data) / sample_rate
        rtf = generation_time / audio_duration
        
        # Store performance metrics
        metric_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'voice': voice,
            'text_length': len(text),
            'generation_time': generation_time,
            'audio_duration': audio_duration,
            'rtf': rtf,
            'sample_rate': sample_rate
        }
        performance_metrics.append(metric_entry)
        
        logger.info(f"✅ REAL SPEECH generated: {generation_time:.2f}s, RTF: {rtf:.3f}")
        logger.info(f"🎵 Real speech file: {audio_path} ({os.path.getsize(audio_path)} bytes)")
        
        # Emit performance update via WebSocket
        socketio.emit('performance_update', metric_entry)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'metrics': {
                'generation_time': f'{generation_time:.2f}',
                'audio_length': f'{audio_duration:.2f}',
                'rtf': f'{rtf:.3f}',
                'method_used': 'Real Kokoro TTS',
                'voice': voice,
                'sample_rate': sample_rate
            },
            'message': f'Real speech generated successfully! 🎤✨'
        })
        
    except Exception as e:
        logger.error(f"❌ Real TTS failed: {e}")
        import traceback
        logger.error(f"❌ Full error: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': f'TTS generation failed: {str(e)}'
        }), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    try:
        temp_dir = '/tmp'
        audio_path = os.path.join(temp_dir, filename)
        
        if os.path.exists(audio_path):
            logger.info(f"🎵 Serving real speech file: {filename}")
            return send_file(audio_path, mimetype='audio/wav', as_attachment=False)
        else:
            logger.error(f"❌ Real audio file not found: {filename}")
            return jsonify({'error': 'Audio file not found'}), 404
            
    except Exception as e:
        logger.error(f"❌ Audio serving error: {e}")
        return jsonify({'error': f'Could not serve audio: {str(e)}'}), 500

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings management"""
    global APP_SETTINGS
    
    if request.method == 'POST':
        data = request.get_json()
        for key, value in data.items():
            if key in APP_SETTINGS:
                APP_SETTINGS[key] = value
                logger.info(f"🔧 Setting updated: {key} = {value}")
        
        # Update logging level if changed
        if 'log_level' in data:
            logging.getLogger().setLevel(getattr(logging, data['log_level']))
        
        return jsonify({'success': True, 'settings': APP_SETTINGS})
    
    return jsonify(APP_SETTINGS)

@app.route('/logs')
def get_logs():
    """Get recent logs"""
    return jsonify(list(log_buffer))

@app.route('/metrics')
def get_metrics():
    """Get performance metrics"""
    return jsonify({
        'recent': list(performance_metrics)[-20:],  # Last 20 entries
        'summary': {
            'total_generations': len(performance_metrics),
            'avg_rtf': sum(m['rtf'] for m in performance_metrics) / len(performance_metrics) if performance_metrics else 0,
            'avg_time': sum(m['generation_time'] for m in performance_metrics) / len(performance_metrics) if performance_metrics else 0,
            'methods_used': list(set(m['method'] for m in performance_metrics))
        }
    })

@app.route('/system')
def get_system():
    """Get system information"""
    return jsonify({
        **get_system_info(),
        **detect_system_status()
    })

@app.route('/status')
def get_status():
    """Get system status"""
    current_status = detect_system_status()
    return jsonify({
        'npu_available': current_status['npu_available'],
        'vitisai_provider': current_status['vitisai_provider'],
        'voices_loaded': current_status['voices_available'],
        'models_loaded': current_status['models_loaded'],
        'mlir_aie_ready': current_status['mlir_aie_ready'],
        'hardware_detected': current_status['hardware_detected'],
        'npu_readiness': current_status['npu_readiness'],
        'acceleration_status': current_status['acceleration_status'],
        'performance_tier': current_status['performance_tier'],
        'systems': {
            'vitisai': 'ready' if current_status['vitisai_provider'] else 'offline',
            'npu': 'ready' if current_status['npu_available'] else 'offline',
            'mlir_aie': 'ready' if current_status['mlir_aie_ready'] else 'offline'
        },
        'version': BRAND_CONFIG['version']
    })

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# WebSocket handlers
@socketio.on('connect')
def handle_connect():
    """Client connected"""
    logger.info("🔌 Client connected to WebSocket")
    emit('log_buffer', list(log_buffer))

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    logger.info("🔌 Client disconnected from WebSocket")

@socketio.on('request_logs')
def handle_log_request():
    """Send log buffer to client"""
    emit('log_buffer', list(log_buffer))

# Background task to stream logs
def log_streamer():
    """Stream logs to connected clients"""
    while True:
        try:
            log_entry = log_queue.get(timeout=1)
            socketio.emit('new_log', log_entry)
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Log streaming error: {e}")

# Start log streaming thread
log_thread = threading.Thread(target=log_streamer, daemon=True)
log_thread.start()

if __name__ == '__main__':
    logger.info("🦄✨ Starting Magic Unicorn TTS Pro Web Interface ✨🦄")
    logger.info(f"🌐 Access at: http://localhost:5001") 
    logger.info(f"🎨 Enhanced experience: {BRAND_CONFIG['title']}")
    logger.info("🚀 Pro features: Logs, Settings, Monitoring, System Info!")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=False,
        allow_unsafe_werkzeug=True
    )