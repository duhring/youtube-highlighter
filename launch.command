#!/bin/bash

# YouTube Highlighter - macOS Double-Click Launcher
# This file can be double-clicked in Finder to launch the application

# Change to the script's directory
cd "$(dirname "$0")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Function to open browser after delay
open_browser() {
    sleep 3
    print_info "Opening browser..."
    open "http://localhost:5000" 2>/dev/null
}

# Main launcher function
main() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     YouTube Highlighter Launcher    ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
    echo
    
    print_info "Starting YouTube Highlighter..."
    print_info "Working directory: $(pwd)"
    echo
    
    # Check if setup is needed
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
                echo
                read -p "Press Enter to exit..."
                exit 1
            fi
        else
            print_error "setup.sh not found!"
            print_info "Please ensure you're in the YouTube Highlighter directory."
            echo
            read -p "Press Enter to exit..."
            exit 1
        fi
    else
        print_success "Environment already set up!"
    fi
    
    # Activate environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    export PYTHONPATH=.
    
    # Quick health check
    print_info "Performing health check..."
    if ! python -c "from moviepy.editor import VideoFileClip" 2>/dev/null; then
        print_error "Environment health check failed!"
        print_info "Try running setup again or check the logs above."
        echo
        read -p "Press Enter to exit..."
        exit 1
    fi
    
    print_success "Health check passed!"
    echo
    
    # Start browser opener in background
    open_browser &
    
    # Show launch info
    print_success "🚀 Starting YouTube Highlighter web server..."
    print_success "🌐 Browser will open automatically at: http://localhost:5000"
    print_warning "📋 Keep this window open while using the application"
    print_warning "🛑 Press Ctrl+C to stop the server"
    echo
    echo "Ready! Starting server..."
    echo
    
    # Start the server
    python app/web/server.py
    
    # Server stopped
    echo
    print_info "Server stopped."
    print_info "Thank you for using YouTube Highlighter!"
    echo
    read -p "Press Enter to close..."
}

# Handle interrupt signal gracefully
trap 'echo -e "\n${YELLOW}[LAUNCHER]${NC} Shutting down server..."; exit 0' INT

# Run main function
main