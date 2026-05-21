from alembic import context
from src.database import Base, engine
import sys
import os

sys.path.insert(0, os.path.abspath("."))

def run_migrations_offline():
    context.configure(context.config.get_main_option("sqlalchemy.url"))
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()