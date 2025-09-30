#!/bin/bash

# YouTube Highlighter - Automated Setup Script
# This script sets up the development environment with all dependencies

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on supported OS
check_os() {
    print_status "Checking operating system..."
    case "$(uname -s)" in
        Darwin*)
            OS="macOS"
            print_success "Detected macOS"
            ;;
        Linux*)
            OS="Linux"
            print_success "Detected Linux"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            OS="Windows"
            print_error "Windows detected. Please use setup.bat instead."
            exit 1
            ;;
        *)
            print_error "Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac
}

# Check for required system dependencies
check_dependencies() {
    print_status "Checking system dependencies..."
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        print_status "Please install Python 3.8 or higher from https://python.org"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $PYTHON_VERSION found"
    
    # Check if Python version is >= 3.8
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        print_success "Python version is compatible"
    else
        print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    # Check pip
    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip is required but not found."
        print_status "Please install pip: https://pip.pypa.io/en/stable/installation/"
        exit 1
    fi
    print_success "pip found"
    
    # Check git (optional but recommended)
    if ! command -v git &> /dev/null; then
        print_warning "Git not found. Some features may be limited."
    else
        print_success "Git found"
    fi
    
    # Check ffmpeg (required for video processing)
    if ! command -v ffmpeg &> /dev/null; then
        print_warning "ffmpeg not found. Video processing may fail."
        if [[ "$OS" == "macOS" ]]; then
            print_status "Install with: brew install ffmpeg"
        elif [[ "$OS" == "Linux" ]]; then
            print_status "Install with: sudo apt install ffmpeg (Ubuntu/Debian) or sudo yum install ffmpeg (CentOS/RHEL)"
        fi
    else
        print_success "ffmpeg found"
    fi
}

# Create virtual environment
create_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [[ -d "venv" ]]; then
        print_warning "Virtual environment already exists. Removing old environment..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    print_success "Virtual environment created"
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    python -m pip install --upgrade pip
    print_success "pip upgraded"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Install from requirements.txt with specific versions for known problematic packages
    if [[ -f "requirements-lock.txt" ]]; then
        print_status "Installing from requirements-lock.txt (pinned versions)..."
        pip install -r requirements-lock.txt
    else
        print_status "Installing from requirements.txt..."
        # Install moviepy with specific version first to avoid conflicts
        pip install moviepy==1.0.3
        pip install -r requirements.txt
    fi
    
    print_success "Dependencies installed successfully"
}

# Validate installation
validate_installation() {
    print_status "Validating installation..."
    
    # Test critical imports
    python -c "
import sys
try:
    from moviepy.editor import VideoFileClip
    print('✓ moviepy.editor import successful')
except ImportError as e:
    print(f'✗ moviepy.editor import failed: {e}')
    sys.exit(1)

try:
    import torch
    print('✓ torch import successful')
except ImportError as e:
    print(f'✗ torch import failed: {e}')
    sys.exit(1)

try:
    from flask import Flask
    print('✓ Flask import successful')
except ImportError as e:
    print(f'✗ Flask import failed: {e}')
    sys.exit(1)

try:
    from transformers import pipeline
    print('✓ transformers import successful')
except ImportError as e:
    print(f'✗ transformers import failed: {e}')
    sys.exit(1)

print('All critical imports successful!')
"
    
    # Test CLI
    print_status "Testing CLI functionality..."
    if python app/cli.py --help > /dev/null 2>&1; then
        print_success "CLI is working"
    else
        print_error "CLI test failed"
        return 1
    fi
    
    # Test with sample file if it exists
    if [[ -f "tests/sample.vtt" ]]; then
        print_status "Testing transcript validation..."
        if python app/cli.py validate-transcript tests/sample.vtt > /dev/null 2>&1; then
            print_success "Transcript validation working"
        else
            print_warning "Transcript validation test failed (non-critical)"
        fi
    fi
    
    print_success "Installation validation complete!"
}

# Create convenience scripts
create_scripts() {
    print_status "Creating convenience scripts..."
    
    # Create activation script
    cat > activate.sh << 'EOF'
#!/bin/bash
# Activate the YouTube Highlighter virtual environment
source venv/bin/activate
export PYTHONPATH=.
echo "YouTube Highlighter environment activated!"
echo "Usage:"
echo "  python app/cli.py --help              # Show CLI help"
echo "  python app/web/server.py              # Start web server"
echo "  make run-web                          # Start web server (if make is available)"
echo "  deactivate                            # Exit virtual environment"
EOF
    chmod +x activate.sh
    
    print_success "Created activate.sh convenience script"
}

# Main setup function
main() {
    echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     YouTube Highlighter Setup       ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
    echo
    
    check_os
    check_dependencies
    create_venv
    install_dependencies
    validate_installation
    create_scripts
    
    echo
    echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Setup Complete! 🎉          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
    echo
    print_success "YouTube Highlighter is ready to use!"
    echo
    echo -e "${YELLOW}Quick Start:${NC}"
    echo "  1. Activate environment:  ${BLUE}source activate.sh${NC}"
    echo "  2. Start web server:      ${BLUE}python app/web/server.py${NC}"
    echo "  3. Open browser:          ${BLUE}http://localhost:5000${NC}"
    echo
    echo -e "${YELLOW}CLI Usage:${NC}"
    echo "  • Show help:              ${BLUE}python app/cli.py --help${NC}"
    echo "  • Download transcript:    ${BLUE}python app/cli.py download-transcript URL${NC}"
    echo "  • Generate highlights:    ${BLUE}python app/cli.py generate URL transcript.vtt${NC}"
    echo
    echo -e "${YELLOW}Development:${NC}"
    echo "  • Run tests:              ${BLUE}python -m pytest${NC}"
    echo "  • Validate transcript:    ${BLUE}python app/cli.py validate-transcript file.vtt${NC}"
    echo
    print_warning "Remember to activate the environment before using: source activate.sh"
}

# Run main function
main "$@"