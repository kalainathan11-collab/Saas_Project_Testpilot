"""Load test cases from a CSV into one user's project, through the app's own API.

Runs inside the backend container (see deploy/load-testcases.sh). Idempotent: rows whose title
already exists in the project are skipped, so it is safe to run twice.

Usage: python load_testcases.py <user-email> <project-name-or-key> <csv-path>
CSV columns: title,module,type,priority,status,preconditions,steps,expected_result
"""

import csv
import json
import os
import sys
import urllib.request

from sqlalchemy import func, or_, select

sys.path.insert(0, os.getcwd())  # make `app` importable when run as a script from /app

BASE = os.environ.get("LOAD_BASE_URL", "http://127.0.0.1:8000")


def main(email: str, project_ref: str, csv_path: str) -> int:
    from app.auth.jwt import create_access_token
    from app.database import SessionLocal
    from app.models import Project, User

    with SessionLocal() as db:
        user = db.scalar(select(User).where(func.lower(User.email) == email.lower()))
        if user is None:
            print(f"ERROR: no user with email {email}")
            return 1
        project = db.scalar(
            select(Project).where(
                Project.user_id == user.id,
                or_(
                    func.lower(Project.name) == project_ref.lower(),
                    Project.key == project_ref.upper(),
                ),
            )
        )
        if project is None:
            names = [p.name for p in db.scalars(select(Project).where(Project.user_id == user.id))]
            print(f"ERROR: project '{project_ref}' not found for {email}. Available: {names}")
            return 1
        user_id, project_id, project_name = user.id, project.id, project.name

    headers = {
        "Authorization": f"Bearer {create_access_token(user_id)}",
        "Content-Type": "application/json",
    }

    def call(method: str, path: str, body: dict[str, str | int] | None = None) -> object:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(BASE + path, method=method, headers=headers, data=data)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read() or "null")

    existing_raw = call("GET", f"/api/testcases?project_id={project_id}&limit=500")
    existing = {c["title"] for c in existing_raw}  # type: ignore[union-attr,index]
    created = skipped = 0
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["title"] in existing:
                skipped += 1
                continue
            call("POST", "/api/testcases", {"project_id": project_id, **row})
            created += 1
    print(
        f"Project '{project_name}' (id {project_id}): created {created}, skipped {skipped} existing"
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
