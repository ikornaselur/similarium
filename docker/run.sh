#!/usr/bin/env bash

# Apply migrations if needed
alembic upgrade head

python -m similarium.app
