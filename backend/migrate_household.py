"""One-time migration: move flat data/ files into data/h_1/, add household_id to users."""

import json
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
H1_DIR = DATA_DIR / "h_1"

FILES_TO_MOVE = [
    "transactions.csv",
    "summary.json",
    "categories_extra.json",
]


def migrate():
    H1_DIR.mkdir(parents=True, exist_ok=True)

    moved = []
    for filename in FILES_TO_MOVE:
        src = DATA_DIR / filename
        dst = H1_DIR / filename
        if src.exists():
            if dst.exists():
                print(f"  SKIP  {filename}  (already exists in h_1/)")
            else:
                shutil.move(str(src), str(dst))
                moved.append(filename)
                print(f"  MOVED {filename}  →  h_1/{filename}")
        else:
            print(f"  SKIP  {filename}  (not found in data/)")

    users_file = DATA_DIR / "users.json"
    if not users_file.exists():
        print("\nusers.json not found — nothing to patch.")
        return

    users = json.loads(users_file.read_text(encoding="utf-8"))
    patched = 0
    for user in users:
        if "household_id" not in user:
            user["household_id"] = 1
            patched += 1

    users_file.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nPatched {patched} user(s) in users.json with household_id=1")
    print(f"\nMoved {len(moved)} file(s). Migration complete.")


if __name__ == "__main__":
    print("VittaMantri → household migration")
    print("=" * 40)
    migrate()
