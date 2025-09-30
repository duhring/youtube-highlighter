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
