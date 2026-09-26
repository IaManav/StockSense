from sqlalchemy import text

from app.database import engine


try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        print(f"{engine.dialect.name} connection successful!")
        print(result.scalar())

except Exception as e:
    print("Database connection failed!")
    print(e)
