# Test intelligent draft suggestion system
import sys
sys.path.append('.')

from app.db.database import SessionLocal
from app.services.meta_draft_engine import MetaDraftEngine

db = SessionLocal()
engine = MetaDraftEngine(db)

print("=" * 80)
print("INTELLIGENT DRAFT SUGGESTION SYSTEM TEST")
print("=" * 80)

test_scenarios = [
    {
        "name": "FIRST PICK (No picks yet)",
        "banned": ["Fanny"],
        "enemy": [],
        "ally": []
    },
    {
        "name": "SECOND PICK (Enemy picked Jungle)",
        "banned": ["Fanny"],
        "enemy": ["Lancelot"],  # Enemy took jungle
        "ally": []
    },
    {
        "name": "THIRD/FOURTH PICK (1-2-2 pattern - We have 2 picks)",
        "banned": ["Fanny", "Ling"],
        "enemy": ["Lancelot"],  # Enemy: jungle
        "ally": ["Chang'e", "Tigreal"]  # Us: mid, roam
    },
    {
        "name": "FIFTH/SIXTH PICK (Enemy has strong mage + tank)",
        "banned": ["Fanny", "Ling"],
        "enemy": ["Valentina", "Esmeralda", "Miya"],  # Enemy: mid, exp, gold
        "ally": ["Chang'e", "Tigreal"]  # Us: mid, roam
    },
    {
        "name": "LAST PICK (Fill remaining lane)",
        "banned": ["Fanny", "Ling"],
        "enemy": ["Valentina", "Esmeralda", "Miya", "Lancelot"],
        "ally": ["Chang'e", "Tigreal", "Cici", "Bruno"]  # We need jungle
    }
]

for i, scenario in enumerate(test_scenarios, 1):
    print(f"\n{'=' * 80}")
    print(f"TEST {i}: {scenario['name']}")
    print(f"{'=' * 80}")
    
    print(f"Banned: {', '.join(scenario['banned']) if scenario['banned'] else 'None'}")
    print(f"Enemy picks: {', '.join(scenario['enemy']) if scenario['enemy'] else 'None'}")
    print(f"Ally picks: {', '.join(scenario['ally']) if scenario['ally'] else 'None'}")
    print()
    
    # Get intelligent suggestions
    result = engine.suggest_best_role_and_heroes(
        banned_heroes=scenario['banned'],
        enemy_picks=scenario['enemy'],
        ally_picks=scenario['ally']
    )
    
    print(f"🎯 RECOMMENDED LANE: {result['recommended_lane']} ({result['lane_code']})")
    print(f"💡 REASONING: {result['reasoning']}")
    print()
    print("TOP 5 HERO SUGGESTIONS:")
    print("-" * 80)
    
    for j, hero in enumerate(result['suggestions'][:5], 1):
        print(f"{j}. {hero['hero']:15} [{hero['role']:10}] Score: {hero['score']:5.2f}")
        for reason in hero['reasons'][:2]:  # Show top 2 reasons
            print(f"   • {reason}")
        print()

db.close()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
