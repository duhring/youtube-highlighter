#!/usr/bin/env python3
"""
YouTube Highlighter - Validation Script
Comprehensive validation of installation and dependencies
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Color codes for terminal output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def print_status(message: str, status: str = "info") -> None:
    """Print colored status message"""
    color_map = {
        "success": Colors.GREEN,
        "error": Colors.RED,
        "warning": Colors.YELLOW,
        "info": Colors.BLUE,
        "cyan": Colors.CYAN
    }
    color = color_map.get(status, Colors.NC)
    icon_map = {
        "success": "✅",
        "error": "❌", 
        "warning": "⚠️",
        "info": "📋",
        "cyan": "🔧"
    }
    icon = icon_map.get(status, "•")
    print(f"{color}{icon} {message}{Colors.NC}")

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible"""
    try:
        version_info = sys.version_info
        version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        
        if version_info >= (3, 8):
            print_status(f"Python version: {version_str}", "success")
            return True, version_str
        else:
            print_status(f"Python version {version_str} is too old (requires 3.8+)", "error")
            return False, version_str
    except Exception as e:
        print_status(f"Failed to check Python version: {e}", "error")
        return False, "unknown"

def check_virtual_environment() -> Tuple[bool, str]:
    """Check if running in virtual environment"""
    try:
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            venv_path = sys.prefix
            print_status(f"Virtual environment: {venv_path}", "success")
            return True, venv_path
        else:
            print_status("Not running in virtual environment", "warning")
            return False, "none"
    except Exception as e:
        print_status(f"Failed to check virtual environment: {e}", "error")
        return False, "error"

def check_module_import(module_name: str, display_name: str = None) -> Tuple[bool, str]:
    """Check if a Python module can be imported"""
    display = display_name or module_name
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')
        print_status(f"{display}: v{version}", "success")
        return True, version
    except ImportError as e:
        print_status(f"{display}: Import failed - {e}", "error")
        return False, "missing"
    except Exception as e:
        print_status(f"{display}: Error - {e}", "error")
        return False, "error"

def check_critical_modules() -> Dict[str, bool]:
    """Check all critical Python modules"""
    modules = {
        'moviepy.editor': 'MoviePy',
        'torch': 'PyTorch', 
        'transformers': 'Transformers',
        'flask': 'Flask',
        'typer': 'Typer',
        'pytube': 'PyTube',
        'yt_dlp': 'yt-dlp',
        'requests': 'Requests',
        'bs4': 'BeautifulSoup4',
        'PIL': 'Pillow',
        'numpy': 'NumPy',
        'yaml': 'PyYAML',
        'pytest': 'PyTest'
    }
    
    results = {}
    print_status("Checking Python modules...", "cyan")
    
    for module_name, display_name in modules.items():
        success, _ = check_module_import(module_name, display_name)
        results[module_name] = success
    
    return results

def check_system_commands() -> Dict[str, bool]:
    """Check for required system commands"""
    commands = {
        'ffmpeg': 'FFmpeg (required for video processing)',
        'git': 'Git (optional, for development)',
        'python3': 'Python 3'
    }
    
    results = {}
    print_status("Checking system commands...", "cyan")
    
    for cmd, description in commands.items():
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            # FFmpeg outputs version to stderr and returns exit code 8, but this is normal
            if result.returncode == 0 or (cmd == 'ffmpeg' and 'ffmpeg version' in result.stderr):
                print_status(f"{description}: Available", "success")
                results[cmd] = True
            else:
                print_status(f"{description}: Not working", "error")
                results[cmd] = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            if cmd == 'git':
                print_status(f"{description}: Not found (optional)", "warning")
                results[cmd] = False
            else:
                print_status(f"{description}: Not found", "error")
                results[cmd] = False
        except Exception as e:
            print_status(f"{description}: Error checking - {e}", "error")
            results[cmd] = False
    
    return results

