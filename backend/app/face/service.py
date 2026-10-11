from functools import lru_cache
import cv2
import numpy as np

# Lazy-load the model once per backend process.
face_app = None


def get_face_app():
    global face_app

    if face_app is None:
        from insightface.app import FaceAnalysis

        app = FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"],
        )
        app.prepare(ctx_id=0, det_size=(512, 512))
        face_app = app

    return face_app


def decode_image(image_bytes: bytes):
    if not image_bytes:
        return None
    return cv2.imdecode(
        np.frombuffer(image_bytes, dtype=np.uint8),
        cv2.IMREAD_COLOR,
    )


def _embedding_from_image(image):
    if image is None:
        raise ValueError("Invalid image")

    faces = get_face_app().get(image)
    if len(faces) == 0:
        raise ValueError("No face detected")
    if len(faces) > 1:
        raise ValueError("Multiple faces detected")

    embedding = np.asarray(faces[0].embedding, dtype=np.float32)
    norm = float(np.linalg.norm(embedding))

    if not np.isfinite(norm) or norm == 0:
        raise ValueError("Invalid face embedding")

    return embedding / norm


def get_face_embedding(image_bytes: bytes) -> np.ndarray:
    return _embedding_from_image(decode_image(image_bytes))


@lru_cache(maxsize=128)
def get_reference_embedding(file_path: str, mtime_ns: int, size: int):
    # Cache is invalidated automatically when the reference file changes.
    with open(file_path, "rb") as image_file:
        image_bytes = image_file.read()
    return get_face_embedding(image_bytes)


def compare_faces(reference_image: bytes, verification_image: bytes) -> dict:
    reference_embedding = get_face_embedding(reference_image)
    verification_embedding = get_face_embedding(verification_image)

    similarity = float(np.dot(reference_embedding, verification_embedding))
    similarity = max(-1.0, min(1.0, similarity))
    score_similarity = max(0.0, similarity)

    if score_similarity >= 0.50:
        status = "PASS"
    elif score_similarity >= 0.35:
        status = "REVIEW"
    else:
        status = "FAIL"

    return {
        "match_score": round(score_similarity * 100, 2),
        "similarity": round(similarity, 4),
        "status": status,
    }


def detect_blink(image_bytes: bytes) -> bool:
    image = decode_image(image_bytes)
    if image is None:
        return False

    faces = get_face_app().get(image)
    if len(faces) != 1:
        return False

    landmarks = getattr(faces[0], "landmark_2d_106", None)
    if landmarks is None or len(landmarks) <= 94:
        return False

    left_eye = landmarks[[35, 36, 37, 38, 39, 40]]
    right_eye = landmarks[[89, 90, 91, 92, 93, 94]]

    def eye_aspect_ratio(eye):
        vertical_1 = np.linalg.norm(eye[1] - eye[5])
        vertical_2 = np.linalg.norm(eye[2] - eye[4])
        horizontal = np.linalg.norm(eye[0] - eye[3])
        if horizontal <= 0:
            return 1.0
        return float((vertical_1 + vertical_2) / (2.0 * horizontal))

    return (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0 < 0.20


def detect_liveness_sequence(frames: list[bytes]) -> bool:
    if len(frames) < 3:
        return False

    nose_positions = []
    face_widths = []

    for image_bytes in frames:
        image = decode_image(image_bytes)
        if image is None:
            continue

        # Downscale large webcam frames to reduce CPU inference time.
        height, width = image.shape[:2]
        longest_side = max(height, width)
        if longest_side > 640:
            scale = 640.0 / longest_side
            image = cv2.resize(
                image,
                (int(width * scale), int(height * scale)),
                interpolation=cv2.INTER_AREA,
            )

        faces = get_face_app().get(image)
        if len(faces) != 1:
            continue

        face = faces[0]
        landmarks = getattr(face, "landmark_2d_106", None)
        if landmarks is None or len(landmarks) <= 46:
            continue

        bbox = face.bbox
        face_width = float(bbox[2] - bbox[0])
        if not np.isfinite(face_width) or face_width <= 0:
            continue

        normalized_nose_x = (
            float(landmarks[46][0]) - float(bbox[0])
        ) / face_width

        nose_positions.append(normalized_nose_x)
        face_widths.append(face_width)

    if len(nose_positions) < 3:
        return False

    movement = max(nose_positions) - min(nose_positions)
    average_face_width = sum(face_widths) / len(face_widths)

    if average_face_width <= 0:
        return False

    width_change = (
        max(face_widths) - min(face_widths)
    ) / average_face_width

    # Prototype movement heuristic, not production-grade anti-spoofing.
    return movement >= 0.025 or width_change >= 0.04