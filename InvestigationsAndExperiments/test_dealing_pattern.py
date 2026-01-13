"""
Simple test to verify card dealing alternation with minimal game.
"""

from taki_simulation import run_single_game

print("\n" + "=" * 70)
print("🧪 TESTING CARD DEALING ALTERNATION")
print("=" * 70)
print("\nRunning a single test game with seed=42...")
print("The debug output from bp_taki.py will show the dealing sequence.\n")
print("-" * 70)

# Run one game with silent=False to see all the output including our debug prints
result = run_single_game(
    game_number=1,
    seed=42,
    num_cards=8,
    starting_player=0,
    silent=False
)

print("-" * 70)

if result:
    print(f"\n✅ Game completed successfully!")
    print(f"   Winner: Player {result.winner}")
    print(f"   Starting player: {result.starting_player}")
    print(f"   Total events: {result.event_count}")
else:
    print(f"\n❌ Game failed to complete")

print("\n" + "=" * 70)
print("📊 ANALYSIS:")
print("=" * 70)
print("\nLook at the '🃏 CARD DEALING SEQUENCE' output above.")
print("\nIf alternation is CORRECT, you should see:")
print("  Card  1: Dealing to Player 0")
print("  Card  2: Dealing to Player 1")
print("  Card  3: Dealing to Player 0")
print("  Card  4: Dealing to Player 1")
print("  ... (and so on)")
print("\nIf alternation is WRONG (old bug), you would see:")
print("  Card  1-8:  All to Player 0")
print("  Card  9-16: All to Player 1")
print("\n" + "=" * 70)
