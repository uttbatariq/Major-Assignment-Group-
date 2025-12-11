# Backend (Flask + SQLite)

This backend is a small Flask app using SQLite for quick local testing. No Node.js required.

Quick start (PowerShell):

```powershell
cd C:\Users\LENOVO\Documents\Tourism\project-structure\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# initialize DB (creates default admin: username=admin password=adminpass)
python init_db.py
# run the API
python app.py
```

API summary (for manual testing):
- GET `/` - root
- POST `/admin/login` {username,password} -> {token}
- GET `/tours` -> list tours
- POST `/tours` (admin) -> create tour (header `X-ADMIN-TOKEN` required)
- GET `/tours/<id>`
- PUT `/tours/<id>` (admin)
- DELETE `/tours/<id>` (admin)
- POST `/registrations` {tourId, seats, user:{name,email,phone}} -> register
- GET `/registrations/tour/<id>` (admin) -> registrations for tour
- GET `/analytics/tour/<id>/registrations` (admin)
- GET `/analytics/tour/<id>/revenue` (admin)
- GET `/analytics/tour/history` (admin)

Notes:
- Admin token must be sent in header `X-ADMIN-TOKEN` for protected endpoints.
- DB file `tourism.db` is created in `backend` directory.
