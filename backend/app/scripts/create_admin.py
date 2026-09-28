"""Create (or promote to) an admin account.

Registration never grants the admin role -- this is the only supported way
to get one.

    python -m app.scripts.create_admin admin@example.com "Admin Name"

The password is read from a hidden prompt (or the ADMIN_PASSWORD env var for
scripted setups), never from the command line, so it doesn't land in shell
history. If the email already exists, that account is promoted instead.
"""
import getpass
import os
import sys

from app.core.security import hash_password
from app.crud.users import create_user, get_user_by_email
from app.database import SessionLocal


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    email, full_name = sys.argv[1].lower(), sys.argv[2]

    db = SessionLocal()
    try:
        user = get_user_by_email(db, email)
        if user is not None:
            user.role = "admin"
            db.commit()
            print(f"Promoted existing account {email} to admin.")
            return 0

        password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            return 1
        user = create_user(db, full_name, email, hash_password(password))
        user.role = "admin"
        db.commit()
        print(f"Created admin {email}.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
