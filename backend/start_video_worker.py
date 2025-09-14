#!/usr/bin/env python3
"""
Startup script for the background video worker
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

from app.services.background_video_worker import main

if __name__ == "__main__":
    print("🚀 Starting Background Video Worker")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    main()
