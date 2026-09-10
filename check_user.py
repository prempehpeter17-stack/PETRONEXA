"""Check a user by email without printing credentials or password hashes."""
import asyncio
import os
from sqlalchemy import select
from database import AsyncSessionLocal, UserModel

async def check():
    email = os.getenv("CHECK_EMAIL")
    if not email:
        raise SystemExit("Set CHECK_EMAIL before running check_user.py")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserModel).where(UserModel.email == email))
        user = result.scalar_one_or_none()
        if user:
            print(f"User found: {user.email}")
            print(f"Username: {user.username}")
            print(f"Role: {user.role}")
        else:
            print("No user found with that email.")

if __name__ == "__main__":
    asyncio.run(check())
