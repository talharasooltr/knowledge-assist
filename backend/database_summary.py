from utils import database_repository
from utils.vectordb import get_available_user_ids, get_pdf_sources


if __name__ == "__main__":
    users = database_repository.get_all_users()
    pdfs = database_repository.get_all_pdfs()
    ingested = database_repository.get_all_ingested_pdfs()

    print("=== PostgreSQL Knowledge Assistant Summary ===")
    print(f"Users: {[user['userid'] for user in users]}")
    print(f"PDF records: {len(pdfs)}")
    print(f"Ingestion records: {len(ingested)}")
    print(f"Vector sources: {get_pdf_sources()}")
    print(f"Users with chat memory: {get_available_user_ids()}")
