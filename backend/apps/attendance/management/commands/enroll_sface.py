from django.core.management.base import BaseCommand
from django.conf import settings
from apps.attendance.db import get_db, get_fs
from apps.attendance.ocv_recognition import extract_feature_from_bgr, refresh_known
import cv2, numpy as np, re, traceback

BASENAME = re.compile(r"^([^.\s]+)")  # E001.jpg -> E001 ; E001_1.jpg -> E001_1

class Command(BaseCommand):
    help = "Compute SFace embeddings from GridFS photos into employees.faceEmbedding (debug verbose)"

    def handle(self, *args, **kwargs):
        db = get_db(); fs = get_fs()
        files_col = f"{settings.MONGODB_GRIDFS_BUCKET}.files"
        self.stdout.write(f"DB: {db.name}")
        self.stdout.write(f"GridFS files collection: {files_col}")

        total_files = db[files_col].count_documents({})
        self.stdout.write(f"Found {total_files} image file(s) in GridFS")

        files = list(db[files_col].find({}, {"_id":1, "filename":1, "uploadDate":1}))
        files.sort(key=lambda d: (d.get("filename",""), d.get("uploadDate")))

        created = updated = noface = skipped = 0

        for f in files:
            try:
                fname = f.get("filename","")
                m = BASENAME.match(fname)
                if not m:
                    self.stdout.write(f"[skip name] {fname}")
                    skipped += 1
                    continue

                code = m.group(1)  # employee code derived from filename
                # ensure employee doc exists
                res = db["employees"].update_one(
                    {"employeeCode": code},
                    {"$setOnInsert": {"employeeCode": code}},
                    upsert=True
                )
                if res.upserted_id:
                    created += 1
                    self.stdout.write(f"[create] employee {code}")

                # read image bytes from GridFS (chunks auto-assembled)
                data = fs.get(f["_id"]).read()
                img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                if img is None:
                    self.stdout.write(f"[bad image] {fname}")
                    skipped += 1
                    continue

                feat = extract_feature_from_bgr(img)
                if feat is None:
                    self.stdout.write(f"[no face] {fname}")
                    noface += 1
                    continue

                db["employees"].update_one(
                    {"employeeCode": code},
                    {"$set": {"faceEmbedding": feat.tolist()}}
                )
                updated += 1
                self.stdout.write(f"[ok] {fname} -> {code}")
            except Exception as e:
                self.stdout.write(f"[error] {f.get('filename')}: {e}")
                self.stdout.write(traceback.format_exc())

        refresh_known()
        self.stdout.write(self.style.SUCCESS(
            f"Summary: created={created}, updated={updated}, noface={noface}, skipped={skipped}"
        ))
