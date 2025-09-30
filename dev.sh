#!/bin/bash

# YouTube Highlighter - Development Launcher
# Quick development environment setup and server launcher

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[DEV]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[DEV]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[DEV]${NC} $1"
}

print_error() {
    echo -e "${RED}[DEV]${NC} $1"
}

# Check if virtual environment exists
check_venv() {
    if [[ ! -d "venv" ]]; then
        print_error "Virtual environment not found!"
        print_info "Please run setup first:"
        echo "  ./setup.sh"
        echo "  OR"  
        echo "  make setup"
        exit 1
    fi
}

# Activate virtual environment
activate_env() {
    print_info "Activating virtual environment..."
    source venv/bin/activate
    export PYTHONPATH=.
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    print_success "Development environment activated"
}

# Quick health check
health_check() {
    print_info "Running quick health check..."
    
    # Test critical imports
    if ! python -c "from moviepy.editor import VideoFileClip" 2>/dev/null; then
        print_error "MoviePy import failed - dependencies may be broken"
        print_info "Try: pip install moviepy==1.0.3"
        exit 1
    fi
    
    if ! python -c "import flask" 2>/dev/null; then
        print_error "Flask import failed"
        exit 1
    fi
    
    print_success "Health check passed"
}

# Show development info
show_info() {
    echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║       Development Environment       ║${NC}"  
    echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
    echo
    
    print_info "Python: $(python --version)"
    print_info "Project: YouTube Highlighter v2.0"
    print_info "Mode: Development (debug enabled)"
    echo
    
    print_success "Available endpoints:"
    echo "  🌐 Web Interface:    http://localhost:5000"
    echo "  📊 Health Check:     http://localhost:5000/health"
    echo
    
    print_success "Development features enabled:"
    echo "  • Auto-reload on file changes"
    echo "  • Debug mode with detailed errors"
    echo "  • Development logging"
    echo
    
    echo -e "${YELLOW}Useful commands while developing:${NC}"
    echo "  make test           - Run tests"
    echo "  make validate       - Check installation"
    echo "  make status         - Show project status"
    echo "  Ctrl+C              - Stop server"
    echo
}

# Start development server
start_server() {
    print_info "Starting development server..."
    print_warning "Server will auto-reload on file changes"
    echo
    
    # Start the server with development settings
    python app/web/server.py
}

# Handle command line arguments
handle_args() {
    case "${1:-}" in
        "test")
            print_info "Running tests..."
            python -m pytest -v
            ;;
        "validate")
            print_info "Running validation..."
            make validate 2>/dev/null || {
                print_warning "Makefile not available, running basic validation..."
                python app/cli.py --help > /dev/null
                print_success "Basic validation passed"
            }
            ;;
        "cli")
            print_info "Starting CLI mode..."
            python app/cli.py --help
            echo
            print_info "Try: python app/cli.py validate-transcript tests/sample.vtt"
            ;;
        "help"|"-h"|"--help")
            echo "YouTube Highlighter Development Launcher"
            echo
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  (no args)    Start development web server"
            echo "  test         Run test suite"
            echo "  validate     Validate installation"
            echo "  cli          Show CLI help and examples"
            echo "  help         Show this help message"
            ;;
        "")
            # Default: start web server
            show_info
            start_server
            ;;
        *)
            print_error "Unknown command: $1"
            print_info "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Main function
main() {
    check_venv
    activate_env
    health_check
    handle_args "$@"
}

# Handle interrupt signal gracefully
trap 'echo -e "\n${YELLOW}[DEV]${NC} Development server stopped"; exit 0' INT

# Run main function with all arguments
main "$@"