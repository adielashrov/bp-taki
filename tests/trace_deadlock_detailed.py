#!/usr/bin/env python3
"""
Detailed trace of deadlock for seed 4 with TAKI strategy
"""

import logging
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from datetime import datetime
from taki_simulation import run_single_game_basic_vs_external, build_game_schedule

# Configure detailed logging to both file and console
log_filename = f'deadlock_trace_seed4_{datetime.now().strftime("%H-%M-%S")}.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Build schedule to get the right starting player
schedule = build_game_schedule(
    num_games=500,
    start_seed=0,
    starting_player=-1,
    balanced_starting_players=True,
)
seed_to_start = {seed: starter for seed, starter in schedule}

# Run with detailed logging
seed = 4
starter = seed_to_start[seed]
logger.info(f"===== Tracing deadlock for seed {seed} with starting_player={starter} =====")

result = run_single_game_basic_vs_external(
    game_number=seed+1,
    seed=seed,
    player_0_strategy='taki',
    starting_player=starter,
    silent=False  # Enable all logging
)

logger.info(f"Game result: {result}")
logger.info(f"Deadlock: {result.ended_in_deadlock if result else 'None'}")
logger.info(f"Events: {result.event_count if result else 'None'}")
logger.info(f"Log written to: {log_filename}")
