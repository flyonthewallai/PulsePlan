"""
Main worker entry point for PulsePlan scheduling system
Starts the timezone-aware scheduler for efficient briefing delivery
"""
import asyncio
import logging
import signal
import sys
from typing import Optional

from ..scheduling.timezone_scheduler import get_timezone_scheduler

logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages the worker processes and schedulers"""
    
    def __init__(self):
        self.timezone_scheduler = None
        self.running = False
    
    async def start(self):
        """Start all worker processes"""
        try:
            logger.info("Starting PulsePlan worker manager...")
            
            # Start timezone-aware scheduler
            self.timezone_scheduler = get_timezone_scheduler()
            await self.timezone_scheduler.start()
            
            self.running = True
            logger.info("Worker manager started successfully")
            
            # Keep the process running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting worker manager: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop all worker processes"""
        logger.info("Stopping worker manager...")
        self.running = False
        
        if self.timezone_scheduler:
            await self.timezone_scheduler.stop()
        
        logger.info("Worker manager stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker_manager = WorkerManager()
    worker_manager.setup_signal_handlers()
    
    try:
        await worker_manager.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Worker manager failed: {e}")
        sys.exit(1)
    finally:
        await worker_manager.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")