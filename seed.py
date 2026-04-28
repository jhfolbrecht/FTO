"""Bootstrap & sample-data seed script.

Usage:
  python seed.py                # full demo seed (admin + sample FTO/trainees/DORs)
  python seed.py --bootstrap    # idempotent: only create the default admin if none exists
"""
from __future__ import annotations

import os
import random
import sys
from datetime import date, timedelta

from app import create_app
from app.constants import (
    DOR_CATEGORY_CODES, PHASE_CODES, ROLE_ADMIN, ROLE_FTO, ROLE_TRAINEE,
)
from app.extensions import db
from app.models import DOR, DORRating, PhaseEvaluation, Trainee, User


def _admin_password() -> str:
    return os.environ.get("ADMIN_PASSWORD", "ChangeMe!2026")


def bootstrap_admin() -> User:
    admin = User.query.filter_by(role=ROLE_ADMIN).first()
    if admin:
        return admin
    admin = User(
        username="admin",
        full_name="Program Administrator",
        email=os.environ.get("ADMIN_EMAIL", "admin@example.com"),
        role=ROLE_ADMIN,
        active=True,
    )
    admin.set_password(_admin_password())
    db.session.add(admin)
    db.session.commit()
    print(f"  · created admin user: admin / {_admin_password()}")
    return admin


def full_seed() -> None:
    bootstrap_admin()

    # FTO
    fto = User.query.filter_by(username="jsmith").first()
    if not fto:
        fto = User(username="jsmith", full_name="J. Smith", role=ROLE_FTO,
                   email="jsmith@example.com", badge_number="FTO-101", active=True)
        fto.set_password("FtoPass!23")
        db.session.add(fto)
        db.session.flush()
        print(f"  · created FTO: jsmith / FtoPass!23")

    # Trainees
    trainees: list[Trainee] = []
    for i, (uname, name, badge) in enumerate([
        ("rdoe", "R. Doe", "T-201"),
        ("agarcia", "A. Garcia", "T-202"),
    ]):
        u = User.query.filter_by(username=uname).first()
        if not u:
            u = User(username=uname, full_name=name, role=ROLE_TRAINEE,
                     email=f"{uname}@example.com", badge_number=badge, active=True)
            u.set_password("TraineePass!23")
            db.session.add(u)
            db.session.flush()
            t = Trainee(
                user_id=u.id,
                academy_class="2026-A",
                hire_date=date.today() - timedelta(days=180),
                program_start_date=date.today() - timedelta(days=60 - i * 20),
                current_phase=PHASE_CODES[i],
                status="active",
                primary_fto_id=fto.id,
            )
            db.session.add(t)
            db.session.flush()
            trainees.append(t)
            print(f"  · created trainee: {uname} / TraineePass!23")
        else:
            trainees.append(u.trainee_profile)

    # Sample DORs (a handful per trainee over the past 3 weeks)
    for t in trainees:
        if t.dors:
            continue
        for delta in (1, 4, 8, 12, 17, 21):
            d = DOR(
                trainee_id=t.id,
                fto_id=fto.id,
                shift_date=date.today() - timedelta(days=delta),
                phase=t.current_phase,
                shift_label=random.choice(["Day", "Swing", "Grave"]),
                beat_assignment=f"Beat {random.randint(1, 9)}",
                most_acceptable="Demonstrated solid officer-safety habits during traffic stop.",
                least_acceptable="Slow to recognize need for backup on disturbance call.",
                additional_comments="Continue pairing on high-stress calls.",
            )
            db.session.add(d)
            db.session.flush()
            for code in DOR_CATEGORY_CODES:
                # Bias scores upward for trainees in later phases
                base = 3 + PHASE_CODES.index(t.current_phase)
                score = max(1, min(7, int(random.gauss(base + 0.5, 1.0))))
                # Occasional NRT
                not_observed = random.random() < 0.06
                db.session.add(DORRating(
                    dor_id=d.id, category_code=code,
                    score=None if not_observed else score,
                    not_observed=not_observed,
                    comment=("Needs improvement." if (not not_observed and score < 4) else None),
                ))

        # One sample phase evaluation
        ev = PhaseEvaluation(
            trainee_id=t.id,
            fto_id=fto.id,
            phase=t.current_phase,
            evaluation_date=date.today() - timedelta(days=2),
            decision="advance" if random.random() < 0.6 else "repeat",
            summary="Trainee shows steady progress and meets phase expectations overall.",
            strengths="Communications, report writing.",
            areas_for_improvement="Decision making under stress.",
            remediation_plan="Additional ride-alongs on high-volume shifts.",
        )
        db.session.add(ev)

    db.session.commit()
    print("  · sample data seeded")


def main() -> None:
    bootstrap_only = "--bootstrap" in sys.argv
    app = create_app()
    with app.app_context():
        db.create_all()
        if bootstrap_only:
            print("Seeding: bootstrap admin only")
            bootstrap_admin()
        else:
            print("Seeding: full demo data")
            full_seed()
        print("Done.")


if __name__ == "__main__":
    main()
