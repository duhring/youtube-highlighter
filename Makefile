# YouTube Highlighter - Makefile
# Standard development commands for easy project management

.PHONY: help install setup clean test run-web run-cli dev lint format check validate

# Default target
help:
	@echo "YouTube Highlighter - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Run full automated setup (recommended for first-time setup)"
	@echo "  make install        - Install dependencies only (requires existing venv)"
	@echo "  make clean          - Remove virtual environment and cache files"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Start development environment with auto-reload"
	@echo "  make run-web        - Start web server"
	@echo "  make run-cli        - Show CLI help and examples"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test           - Run all tests"
	@echo "  make test-verbose   - Run tests with verbose output"
	@echo "  make validate       - Validate installation and run health checks"
	@echo "  make lint          - Run code quality checks (if available)"
	@echo ""
	@echo "Utility:"
	@echo "  make activate       - Show how to activate virtual environment"
	@echo "  make status         - Show project status and health"
	@echo "  make help           - Show this help message"

# Full automated setup
setup:
	@echo "Running automated setup..."
	@./setup.sh

# Install dependencies (assumes venv is already created and activated)
install:
	@if [ ! -d "venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@echo "Installing dependencies..."
	@. venv/bin/activate && \
	python -m pip install --upgrade pip && \
	if [ -f "requirements-lock.txt" ]; then \
		pip install -r requirements-lock.txt; \
	else \
		pip install moviepy==1.0.3 && pip install -r requirements.txt; \
	fi
	@echo "✅ Dependencies installed"

# Clean up environment
clean:
	@echo "Cleaning up..."
	@rm -rf venv/
	@rm -rf .pytest_cache/
	@rm -rf __pycache__/
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -f activate.sh
	@echo "✅ Cleanup complete"

# Run all tests
test:
	@if [ ! -d "venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@echo "Running tests..."
	@. venv/bin/activate && export PYTHONPATH=. && python -m pytest

# Run tests with verbose output
test-verbose:
	@if [ ! -d "venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@echo "Running tests (verbose)..."
	@. venv/bin/activate && export PYTHONPATH=. && python -m pytest -v

# Start web server
run-web:
	@if [ ! -d "venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@echo "Starting web server..."
	@echo "🌐 Open http://localhost:5000 in your browser"
	@. venv/bin/activate && export PYTHONPATH=. && python app/web/server.py

# Start development server with auto-reload
dev:
	@if [ ! -d "venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@echo "Starting development server with auto-reload..."
	@echo "🌐 Open http://localhost:5000 in your browser"
	@echo "Press Ctrl+C to stop"
	@. venv/bin/activate && export PYTHONPATH=. && export FLASK_ENV=development && python app/web/server.py

# Show CLI help and examples
run-cli:
	@if [ ! -d "venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@echo "YouTube Highlighter CLI"
	@echo "======================"
	@. venv/bin/activate && export PYTHONPATH=. && python app/cli.py --help
	@echo ""
	@echo "Examples:"
	@echo "  Download transcript:     python app/cli.py download-transcript 'https://youtube.com/watch?v=VIDEO_ID'"
	@echo "  Generate highlights:     python app/cli.py generate 'https://youtube.com/watch?v=VIDEO_ID' transcript.vtt"
	@echo "  Validate transcript:     python app/cli.py validate-transcript tests/sample.vtt"
	@echo "  Clear cache:            python app/cli.py clear-cache --all"

# Validate installation
validate:
	@if [ ! -d "venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@echo "Running comprehensive validation..."
	@. venv/bin/activate && python validate.py

# Show project status
status:
	@echo "YouTube Highlighter - Project Status"
	@echo "===================================="
	@echo ""
	@if [ -d "venv" ]; then \
		echo "✅ Virtual environment: Ready"; \
		. venv/bin/activate && python --version | sed 's/^/   Python: /'; \
	else \
		echo "❌ Virtual environment: Not found (run 'make setup')"; \
	fi
	@echo ""
	@if [ -d ".cache" ]; then \
		CACHE_SIZE=$$(du -sh .cache 2>/dev/null | cut -f1); \
		echo "📁 Cache directory: $$CACHE_SIZE"; \
	else \
		echo "📁 Cache directory: Empty"; \
	fi
	@if [ -d "output" ]; then \
		OUTPUT_COUNT=$$(find output -name "*.html" 2>/dev/null | wc -l | tr -d ' '); \
		echo "📄 Generated pages: $$OUTPUT_COUNT"; \
	else \
		echo "📄 Generated pages: 0"; \
	fi
	@echo ""
	@if command -v git >/dev/null 2>&1 && [ -d ".git" ]; then \
		echo "Git status:"; \
		git status --porcelain | head -5; \
		if [ $$(git status --porcelain | wc -l) -gt 5 ]; then \
			echo "   ... and more"; \
		fi; \
	fi

# Show activation instructions
activate:
	@echo "To activate the YouTube Highlighter environment:"
	@echo ""
	@if [ -f "activate.sh" ]; then \
		echo "  source activate.sh"; \
	else \
		echo "  source venv/bin/activate"; \
		echo "  export PYTHONPATH=."; \
	fi
	@echo ""
	@echo "Then you can run:"
	@echo "  python app/web/server.py       # Web interface"
	@echo "  python app/cli.py --help       # CLI interface"

# Lint code (if tools are available)
lint:
	@echo "Running code quality checks..."
	@. venv/bin/activate && export PYTHONPATH=. && \
	if python -c "import flake8" 2>/dev/null; then \
		echo "Running flake8..."; \
		python -m flake8 app/ --max-line-length=100 --exclude=__pycache__ || true; \
	else \
		echo "flake8 not available, skipping lint checks"; \
	fi

# Check for common issues
check:
	@echo "Checking for common issues..."
	@if [ ! -f "requirements.txt" ]; then \
		echo "❌ requirements.txt not found"; \
	else \
		echo "✅ requirements.txt exists"; \
	fi
	@if [ ! -f "config.yaml" ]; then \
		echo "❌ config.yaml not found"; \
	else \
		echo "✅ config.yaml exists"; \
	fi
	@if [ ! -d "app" ]; then \
		echo "❌ app directory not found"; \
	else \
		echo "✅ app directory exists"; \
	fi
	@if command -v ffmpeg >/dev/null 2>&1; then \
		echo "✅ ffmpeg is available"; \
	else \
		echo "⚠️  ffmpeg not found (video processing may fail)"; \
	fi