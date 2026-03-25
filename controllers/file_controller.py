import os
import shutil
from datetime import datetime

from database.db import get_session
from database.models import CustomerFile

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
PHOTOS_DIR = os.path.join(UPLOADS_DIR, "photos")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic", ".heif"}


def _customer_photos_dir(customer_id: int) -> str:
    path = os.path.join(PHOTOS_DIR, str(customer_id))
    os.makedirs(path, exist_ok=True)
    return path


class FileController:

    def get_photos(self, customer_id: int) -> list[CustomerFile]:
        session = get_session()
        try:
            photos = (
                session.query(CustomerFile)
                .filter(
                    CustomerFile.customer_id == customer_id,
                    CustomerFile.filetype.in_(["jpg", "jpeg", "png", "gif", "bmp", "webp", "heic", "heif"])
                )
                .order_by(CustomerFile.uploaded_at.desc())
                .all()
            )
            for p in photos:
                session.expunge(p)
            return photos
        finally:
            session.close()

    def add_photo(self, customer_id: int, source_path: str) -> CustomerFile:
        ext = os.path.splitext(source_path)[1].lower()
        if ext not in IMAGE_EXTENSIONS:
            raise ValueError("קובץ זה אינו תמונה נתמכת")

        dest_dir = _customer_photos_dir(customer_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp}{ext}"
        dest_path = os.path.join(dest_dir, filename)
        shutil.copy2(source_path, dest_path)

        session = get_session()
        try:
            record = CustomerFile(
                customer_id=customer_id,
                filename=os.path.basename(source_path),
                filepath=dest_path,
                filetype=ext.lstrip("."),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            session.expunge(record)
            return record
        finally:
            session.close()

    def delete_photo(self, photo_id: int):
        session = get_session()
        try:
            photo = session.query(CustomerFile).filter_by(id=photo_id).first()
            if not photo:
                return
            filepath = photo.filepath
            session.delete(photo)
            session.commit()
        finally:
            session.close()

        if filepath and os.path.isfile(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass


file_controller = FileController()
