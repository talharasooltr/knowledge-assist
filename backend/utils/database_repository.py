from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from utils.database import get_session
from utils.models import IngestState, Pdf, User


def _as_flag(value: bool | int) -> int:
    return int(bool(value))


def add_user(userid: str, password: str, is_admin: int = 0) -> bool:
    try:
        with get_session() as session:
            session.add(User(userid=userid, password=password, is_admin=bool(is_admin)))
        return True
    except IntegrityError:
        return False


def delete_user(userid: str) -> bool:
    with get_session() as session:
        result = session.execute(delete(User).where(User.userid == userid))
        return result.rowcount > 0


def authenticate_user(userid: str, password: str) -> bool:
    with get_session() as session:
        return session.scalar(
            select(User.id).where(User.userid == userid, User.password == password)
        ) is not None


def update_user_password(userid: str, new_password: str) -> bool:
    with get_session() as session:
        user = session.scalar(select(User).where(User.userid == userid))
        if user is None:
            return False
        user.password = new_password
        return True


def get_all_users() -> list[dict]:
    with get_session() as session:
        users = session.scalars(select(User).order_by(User.id)).all()
        return [
            {"id": user.id, "userid": user.userid, "password": user.password}
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


def _pdf_dict(pdf: Pdf) -> dict:
    return {
        "id": pdf.id,
        "filename": pdf.filename,
        "filepath": pdf.filepath,
        "uploaded_by": pdf.uploaded_by,
        "is_public": _as_flag(pdf.is_public),
        "created_at": pdf.created_at.isoformat() if pdf.created_at else None,
    }


def get_pdfs_by_user(uploaded_by: str) -> list[dict]:
    with get_session() as session:
        pdfs = session.scalars(
            select(Pdf).where(Pdf.uploaded_by == uploaded_by).order_by(Pdf.id)
        ).all()
        return [_pdf_dict(pdf) for pdf in pdfs]


def get_all_pdfs() -> list[dict]:
    with get_session() as session:
        return [_pdf_dict(pdf) for pdf in session.scalars(select(Pdf).order_by(Pdf.id)).all()]


def delete_pdf_by_filename(filename: str, uploaded_by: str | None = None) -> bool:
    with get_session() as session:
        query = delete(Pdf).where(Pdf.filename == filename)
        if uploaded_by is not None:
            query = query.where(Pdf.uploaded_by == uploaded_by)
        result = session.execute(query)
        return result.rowcount > 0


def delete_pdf_by_id(pdf_id: int) -> bool:
    with get_session() as session:
        result = session.execute(delete(Pdf).where(Pdf.id == pdf_id))
        return result.rowcount > 0


def get_pdf_filepath_by_filename(filename: str) -> Optional[str]:
    with get_session() as session:
        return session.scalar(select(Pdf.filepath).where(Pdf.filename == filename))


def ingest(pdf_filename: str, ingested_by: str, is_public: int) -> int:
    with get_session() as session:
        state = IngestState(
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


def get_ingested_pdfs_by_user(ingested_by: str) -> list[dict]:
    with get_session() as session:
        states = session.scalars(
            select(IngestState)
            .where(IngestState.ingested_by == ingested_by)
            .order_by(IngestState.id)
        ).all()
        return [_ingest_dict(state) for state in states]


def get_all_ingested_pdfs() -> list[dict]:
    with get_session() as session:
        states = session.scalars(select(IngestState).order_by(IngestState.id)).all()
        return [_ingest_dict(state) for state in states]


def delete_ingested_pdf_by_filename(pdf_filename: str) -> bool:
    with get_session() as session:
        result = session.execute(delete(IngestState).where(IngestState.filename == pdf_filename))
        return result.rowcount > 0


def delete_ingested_pdf_by_id(state_id: int) -> bool:
    with get_session() as session:
        result = session.execute(delete(IngestState).where(IngestState.id == state_id))
        return result.rowcount > 0
