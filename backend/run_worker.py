#!/usr/bin/env python3
"""
Standalone worker script for PulsePlan
Use this to run the timezone-aware scheduler independently of the FastAPI app
"""
import asyncio
import logging
from dotenv import load_dotenv

# Load environment first
load_dotenv()

from app.workers.main import main

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Starting PulsePlan Worker...")
    print("Use Ctrl+C to stop")
    
    asyncio.run(main())