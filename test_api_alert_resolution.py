import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from api import resolve_alert, resolve_all_alerts
from database import Base
from models import Alert


def test_resolve_alert_marks_unresolved_alert_as_resolved() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        alert = Alert(mac_address="aa:bb:cc:dd:ee:ff", alert_type="new_device", message="Dispozitiv nou")
        db.add(alert)
        db.commit()
        db.refresh(alert)

        result = resolve_alert(alert.id, db)

        assert result == {"id": alert.id, "resolved": True, "already_resolved": False}
        refreshed = db.scalar(select(Alert).where(Alert.id == alert.id))
        assert refreshed is not None
        assert refreshed.is_resolved is True


def test_resolve_alert_returns_already_resolved_payload() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        alert = Alert(
            mac_address="aa:bb:cc:dd:ee:11",
            alert_type="new_device",
            message="Dispozitiv rezolvat",
            is_resolved=True,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        result = resolve_alert(alert.id, db)

        assert result == {"id": alert.id, "resolved": False, "already_resolved": True}


def test_resolve_all_alerts_updates_only_unresolved_alerts() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        db.add_all(
            [
                Alert(mac_address="00:00:00:00:00:01", alert_type="new_device", message="A1", is_resolved=False),
                Alert(mac_address="00:00:00:00:00:02", alert_type="new_device", message="A2", is_resolved=False),
                Alert(mac_address="00:00:00:00:00:03", alert_type="new_device", message="A3", is_resolved=True),
            ]
        )
        db.commit()

        result = resolve_all_alerts(db)

        assert result == {"resolved": True, "updated_count": 2}
        alerts = db.scalars(select(Alert)).all()
        assert all(alert.is_resolved for alert in alerts)


def test_resolve_alert_returns_404_when_missing() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        with pytest.raises(HTTPException) as exc:
            resolve_alert(999, db)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Alert not found"
