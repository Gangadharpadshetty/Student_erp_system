# Student ERP

A role-based school management app built with FastAPI, Jinja templates, and SQLAlchemy. It provides separate workspaces for administrators, teachers, and students.

## Features

- Admin: create student and teacher accounts, browse profiles, enter marks, manage academic summaries, and create or resolve support tickets.
- Teacher: access the teacher workspace to record attendance and marks.
- Student: view the academic report and submit a correction/support ticket.
- Database: SQLite by default, with PostgreSQL supported through `DATABASE_URL`.

## Requirements

- Python 3.10 or newer
- pip

## Run Locally

From the repository root, create and activate a virtual environment, then install the dependencies.

Windows PowerShell:

```powershell
py -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

Start the development server:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. The API documentation is at `http://127.0.0.1:8000/docs`.

The default database is `sqlite:///./student_erp.db`. To use PostgreSQL, set `DATABASE_URL` in the environment or in a root `.env` file, for example:

```text
DATABASE_URL=postgresql://username:password@host:5432/database_name
```

The application does not create tables automatically at server startup. Running `seed_db.py` creates the tables and inserts the sample records:

```bash
python seed_db.py
```

`seed_db.py` operates on the database configured by `DATABASE_URL`; verify the target before running it. `run_app.bat` and `run_app.sh` also run the seed script before starting the server. To start without seeding, use the `uvicorn` command above.

## Sample Accounts

The current development admin account is hard-coded in `app/api/controllers/auth_controller.py`:

| Role | Email | Password | Notes |
| :--- | :--- | :--- | :--- |
| Admin | `admin@erp.com` | `admin123` | Available without seeding |
| Teacher | `math_teacher@erp.com` | `pass123` | Created by `seed_db.py` |
| Teacher | `sci_teacher@erp.com` | `pass123` | Created by `seed_db.py` |
| Student | `student1@erp.com` | `pass123` | Created by `seed_db.py` |
| Student | `student2@erp.com` | `pass123` | Created by `seed_db.py` |
| Student | `student3@erp.com` | `pass123` | Created by `seed_db.py` |

These credentials are for local development only. Replace the hard-coded admin authentication and sample passwords before deploying to a public environment.

## Role Pages

| Role | Page |
| :--- | :--- |
| Public | `/` |
| Sign in | `/auth/login-page` |
| Admin dashboard | `/admin/dashboard` |
| Manage users | `/admin/users` |
| Academic control | `/admin/academics` |
| Ticket center | `/admin/tickets` |
| Teacher workspace | `/teacher/dashboard` |
| Student report | `/student/dashboard` |

## Tests

Run the test suite from the repository root with the virtual environment active:

```bash
pytest -q
```

## Project Layout

```text
app/
	api/controllers/   Business logic
	routers/           HTTP routes
	templates/         Jinja HTML pages
	static/            CSS and other static assets
	models.py          SQLAlchemy models
	database.py        Database configuration and session dependency
tests/               Automated tests
seed_db.py           Optional sample data initialization
```

## Data Model

The SQLAlchemy models are defined in `app/models.py`:

- `Teacher`, `Student`, and `Class` store people and class assignments.
- `Report` stores subject marks, calculated percentage, and result status.
- `Academics` stores class-level enrollment, financial, pass, and distinction totals by year.
- `Attendance` stores daily student attendance.
- `Ticket` stores student support requests and their status.
- `SystemLog` stores administrative activity.
