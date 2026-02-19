"""
Launch script for Gradio UI.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logging_config import setup_logging
from src.ui.gradio_app import launch_ui


def main():
    """Main entry point for UI launcher."""
    
    parser = argparse.ArgumentParser(
        description="Launch Business AI Copilot Gradio UI"
    )
    
    parser.add_argument(
        '--share',
        action='store_true',
        help='Create a public sharing link (Gradio share)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=7860,
        help='Port to run server on (default: 7860)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1, use 0.0.0.0 for network access)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Print startup info
    print("=" * 60)
    print("🤖 Business AI Copilot - Gradio UI")
    print("=" * 60)
    print()
    print(f"Server: http://{args.host}:{args.port}")
    if args.share:
        print("Share: Enabled (public link will be generated)")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    # Launch UI
    try:
        launch_ui(
            share=args.share,
            server_name=args.host,
            server_port=args.port
        )
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()