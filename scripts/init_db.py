import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.db.session import init_db
print("Creating database tables...")
init_db()
print("Done!")
