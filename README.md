# Tourism Project (No-Node Testable Scaffold)

This scaffolding provides a runnable backend (Flask + SQLite) and a static frontend (no Node). Use this for local testing.

Directories of interest:
- `backend/` - Flask app, DB init, requirements
- `frontend/public/` - static HTML/JS for landing and admin UI
- `database/` - SQL schema reference (optional)

Steps to test everything:
1. Start backend (PowerShell):
```powershell
cd C:\Users\LENOVO\Documents\Tourism\project-structure\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python init_db.py
python app.py
```
2. Open the frontend in a browser (no bundler):
- Open `c:\Users\LENOVO\Documents\Tourism\project-structure\frontend\public\index.html` in your browser (File -> Open) OR run a simple static server (optional).
- Admin panel: open `admin.html` in the same folder.

Default admin credentials created by `init_db.py`:
- username: `admin`
- password: `adminpass`

API is at `http://localhost:5000` by default.
