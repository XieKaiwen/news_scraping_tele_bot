echo "Running db migration"
read -p "Enter a name for the migration: " migration_name

alembic revision --autogenerate -m "$migration_name"
alembic upgrade head