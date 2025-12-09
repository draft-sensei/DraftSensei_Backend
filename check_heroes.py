from app.db.database import SessionLocal
from app.db.models import Hero
import json

db = SessionLocal()

heroes_to_check = ['Sora', 'Lancelot', 'Fanny', 'Ling', 'Hayabusa', 'Gusion', 'Julian', 'Valentina']

print("HERO COMPARISON:\n")
for name in heroes_to_check:
    h = db.query(Hero).filter(Hero.name == name).first()
    if h:
        meta = h.get_meta()
        attrs = meta.get('attributes', {})
        combat = attrs.get('combat', {})
        surv = attrs.get('survivability', {})
        power = attrs.get('power_curve', {})
        
        print(f"{name}:")
        print(f"  Burst: {combat.get('burst_damage')}, Sustained: {combat.get('sustained_damage')}, DPS: {combat.get('dps')}")
        print(f"  Anti-Squishy: {combat.get('anti_squishy')}, Anti-Tank: {combat.get('anti_tank')}")
        print(f"  Tankiness: {surv.get('tankiness')}, Mobility: {surv.get('mobility')}")
        print(f"  Late Game: {power.get('late_game')}, Scaling: {power.get('scaling')}")
        print()

db.close()
