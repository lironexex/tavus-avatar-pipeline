# src/dropbox_utils.py
import os
import dropbox
from tqdm import tqdm

class ProgressFile:
    """A wrapper for a file object that updates a tqdm progress bar."""
    def __init__(self, file, pbar):
        self.file = file
        self.pbar = pbar

    def read(self, size=-1):
        chunk = self.file.read(size)
        if chunk:
            self.pbar.update(len(chunk))
        return chunk

    def __len__(self):
        return os.fstat(self.file.fileno()).st_size

def upload_and_get_link(file_path):
    """Uploads to Dropbox and returns a direct temporary download link."""
    access_token = os.getenv("DROPBOX_ACCESS_TOKEN")
    if not access_token:
        print("Error: DROPBOX_ACCESS_TOKEN not found in .env")
        return None

    dbx = dropbox.Dropbox(access_token)
    file_name = f"/{os.path.basename(file_path)}"
    file_size = os.path.getsize(file_path)

    try:
        print(f"Uploading {os.path.basename(file_path)} to Dropbox...")
        with tqdm(total=file_size, unit='B', unit_scale=True, desc="Dropbox Upload") as pbar:
            with open(file_path, "rb") as f:
                wrapped_file = ProgressFile(f, pbar)
                # Upload with overwrite mode for re-runs
                dbx.files_upload(wrapped_file.read(), file_name, mode=dropbox.files.WriteMode("overwrite"))

        print("\nGenerating direct link for Tavus...")
        # Temporary links are the most reliable for API training
        link_metadata = dbx.files_get_temporary_link(file_name)
        download_url = link_metadata.link
        print(f"✅ Download Link: {download_url}")
        return download_url

    except Exception as e:
        print(f"\nDropbox Error: {e}")
        return None