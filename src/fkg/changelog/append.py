"""Append-only changelog for tracking graph changes."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from fkg.models.event import Event


def append_event(
    session: Session,
    event_type: str,
    authority_id: str,
    payload: dict[str, Any],
) -> Event:
    """Append an event to the changelog.

    Args:
        session: Database session
        event_type: Type of event (e.g., 'create_entity', 'update_edge')
        authority_id: The authority making the change
        payload: Event payload with details

    Returns:
        The created event
    """
    event = Event(
        event_type=event_type,
        authority_id=authority_id,
        payload=payload,
    )
    session.add(event)
    session.flush()
    return event


def get_events(
    session: Session,
    since_seq: int | None = None,
    event_type: str | None = None,
    authority_id: str | None = None,
    limit: int = 1000,
) -> list[Event]:
    """Get events from the changelog.

    Args:
        session: Database session
        since_seq: Return events after this sequence number
        event_type: Filter by event type
        authority_id: Filter by authority
        limit: Maximum number of events to return

    Returns:
        List of events
    """
    stmt = select(Event)

    if since_seq is not None:
        stmt = stmt.where(Event.seq > since_seq)

    if event_type:
        stmt = stmt.where(Event.event_type == event_type)

    if authority_id:
        stmt = stmt.where(Event.authority_id == authority_id)

    stmt = stmt.order_by(Event.seq.asc()).limit(limit)

    return list(session.execute(stmt).scalars().all())


def get_latest_seq(session: Session) -> int | None:
    """Get the latest sequence number in the changelog.

    Args:
        session: Database session

    Returns:
        The latest sequence number, or None if no events exist
    """
    stmt = select(Event.seq).order_by(Event.seq.desc()).limit(1)
    result = session.execute(stmt).scalar()
    return result


def get_events_for_export(
    session: Session,
    authority_id: str | None = None,
) -> list[Event]:
    """Get all events for PKG export.

    Args:
        session: Database session
        authority_id: Optional authority filter

    Returns:
        List of events for export
    """
    stmt = select(Event).order_by(Event.seq.asc())

    if authority_id:
        stmt = stmt.where(Event.authority_id == authority_id)

    return list(session.execute(stmt).scalars().all())
