#!/bin/bash

cd /home/mde-admin/OceENS

# Installe (ou met à jour) l'environnement .venv depuis uv.lock
uv sync --locked --no-dev

if pgrep -f "bin/oceens$" > /dev/null; then
	echo "Website already launched"
else

	echo "Launching Website with screen"
	screen -d -m bash -c "uv run --no-sync oceens 2> >(tee -a app.error) | tee -a app.log"
fi

if pgrep -f "bin/oceens-summaries-daemon$" > /dev/null; then
	echo "Summaries generator already launched"
else

	echo "Launching Summaries generator with screen"
	screen -d -m bash -c "uv run --no-sync oceens-summaries-daemon 2> >(tee -a summaries.error) | tee -a summaries.log"
fi
