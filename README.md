# PollySystem

---

# WORK IN PROGRESS

---
# PollySystem

A modular system to manage servers, Docker containers, and real-time metrics.  
Features:
- Plugin-based backend (FastAPI)
- React + TypeScript frontend
- Add/delete machines, retrieve CPU/RAM metrics
- Run commands on all hosts
- Manage Docker installations and docker-compose services

## Running the Project

### Prerequisites
- Docker & Docker Compose installed

### Steps
1. `cd docker`
2. `docker-compose build`
3. `docker-compose up`

Access frontend at [http://localhost:3000](http://localhost:3000)  
Access backend at [http://localhost:8000](http://localhost:8000)

Add machines, view metrics, run commands, and manage Docker components as needed.

## Next Steps
- Implement authentication & RBAC.
- Integrate a real database (e.g., Supabase).
- Add robust error handling and logging.
- Enhance UI/UX styling and add more features as needed.









uvicorn app.main:app --reload

npx tailwindcss -i .\styles\globals.css -o .\styles\output.css --watch