import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import AsyncSessionLocal
from app.models import User, Role
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def init_db():
    async with AsyncSessionLocal() as session:
        # Check if admin exists
        # In a real app we'd query by email, here we assume clean slate or check first
        from sqlalchemy import select
        
        # Seed Admin
        admin_email = "admin@acturesolutions.com"
        result = await session.execute(select(User).where(User.email == admin_email))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print(f"Seeding admin user: {admin_email}")
            admin_user = User(
                email=admin_email,
                hashed_password=pwd_context.hash("admin"),
                display_name="Admin User",
                role=Role.ADMIN
            )
            session.add(admin_user)
        
        # Seed User
        user_email = "user@acturesolutions.com"
        result = await session.execute(select(User).where(User.email == user_email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"Seeding standard user: {user_email}")
            standard_user = User(
                email=user_email,
                hashed_password=pwd_context.hash("user"),
                display_name="Standard User",
                role=Role.USER
            )
            session.add(standard_user)
            
        await session.commit()

if __name__ == "__main__":
    asyncio.run(init_db())
