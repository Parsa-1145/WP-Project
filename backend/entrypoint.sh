#!/bin/bash
set -e
collect_static() {
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear
    echo "Static files collected successfully!"
}

migrate() {
    echo "Running database migrations..."
    python manage.py migrate --noinput
    echo "Database migrations completed successfully!"
}

wait_for_db() {
    if [ "$DATABASE_ENGINE" = "sqlite" ]; then
        echo -e "${GREEN}SQLite detected. Skipping network database check.${NC}"
        return 0
    fi

    echo -e "${YELLOW}Waiting for the network database to be ready...${NC}"
    until python manage.py check --database default > /dev/null 2>&1; do
        sleep 2
    done
    echo -e "${GREEN}Database is ready!${NC}"
}

echo "Starting entrypoint script..."

wait_for_db
collect_static
migrate

echo "Starting the main application process..."
exec "$@"