def check_project_structure() -> Dict[str, bool]:
    """Check if required project files exist"""
    required_files = {
        'config.yaml': 'Configuration file',
        'requirements.txt': 'Dependencies list',
        'app/cli.py': 'CLI interface',
        'app/web/server.py': 'Web server',
        'app/main.py': 'Main application',
        'tests/sample.vtt': 'Sample test data'
    }
    
    results = {}
    print_status("Checking project structure...", "cyan")
    
    for file_path, description in required_files.items():
        path = Path(file_path)
        if path.exists():
            print_status(f"{description}: Found", "success")
            results[file_path] = True
        else:
            print_status(f"{description}: Missing ({file_path})", "error")
            results[file_path] = False
    
    return results

def check_cli_functionality() -> bool:
    """Test basic CLI functionality"""
    print_status("Testing CLI functionality...", "cyan")
    
    try:
        # Test CLI help
        result = subprocess.run([
            sys.executable, 'app/cli.py', '--help'
        ], capture_output=True, text=True, timeout=10, cwd=project_root)
        
        if result.returncode == 0 and 'Usage:' in result.stdout:
            print_status("CLI help command: Working", "success")
            
            # Test transcript validation if sample exists
            sample_path = Path('tests/sample.vtt')
            if sample_path.exists():
                result = subprocess.run([
                    sys.executable, 'app/cli.py', 'validate-transcript', str(sample_path)
                ], capture_output=True, text=True, timeout=10, cwd=project_root,
                  env={**os.environ, 'PYTHONPATH': str(project_root)})
                
                if result.returncode == 0:
                    print_status("CLI transcript validation: Working", "success")
                    return True
                else:
                    print_status(f"CLI transcript validation failed: {result.stderr}", "error")
                    return False
            else:
                print_status("Sample transcript not found, skipping validation test", "warning")
                return True
        else:
            print_status(f"CLI help failed: {result.stderr}", "error")
            return False
            
    except subprocess.TimeoutExpired:
        print_status("CLI test timed out", "error")
        return False
    except Exception as e:
        print_status(f"CLI test error: {e}", "error")
        return False

def generate_report(results: Dict) -> None:
    """Generate final validation report"""
    print("\n" + "="*60)
    print_status("VALIDATION REPORT", "cyan")
    print("="*60)
    
    # Count successes and failures
    total_checks = 0
    passed_checks = 0
    critical_failures = []
    
    for category, items in results.items():
        print_status(f"\n{category.upper()}:", "cyan")
        if isinstance(items, dict):
            for item, status in items.items():
                total_checks += 1
                if status:
                    passed_checks += 1
                    print(f"  ✅ {item}")
                else:
                    print(f"  ❌ {item}")
                    if category in ['modules', 'cli'] or item == 'ffmpeg':
                        critical_failures.append(f"{category}/{item}")
        elif isinstance(items, bool):
            total_checks += 1
            if items:
                passed_checks += 1
                print(f"  ✅ {category}")
            else:
                print(f"  ❌ {category}")
                critical_failures.append(category)
    
    print("\n" + "="*60)
    print_status(f"SUMMARY: {passed_checks}/{total_checks} checks passed", "cyan")
    
    if not critical_failures:
        print_status("🎉 All critical components are working!", "success")
        print_status("YouTube Highlighter is ready to use!", "success")
        return True
    else:
        print_status("❌ Critical issues found:", "error")
        for failure in critical_failures:
            print(f"  • {failure}")
        print_status("\nPlease fix these issues before using YouTube Highlighter", "error")
        return False

def main():
    """Main validation function"""
    print_status("YouTube Highlighter - Installation Validator", "cyan")
    print("="*60)
    
    # Collect all validation results
    results = {}
    
    # Check Python and environment
    python_ok, python_version = check_python_version()
    venv_ok, venv_path = check_virtual_environment()
    results['python'] = python_ok
    results['venv'] = venv_ok
    
    # Check modules
    results['modules'] = check_critical_modules()
    
    # Check system commands  
    results['system'] = check_system_commands()
    
    # Check project structure
    results['structure'] = check_project_structure()
    
    # Check CLI functionality
    results['cli'] = check_cli_functionality()
    
    # Generate final report
    success = generate_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()