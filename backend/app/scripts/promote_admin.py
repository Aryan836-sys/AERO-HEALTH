"""Promotes an existing user to the admin role.

There is deliberately no HTTP endpoint that does this -- an
"become an admin" API route, however it were gated, would be a serious
privilege-escalation risk. The very first admin has to be created by
someone with direct database/server access, which is exactly what
running this script requires.

Run with:
    python -m app.scripts.promote_admin someone@example.com
"""
import sys

from app.crud.users import get_user_by_email
from app.database import SessionLocal


def promote(email: str) -> None:
    db = SessionLocal()
    try:
        user = get_user_by_email(db, email)
        if user is None:
            print(f"No user found with email {email!r}.")
            return
        if user.role == "admin":
            print(f"{email} is already an admin.")
            return

        previous_role = user.role
        user.role = "admin"
        db.commit()
        print(f"Promoted {email} from '{previous_role}' to 'admin'.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.promote_admin <email>")
        sys.exit(1)
    promote(sys.argv[1])