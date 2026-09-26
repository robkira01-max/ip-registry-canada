#!/usr/bin/env python3
"""Crée l'utilisateur administrateur initial.

Usage : python scripts/create_admin.py [--username admin] [--email admin@cipo.ca]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal, init_db
from models.user import User, UserRole
from core.security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Seed utilisateur admin")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--email", default="admin@registreip.ca")
    parser.add_argument("--password", default="Admin2026!")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == args.username).first()
        if existing:
            print(f"Utilisateur '{args.username}' existe déjà.")
            return

        user = User(
            username=args.username,
            email=args.email,
            hashed_password=hash_password(args.password),
            role=UserRole.admin,
        )
        db.add(user)
        db.commit()
        print(f"Admin créé : {args.username} / {args.password}")
        print("IMPORTANT : changez le mot de passe en production.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
