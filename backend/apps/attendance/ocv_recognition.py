import os, base64, cv2, numpy as np
from apps.attendance.db import get_db

# ----- Model file locations (supports either app root or /models folder) -----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YUNET_CANDIDATES = [
    os.path.join(BASE_DIR, "face_detection_yunet_2023mar.onnx"),
    os.path.join(BASE_DIR, "models", "face_detection_yunet_2023mar.onnx"),
]
SFACE_CANDIDATES = [
    os.path.join(BASE_DIR, "face_recognition_sface_2021dec.onnx"),
    os.path.join(BASE_DIR, "models", "face_recognition_sface_2021dec.onnx"),
]
def _pick(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("Missing ONNX models. Put YuNet + SFace ONNX in "
                            "apps/attendance/ or apps/attendance/models/")

YUNET = _pick(YUNET_CANDIDATES)
SFACE = _pick(SFACE_CANDIDATES)

# ----- Singletons -----
_detector = None
_recognizer = None
_known_codes = None
_known_feats = None  # np.ndarray [N, D]

def _load_models():
    global _detector, _recognizer
    if _detector is None:
        # lower score threshold to be more tolerant
        _detector = cv2.FaceDetectorYN.create(YUNET, "", (320, 320), 0.6, 0.3, 5000)
    if _recognizer is None:
        _recognizer = cv2.FaceRecognizerSF.create(SFACE, "")

def _b64_to_bgr(s: str):
    if "," in s:
        s = s.split(",", 1)[1]
    data = base64.b64decode(s)
    arr = np.frombuffer(data, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)

def _detect_biggest_on(img_bgr):
    h, w = img_bgr.shape[:2]
    _detector.setInputSize((w, h))
    _, faces = _detector.detect(img_bgr)
    if faces is None or len(faces) == 0:
        return None
    areas = faces[:, 2] * faces[:, 3]
    return faces[int(np.argmax(areas))]

def _try_orientations_and_scales(img_bgr):
    """Try original, up/down-scale, and 90° rotations."""
    attempts = [("orig", img_bgr)]
    h, w = img_bgr.shape[:2]
    if min(h, w) < 480:
        sf = 640.0 / min(h, w)
        attempts.append(("up", cv2.resize(img_bgr, (int(w*sf), int(h*sf)), interpolation=cv2.INTER_CUBIC)))
    if max(h, w) > 1600:
        sf = 1200.0 / max(h, w)
        attempts.append(("down", cv2.resize(img_bgr, (int(w*sf), int(h*sf)), interpolation=cv2.INTER_AREA)))
    attempts.append(("rot90",  cv2.rotate(img_bgr, cv2.ROTATE_90_CLOCKWISE)))
    attempts.append(("rot270", cv2.rotate(img_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)))
    for tag, im in attempts:
        face = _detect_biggest_on(im)
        if face is not None:
            return tag, im, face
    return None, None, None

def _feat_from_bgr(img_bgr):
    tag, im, face = _try_orientations_and_scales(img_bgr)
    if face is None:
        return None
    aligned = _recognizer.alignCrop(im, face)
    feat = _recognizer.feature(aligned)            # may be (1,128) or (128,)
    feat = np.asarray(feat, dtype=np.float32).ravel()  # -> (128,)
    norm = np.linalg.norm(feat) + 1e-12
    feat = feat / norm
    return feat


# =====================  PUBLIC API  =====================

def extract_feature_from_bgr(img_bgr):
    """Return SFace feature (np.float32 vector) from a BGR image, or None."""
    _load_models()
    return _feat_from_bgr(img_bgr)

def recognize_image_base64(image_b64: str, sim_thresh: float):
    """Return {ok, employeeCode, confidence} or {ok: False, reason, confidence?}."""
    _load_models()
    global _known_codes, _known_feats
    if _known_codes is None:
        # load embeddings once from Mongo
        cur = get_db()["employees"].find({"faceEmbedding": {"$type": "array"}}, {"employeeCode":1, "faceEmbedding":1})
        codes, feats = [], []
        for d in cur:
            v = np.array(d["faceEmbedding"], dtype=np.float32).ravel()  # -> (128,)
            if v.size != 128:
                # skip malformed embeddings (e.g., empty or wrong length)
                continue
            v /= (np.linalg.norm(v) + 1e-12)
            codes.append(d["employeeCode"])
            feats.append(v)

        _known_codes = codes
        _known_feats = np.vstack(feats) if feats else np.zeros((0, 128), np.float32)


    img = _b64_to_bgr(image_b64)
    if img is None:
        return {"ok": False, "reason": "bad_image"}

    q = _feat_from_bgr(img)
    if q is None:
        return {"ok": False, "reason": "no_face"}

    if _known_feats.shape[0] == 0:
        return {"ok": False, "reason": "no_enrolled_faces"}

    sims = (_known_feats @ q)  # cosine sim on normalized vectors
    idx = int(np.argmax(sims))
    best_sim = float(sims[idx])
    best_code = _known_codes[idx]

    if best_sim >= sim_thresh:
        return {"ok": True, "employeeCode": best_code, "confidence": best_sim}
    
    else:
        return {"ok": False, "reason": "low_confidence", "confidence": best_sim}

def refresh_known():
    """Clear cached embeddings so next call reloads from DB."""
    global _known_codes, _known_feats
    _known_codes = None
    _known_feats = None
    
