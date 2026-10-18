import getpass
import os
from client_logger import log_client_event
import pprint
from api_client import ApiClient

BASE_URL = "http://127.0.0.1:8000"

class UserToolsManager:
    def __init__(self, username, client: ApiClient):
        self.username = username
        self.client = client

    def upload_pdfs(self):
        filepaths = input("Enter PDF file paths (comma separated): ").split(",")
        files = [("files", (fp.strip(), open(fp.strip(), "rb"), "application/pdf")) for fp in filepaths if fp.strip()]
        is_public = input("Is public? (1 for yes, 0 for no): ").strip()
        res = self.client.post("/pdf/upload", files=files, data={"is_public": is_public})
        log_client_event(self.username, "user_upload_pdfs", "success" if res.status_code == 200 else "fail", f"files={filepaths}, is_public={is_public}, response={res.text}", is_admin=False)
        pprint.pprint(res.json())

    def upload_all_pdfs_from_folder(self):
        folder = input("Enter folder path: ").strip()
        files = []
        for fname in os.listdir(folder):
            if fname.lower().endswith(".pdf"):
                files.append(("files", (fname, open(os.path.join(folder, fname), "rb"), "application/pdf")))
        is_public = input("Is public? (1 for yes, 0 for no): ").strip()
        res = self.client.post("/pdf/upload", files=files, data={"is_public": is_public})
        log_client_event(self.username, "user_upload_folder", "success" if res.status_code == 200 else "fail", f"folder={folder}, is_public={is_public}, response={res.text}", is_admin=False)
        pprint.pprint(res.json())

    def list_my_pdfs(self):
        res = self.client.get("/pdf")
        log_client_event(self.username, "user_list_pdfs", "success" if res.status_code == 200 else "fail", f"response={res.text}", is_admin=False)
        pprint.pprint(res.json())

    def ingest_my_pdf(self):
        listing = self.client.get("/pdf").json().get("pdfs", [])
        pprint.pprint(listing)
        pdf_id = int(input("PDF ID to ingest: ").strip())
        res = self.client.post(f"/vectordb/ingest/pdf/{pdf_id}")
        log_client_event(self.username, "user_ingest_pdf", "success" if res.status_code == 200 else "fail", f"pdf_id={pdf_id}, response={res.text}", is_admin=False)
        pprint.pprint(res.json())

    def ingest_all_my_pdfs(self):
        res = self.client.post("/vectordb/ingest/all")
        log_client_event(self.username, "user_ingest_all_pdfs", "success" if res.status_code == 200 else "fail", f"response={res.text}", is_admin=False)
        pprint.pprint(res.json())

    def change_password(self):
        print("Not implemented. Please contact admin.")

    def delete_all_my_pdfs_from_vector_store(self):
        res = self.client.delete("/vectordb/pdf")
        log_client_event(self.username, "user_remove_all_pdfs_vectordb", "success" if res.status_code == 200 else "fail", f"response={res.text}", is_admin=False)
        pprint.pprint(res.json())

    def delete_my_pdf_from_data_by_id(self):
        listing = self.client.get("/pdf").json().get("pdfs", [])
        pprint.pprint(listing)
        pdf_id = int(input("PDF ID to delete: ").strip())
        res = self.client.delete(f"/pdf/{pdf_id}")
        log_client_event(self.username, "user_delete_pdf_data", "success" if res.status_code == 200 else "fail", f"pdf_id={pdf_id}, response={res.text}", is_admin=False)
        pprint.pprint(res.json())

    def delete_all_my_pdfs_from_data(self):
        res = self.client.get("/pdf")
        pdfs = res.json().get("pdfs", [])
        pdf_ids = [pdf["id"] for pdf in pdfs]
        if not pdf_ids:
            print("No PDFs to delete.")
            return
        results = [
            self.client.delete(f"/pdf/{pdf_id}")
            for pdf_id in pdf_ids
        ]
        success = all(response.status_code == 200 for response in results)
        log_client_event(self.username, "user_delete_all_pdfs_data", "success" if success else "fail", f"pdf_ids={pdf_ids}", is_admin=False)
        pprint.pprint([response.json() for response in results])

    def list_ingested_pdfs(self):
        res = self.client.get("/vectordb/pdf")
        log_client_event(self.username, "user_list_ingested_pdfs", "success" if res.status_code == 200 else "fail", f"response={res.text}", is_admin=False)
        pprint.pprint(res.json())

    def main_menu(self):
        while True:
            print("\n=== User Main Menu ===")
            print("1. Upload PDFs")
            print("2. Upload all PDFs from folder")
            print("3. List my PDFs")
            print("4. Ingest a PDF")
            print("5. Ingest all my PDFs")
            print("6. List my ingested PDFs")
            print("7. Delete a PDF from storage")
            print("8. Delete all my PDFs from storage")
            print("9. Remove all my PDFs from vectordb")
            print("0. Exit")
            choice = input("Select option: ").strip()
            if choice == "1":
                self.upload_pdfs()
            elif choice == "2":
                self.upload_all_pdfs_from_folder()
            elif choice == "3":
                self.list_my_pdfs()
            elif choice == "4":
                self.ingest_my_pdf()
            elif choice == "5":
                self.ingest_all_my_pdfs()
            elif choice == "6":
                self.list_ingested_pdfs()
            elif choice == "7":
                self.delete_my_pdf_from_data_by_id()
            elif choice == "8":
                self.delete_all_my_pdfs_from_data()
            elif choice == "9":
                self.delete_all_my_pdfs_from_vector_store()
            elif choice == "0":
                log_client_event(self.username, "user_exit", "success", "user exited", is_admin=False)
                print("Goodbye!")
                break
            else:
                print("Invalid option.")

def authenticate():
    print("=== User Login ===")
    while True:
        username = input("User ID: ").strip()
        password = getpass.getpass("Password: ")
        try:
            client = ApiClient(BASE_URL)
            res = client.login(username, password)
            if res.status_code == 200 and res.json().get("role") == "user":
                print("✅ Authentication successful!\n")
                log_client_event(username, "user_login", "success", "login succeeded", is_admin=False)
                return username, client
            else:
                print("❌ Incorrect username or password. Please try again.\n")
                log_client_event(username, "user_login", "fail", f"login failed: {res.text}", is_admin=False)
        except Exception as e:
            print(f"❌ Error connecting to server: {e}\n")
            log_client_event(username, "user_login", "fail", f"connection error: {e}", is_admin=False)

if __name__ == "__main__":
    username, client = authenticate()
    manager = UserToolsManager(username, client)
    manager.main_menu()
