#!/bin/bash

# YouTube Highlighter - Universal Shell Launcher
# Cross-platform launcher that works on macOS, Linux, and other Unix systems

set -e  # Exit on any error

# Change to the script's directory
cd "$(dirname "$0")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to print colored output
print_info() {
    echo -e "${BLUE}[LAUNCHER]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[LAUNCHER]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[LAUNCHER]${NC} $1"
}

print_error() {
    echo -e "${RED}[LAUNCHER]${NC} $1"
}

print_highlight() {
    echo -e "${CYAN}[LAUNCHER]${NC} $1"
}

# Detect operating system
detect_os() {
    case "$(uname -s)" in
        Darwin*)
            OS="macOS"
            BROWSER_CMD="open"
            ;;
        Linux*)
            OS="Linux"
            BROWSER_CMD="xdg-open"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            OS="Windows"
            BROWSER_CMD="start"
            ;;
        *)
            OS="Unix"
            BROWSER_CMD="xdg-open"
            ;;
    esac
}

# Function to open browser after delay
open_browser() {
    sleep 3
    print_info "Opening browser..."
    if command -v $BROWSER_CMD &> /dev/null; then
        $BROWSER_CMD "http://localhost:5000" 2>/dev/null &
    else
        print_warning "Could not auto-open browser. Please visit: http://localhost:5000"
    fi
}

# Check for required commands
check_requirements() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not found."
        print_info "Please install Python 3.8 or higher from https://python.org"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        print_success "Python $PYTHON_VERSION detected"
    else
        print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
}

# Setup if needed
run_setup_if_needed() {
    if [[ ! -d "venv" ]]; then
        print_warning "First time setup required!"
        print_info "Running automated setup..."
        echo
        
        if [[ -f "setup.sh" ]]; then
            chmod +x setup.sh
            ./setup.sh
            
            if [[ $? -ne 0 ]]; then
                print_error "Setup failed!"
                print_info "Please check the error messages above."
                exit 1
            fi
        else
            print_error "setup.sh not found!"
            print_info "Please ensure you're in the YouTube Highlighter directory."
            exit 1
        fi
    else
        print_success "Environment already configured!"
    fi
}

# Activate environment and run health check
prepare_environment() {
    print_info "Activating virtual environment..."
    source venv/bin/activate
    export PYTHONPATH=.
    
    # Quick health check
    print_info "Performing health check..."
    if ! python -c "from moviepy.editor import VideoFileClip" 2>/dev/null; then
        print_error "Environment health check failed!"
        print_info "Critical modules are missing. Try running setup again."
        exit 1
    fi
    
    if ! python -c "import flask" 2>/dev/null; then
        print_error "Flask is not available!"
        print_info "Web server cannot start. Please check your installation."
        exit 1
    fi
    
    print_success "Health check passed!"
}

# Main launcher function
main() {
    # Clear screen if running interactively
    if [[ -t 1 ]]; then
        clear
    fi
    
    echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     YouTube Highlighter Launcher    ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
    echo
    
    detect_os
    print_highlight "Platform: $OS"
    print_info "Working directory: $(pwd)"
    echo
    
    check_requirements
    run_setup_if_needed
    prepare_environment
    
    echo
    
    # Start browser opener in background
    open_browser &
    
    # Show launch info
    print_success "🚀 Starting YouTube Highlighter web server..."
    print_success "🌐 Browser will open automatically at: http://localhost:5000"
    print_warning "📋 Keep this terminal window open while using the application"
    print_warning "🛑 Press Ctrl+C to stop the server"
    echo
    
    # Additional helpful info
    print_info "Quick links:"
    echo "  • Web Interface: http://localhost:5000"
    echo "  • Health Check:  http://localhost:5000/health"
    echo "  • Stop Server:   Ctrl+C in this window"
    echo
    
    print_highlight "Ready! Starting server..."
    echo
    
    # Start the server
    python app/web/server.py
    
    # Server stopped
    echo
    print_info "Server stopped."
    print_success "Thank you for using YouTube Highlighter!"
    
    # Keep window open if running interactively
    if [[ -t 1 ]]; then
        echo
        read -p "Press Enter to close..."
    fi
}

# Handle interrupt signal gracefully
trap 'echo -e "\n${YELLOW}[LAUNCHER]${NC} Shutting down server..."; exit 0' INT

# Handle command line arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "YouTube Highlighter Universal Launcher"
        echo
        echo "Usage: $0 [option]"
        echo
        echo "Options:"
        echo "  (no args)    Launch web interface"
        echo "  help         Show this help message"
        echo "  setup        Run setup only (don't launch)"
        echo "  validate     Validate installation only"
        echo "  cli          Show CLI interface"
        echo
        ;;
    "setup")
        detect_os
        check_requirements
        run_setup_if_needed
        print_success "Setup complete! Run './launch.sh' to start the application."
        ;;
    "validate")
        detect_os
        check_requirements
        if [[ -f "validate.py" ]]; then
            source venv/bin/activate 2>/dev/null || true
            python3 validate.py
        else
            print_warning "validate.py not found, running basic checks..."
            run_setup_if_needed
            prepare_environment
            print_success "Basic validation passed!"
        fi
        ;;
    "cli")
        detect_os
        check_requirements
        run_setup_if_needed
        source venv/bin/activate
        export PYTHONPATH=.
        python app/cli.py --help
        echo
        print_info "Example: python app/cli.py validate-transcript tests/sample.vtt"
        ;;
    "")
        # Default: launch web interface
        main
        ;;
    *)
        print_error "Unknown option: $1"
        print_info "Use '$0 help' for available options"
        exit 1
        ;;
esac