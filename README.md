# Student Attendance Management System

A Flask + MySQL application for managing students, marking attendance, viewing attendance history and reports, and exporting attendance to Excel.

## 1. Run locally on Windows

### Requirements
- Python 3.11 or 3.12
- MySQL Server running locally (for example, MySQL 8)
- Git (optional for local run)

### Setup
Open PowerShell in this project folder and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create the database in MySQL Workbench or the MySQL command line:

```sql
CREATE DATABASE attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Set the database connection and initial admin credentials in PowerShell (replace the example values):

```powershell
$env:MYSQL_HOST="localhost"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="YOUR_MYSQL_PASSWORD"
$env:MYSQL_DATABASE="attendance_db"
$env:DB_SSL_DISABLED="true"
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="Choose-A-Strong-Password"
python init_db.py
python app.py
```

Open http://127.0.0.1:5000 in your browser. Sign in with the `ADMIN_USERNAME` and `ADMIN_PASSWORD` values you chose. The password is stored as a hash.

## 2. Push to GitHub

Create an empty repository on GitHub (do not add a README if this project already has one). From PowerShell in the project folder run:

```powershell
git init
git add .
git status
git commit -m "Prepare student attendance app for deployment"
git branch -M main
git remote add origin https://github.com/YOUR-GITHUB-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace the remote URL with your own repository URL. Check `git status` before committing and make sure no `.env`, passwords, or virtual environment files are included. If `origin` already exists, use `git remote set-url origin YOUR-REPOSITORY-URL` instead of `git remote add origin`.

## 3. Deploy on Render

Render does not provide a persistent MySQL database with a normal web service. Use a MySQL provider that is reachable from Render (for example, an existing Aiven MySQL service), and create a database for this app. Do not use `localhost` for a remote database.

1. Push the project to GitHub.
2. In Render, choose **New + → Web Service** and connect the repository.
3. Set **Runtime** to Python.
4. Set **Build Command** to `pip install -r requirements.txt`.
5. Set **Start Command** to `gunicorn app:app`.
6. Add these Environment Variables in Render, using the values supplied by your MySQL provider:
   - `MYSQL_HOST` = database host
   - `MYSQL_PORT` = database port
   - `MYSQL_USER` = database username
   - `MYSQL_PASSWORD` = database password
   - `MYSQL_DATABASE` = database name
   - `DB_SSL_DISABLED` = `false` for a TLS-enabled hosted MySQL service (normally keep SSL enabled)
   - `SECRET_KEY` = a long, random secret value
   - `ADMIN_USERNAME` = desired admin username
   - `ADMIN_PASSWORD` = strong admin password of at least 8 characters
7. Deploy the service.
8. After deployment, open Render's **Shell** for the service if available and run `python init_db.py` once to create tables and the admin account. If Shell is unavailable on your plan, run `init_db.py` locally with the hosted database connection environment variables set to the same values. Do not put database credentials in source code or GitHub.

### Notes
- The hosted database must allow connections from Render and require the correct TLS settings. Follow your database provider's connection instructions if it requires a CA certificate or other SSL configuration.
- Run `python init_db.py` again after creating a fresh database. It creates missing tables and creates the admin user only if that username does not already exist.
- Keep the `venv` / `.venv` directory out of GitHub. The included `.gitignore` does this.
- If you have already committed a real password to a public repository, change that password and remove the secret from the repository history.
