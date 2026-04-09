#!/usr/bin/env python3
"""
Debug script to trace deadlock for seed 3
"""

import logging
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from datetime import datetime
from taki_simulation import run_single_game_basic_vs_external

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'debug_seed3_{datetime.now().strftime("%H-%M-%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting debug trace for seed 3")

# Run the game with detailed logging enabled (silent=False)
result = run_single_game_basic_vs_external(
    game_number=7,
    seed=3,
    silent=False  # Enable logging
)

if result:
    logger.info(f"Game result: {result}")
    logger.info(f"Deadlock: {result.ended_in_deadlock}")
    logger.info(f"Events: {result.event_count}")
else:
    logger.error("Game returned None result")
