#!/bin/bash
# Script di avvio per la produzione
# Avvia l'applicazione usando Gunicorn su porta 5003 con 4 worker
gunicorn -w 4 -b 0.0.0.0:5003 "app:create_app()"
