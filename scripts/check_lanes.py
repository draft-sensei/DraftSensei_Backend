from app.db.database import SessionLocal
from app.db.models import Hero
import json

db = SessionLocal()

heroes_to_check = ['Obsidia', 'Sora', 'Julian', 'Kalea', 'Hilda', 'Khaleed', 
                   'Akai', 'Fredrinn', 'Baxia', 'Valentina', 'Chang\'e', 
                   'Zhuxin', 'Lancelot', 'Miya', 'Bruno']

print("Hero Lane Priorities:")
print("=" * 60)

for name in heroes_to_check:
    h = db.query(Hero).filter(Hero.name == name).first()
    if h:
        meta = h.get_meta()
        roles_data = meta.get('attributes', {}).get('roles', {})
        lanes = roles_data.get('lane_priority', [])
        primary_role = roles_data.get('primary_role', 'Unknown')
        print(f"{name:15} [{primary_role:10}]: {lanes}")

db.close()
