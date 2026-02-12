from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models, auth
from models import UserRole

# Create tables if not exist (ensures models are synced)
models.Base.metadata.create_all(bind=engine)

def seed_users():
    db = SessionLocal()
    try:
        users = [
            {
                "email": "sourcing@example.com",
                "password": "password123",
                "role": UserRole.SOURCING_BUYER,
                "name": "Sourcing Buyer"
            },
            {
                "email": "qa@example.com",
                "password": "password123",
                "role": UserRole.QA_MANAGER,
                "name": "QA Manager"
            },
            {
                "email": "procure@example.com",
                "password": "password123",
                "role": UserRole.PROCUREMENT_MANAGER,
                "name": "Procurement Manager"
            }
        ]

        for user_data in users:
            user = db.query(models.User).filter(models.User.email == user_data["email"]).first()
            if not user:
                print(f"Creating user: {user_data['email']} ({user_data['role'].value})")
                hashed_password = auth.get_password_hash(user_data["password"])
                new_user = models.User(
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    full_name=user_data["name"],
                    role=user_data["role"]
                )
                db.add(new_user)
            else:
                print(f"Updating user: {user_data['email']} to role {user_data['role'].value}")
                # Update role if changed
                user.role = user_data["role"]
                # Update password just in case
                user.hashed_password = auth.get_password_hash(user_data["password"])
        
        db.commit()
        print("Database seeding completed successfully.")

    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
