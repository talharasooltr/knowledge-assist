from typing import Optional

from sqlalchemy import delete, exists, select, update
from sqlalchemy.exc import IntegrityError

from app.core.passwords import burn_password_check, hash_password, verify_password
from app.infrastructure.db.session import get_session
from app.infrastructure.db.models import IngestState, Pdf, User


def _as_flag(value: bool | int) -> int:
    return int(bool(value))


def add_user(userid: str, password: str, is_admin: int = 0) -> bool:
    try:
        with get_session() as session:
            session.add(
                User(
                    userid=userid,
                    password=hash_password(password),
                    is_admin=bool(is_admin),
                )
            )
        return True
    except IntegrityError:
        return False


def delete_user(userid: str) -> bool:
    with get_session() as session:
        result = session.execute(delete(User).where(User.userid == userid))
        return result.rowcount > 0


def authenticate_user(userid: str, password: str) -> bool:
    with get_session() as session:
        user = session.scalar(select(User).where(User.userid == userid))
        if user is None:
            burn_password_check(password)
            return False
        valid, replacement_hash = verify_password(password, user.password)
        if valid and replacement_hash is not None:
            user.password = replacement_hash
        return valid


def update_user_password(userid: str, new_password: str) -> bool:
    with get_session() as session:
        user = session.scalar(select(User).where(User.userid == userid))
        if user is None:
            return False
        user.password = hash_password(new_password)
        return True


def get_all_users() -> list[dict]:
    with get_session() as session:
        users = session.scalars(select(User).order_by(User.id)).all()
        return [
            {"id": user.id, "userid": user.userid}
            for user in users
        ]


def add_pdf(
    filename: str,
    uploaded_by: str,
    is_global: int = 0,
    filepath: Optional[str] = None,
) -> int:
    with get_session() as session:
        pdf = Pdf(
            filename=filename,
            filepath=filepath or filename,
            uploaded_by=uploaded_by,
            is_public=bool(is_global),
        )
        session.add(pdf)
        session.flush()
        return pdf.id


def _pdf_dict(pdf: Pdf, is_indexed: bool = False) -> dict:
    return {
        "id": pdf.id,
        "filename": pdf.filename,
        "filepath": pdf.filepath,
        "uploaded_by": pdf.uploaded_by,
        "is_public": _as_flag(pdf.is_public),
        "is_indexed": is_indexed,
        "is_deleting": pdf.deletion_requested,
        "created_at": pdf.created_at.isoformat() if pdf.created_at else None,
    }


def _pdf_indexed_expression():
    return exists(
        select(IngestState.id).where(IngestState.pdf_id == Pdf.id)
    )


def get_pdfs_by_user(uploaded_by: str) -> list[dict]:
    with get_session() as session:
        rows = session.execute(
            select(Pdf, _pdf_indexed_expression()).where(
                Pdf.uploaded_by == uploaded_by
            ).order_by(Pdf.id)
        ).all()
        return [_pdf_dict(pdf, is_indexed) for pdf, is_indexed in rows]


def get_all_pdfs() -> list[dict]:
    with get_session() as session:
        rows = session.execute(
            select(Pdf, _pdf_indexed_expression()).order_by(Pdf.id)
        ).all()
        return [_pdf_dict(pdf, is_indexed) for pdf, is_indexed in rows]


def get_pdf_by_id(pdf_id: int) -> dict | None:
    with get_session() as session:
        pdf = session.get(Pdf, pdf_id)
        return _pdf_dict(pdf) if pdf is not None else None


def request_pdf_deletion(pdf_id: int, uploaded_by: str | None = None) -> bool:
    with get_session() as session:
        query = update(Pdf).where(Pdf.id == pdf_id)
        if uploaded_by is not None:
            query = query.where(Pdf.uploaded_by == uploaded_by)
        result = session.execute(query.values(deletion_requested=True))
        return result.rowcount > 0


def delete_pdf_by_id(pdf_id: int, uploaded_by: str | None = None) -> bool:
    with get_session() as session:
        query = delete(Pdf).where(
            Pdf.id == pdf_id,
            Pdf.deletion_requested.is_(True),
        )
        if uploaded_by is not None:
            query = query.where(Pdf.uploaded_by == uploaded_by)
        result = session.execute(query)
        return result.rowcount > 0


def ingest(pdf_filename: str, ingested_by: str, is_public: int, pdf_id: int) -> int:
    with get_session() as session:
        state = IngestState(
            pdf_id=pdf_id,
            filename=pdf_filename,
            ingested_by=ingested_by,
            is_public=bool(is_public),
        )
        session.add(state)
        session.flush()
        return state.id


def _ingest_dict(state: IngestState) -> dict:
    return {
        "id": state.id,
        "filename": state.filename,
        "ingested_by": state.ingested_by,
        "is_public": _as_flag(state.is_public),
        "created_at": state.created_at.isoformat() if state.created_at else None,
    }


def get_all_ingested_pdfs() -> list[dict]:
    with get_session() as session:
        states = session.scalars(select(IngestState).order_by(IngestState.id)).all()
        return [_ingest_dict(state) for state in states]
