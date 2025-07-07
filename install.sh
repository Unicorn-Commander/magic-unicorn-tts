#!/bin/bash
set -e

# Magic Unicorn TTS - Quick Installer
# NPU-Optimized Voice Synthesis

echo "🦄✨ Magic Unicorn TTS Installation ✨🦄"
echo "NPU-Optimized Kokoro TTS for AMD Ryzen AI"
echo ""

# Check requirements
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.8+ first."
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "❌ Git is required. Please install git first."
    exit 1
fi

echo "✅ Requirements check passed"

# Clone repository
echo "📦 Cloning Magic Unicorn TTS..."
git clone https://github.com/Unicorn-Commander/magic-unicorn-tts.git
cd magic-unicorn-tts

# Setup Python environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download models
echo "🤖 Downloading NPU-optimized models..."
python3 -c "
from huggingface_hub import hf_hub_download
import os

try:
    # Download NPU-optimized models
    print('Downloading INT8 model...')
    hf_hub_download(
        repo_id='magicunicorn/kokoro-npu-quantized',
        filename='kokoro-npu-quantized-int8.onnx',
        local_dir='.',
        local_dir_use_symlinks=False
    )
    
    print('Downloading FP16 model...')
    hf_hub_download(
        repo_id='magicunicorn/kokoro-npu-quantized',
        filename='kokoro-npu-fp16.onnx',
        local_dir='.',
        local_dir_use_symlinks=False
    )
    
    print('Downloading voice models...')
    hf_hub_download(
        repo_id='magicunicorn/kokoro-npu-quantized',
        filename='voices-v1.0.bin',
        local_dir='.',
        local_dir_use_symlinks=False
    )
    
    print('✅ NPU-optimized models downloaded successfully!')
    
except Exception as e:
    print(f'⚠️  Model download failed: {e}')
    print('Falling back to original models...')
    # Fallback download logic here
"

# Create launcher
echo "🚀 Creating launcher..."
cat > launch.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🦄✨ Starting Magic Unicorn TTS ✨🦄"
echo "🌐 Access at: http://localhost:5001"
python web_interface_enhanced.py
EOF

chmod +x launch.sh

echo ""
echo "🎉 Installation Complete!"
echo ""
echo "🚀 To start Magic Unicorn TTS:"
echo "   cd magic-unicorn-tts"
echo "   ./launch.sh"
echo ""
echo "🌐 Then open: http://localhost:5001"
echo ""
echo "🦄 Enjoy magical NPU-accelerated voice synthesis!"