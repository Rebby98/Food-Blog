import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ----------------------------
# CHANGE THIS TO YOUR POSTGRES URL
# ----------------------------
POSTGRES_URL = "postgresql://foodblog_db_user:66SIpvmid4n3wgeyYDv2wwsPDGgOeUGT@dpg-d9aaktl8nd3s73ao745g-a.ohio-postgres.render.com/foodblog_db"

# ----------------------------
# SQLite database
# ----------------------------
SQLITE_URL = "sqlite:///instance/foodblog.db"

# ----------------------------
# Import your app and models
# ----------------------------
from app import (
    db,
    User,
    Admin,
    Category,
    Recipe,
    Blog,
    Comment,
    SavedRecipe,
)

# ----------------------------
# Create database engines
# ----------------------------
sqlite_engine = create_engine(SQLITE_URL)
postgres_engine = create_engine(POSTGRES_URL)

SQLiteSession = sessionmaker(bind=sqlite_engine)
PostgresSession = sessionmaker(bind=postgres_engine)

sqlite_session = SQLiteSession()
postgres_session = PostgresSession()

# ----------------------------
# Create tables in PostgreSQL
# ----------------------------
db.metadata.create_all(bind=postgres_engine)

print("Tables created successfully.\n")

# --------------------------------------------------
# USERS
# --------------------------------------------------
print("Migrating Users...")

for user in sqlite_session.query(User).all():

    exists = postgres_session.get(User, user.id)

    if not exists:
        postgres_session.add(
            User(
                id=user.id,
                username=user.username,
                email=user.email,
                password=user.password,
                is_verified=user.is_verified,
            )
        )

postgres_session.commit()

print("Users migrated.")

# --------------------------------------------------
# ADMINS
# --------------------------------------------------
print("Migrating Admins...")

for admin in sqlite_session.query(Admin).all():

    exists = postgres_session.get(Admin, admin.id)

    if not exists:
        postgres_session.add(
            Admin(
                id=admin.id,
                username=admin.username,
                password=admin.password,
            )
        )

postgres_session.commit()

print("Admins migrated.")

# --------------------------------------------------
# CATEGORIES
# --------------------------------------------------
print("Migrating Categories...")

for category in sqlite_session.query(Category).all():

    exists = postgres_session.get(Category, category.id)

    if not exists:
        postgres_session.add(
            Category(
                id=category.id,
                name=category.name,
            )
        )

postgres_session.commit()

print("Categories migrated.")

# --------------------------------------------------
# BLOGS
# --------------------------------------------------
print("Migrating Blogs...")

for blog in sqlite_session.query(Blog).all():

    exists = postgres_session.get(Blog, blog.id)

    if not exists:
        postgres_session.add(
            Blog(
                id=blog.id,
                title=blog.title,
                content=blog.content,
                author=blog.author,
                date_posted=blog.date_posted,
                image=blog.image,
                category=blog.category,
            )
        )

postgres_session.commit()

print("Blogs migrated.")

# --------------------------------------------------
# RECIPES
# --------------------------------------------------
print("Migrating Recipes...")

for recipe in sqlite_session.query(Recipe).all():

    exists = postgres_session.get(Recipe, recipe.id)

    if not exists:
        postgres_session.add(
            Recipe(
                id=recipe.id,
                title=recipe.title,
                description=recipe.description,
                ingredients=recipe.ingredients,
                instructions=recipe.instructions,
                cuisine=recipe.cuisine,
                diet_type=recipe.diet_type,
                prep_time=recipe.prep_time,
                goal=recipe.goal,
                image=recipe.image,
                category_id=recipe.category_id,
            )
        )

postgres_session.commit()

print("Recipes migrated.")

# --------------------------------------------------
# COMMENTS
# --------------------------------------------------
import sqlite3
from datetime import datetime

print("Migrating Comments...")

conn = sqlite3.connect("instance/foodblog.db")
cursor = conn.cursor()

cursor.execute("""
SELECT id, name, email, message, reply, status, date_posted
FROM comment
""")

rows = cursor.fetchall()

for row in rows:

    id_, name, email, message, reply, status, date_posted = row

    if isinstance(date_posted, str):
        try:
            date_posted = datetime.fromisoformat(date_posted)
        except ValueError:
            date_posted = datetime.utcnow()
    else:
        date_posted = datetime.utcnow()

    exists = postgres_session.get(Comment, id_)

    if not exists:
        postgres_session.add(
            Comment(
                id=id_,
                name=name,
                email=email,
                message=message,
                reply=reply,
                status=status,
                date_posted=date_posted,
            )
        )

postgres_session.commit()
conn.close()

print("Comments migrated.")

# --------------------------------------------------
# SAVED RECIPES
# --------------------------------------------------
print("Migrating Saved Recipes...")

for saved in sqlite_session.query(SavedRecipe).all():

    exists = postgres_session.get(SavedRecipe, saved.id)

    if not exists:
        postgres_session.add(
            SavedRecipe(
                id=saved.id,
                user_id=saved.user_id,
                recipe_id=saved.recipe_id,
            )
        )

postgres_session.commit()

print("Saved Recipes migrated.")

print("\n===============================")
print("Migration completed successfully!")
print("===============================")

sqlite_session.close()
postgres_session.close()