"""Create an admin user from environment variables; never store credentials in source."""
import asyncio
import os
from sqlalchemy import select
import database
from security import get_password_hash

async def initialize_admin():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_username = os.getenv("ADMIN_USERNAME", admin_email or "admin")
    if not admin_email or not admin_password:
        raise SystemExit("Set ADMIN_EMAIL and ADMIN_PASSWORD before running create_admin.py")
    async with database.AsyncSessionLocal() as db:
        result = await db.execute(select(database.UserModel).where(database.UserModel.email == admin_email))
        if result.scalars().first():
            print("Admin user already exists.")
            return
        new_user = database.UserModel(username=admin_username, email=admin_email, hashed_password=get_password_hash(admin_password), role="Admin", company_name=os.getenv("ADMIN_COMPANY", ""))
        db.add(new_user)
        await db.commit()
        print(f"Admin user '{admin_email}' created successfully.")

if __name__ == "__main__":
    asyncio.run(initialize_admin())
