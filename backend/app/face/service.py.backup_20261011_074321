
import cv2
import numpy as np

# Load InsightFace only when face verification is requested.
# This allows other API routes to start without importing ONNX.
face_app = None


def get_face_app():
    global face_app

    if face_app is None:
        from insightface.app import FaceAnalysis

        app = FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"],
        )

        app.prepare(
            ctx_id=0,
            det_size=(640, 640),
        )

        face_app = app

    return face_app


def decode_image(image_bytes: bytes):
    """Decode image bytes into an OpenCV image."""
    if not image_bytes:
        return None

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    return cv2.imdecode(image_array, cv2.IMREAD_COLOR)


def get_face_embedding(image_bytes: bytes) -> np.ndarray:
    image = decode_image(image_bytes)

    if image is None:
        raise ValueError("Invalid image")

    faces = get_face_app().get(image)

    if len(faces) == 0:
        raise ValueError("No face detected")

    if len(faces) > 1:
        raise ValueError("Multiple faces detected")

    embedding = np.asarray(faces[0].embedding, dtype=np.float32)
    norm = np.linalg.norm(embedding)

    if not np.isfinite(norm) or norm == 0:
        raise ValueError("Invalid face embedding")

    return embedding


def compare_faces(
    reference_image: bytes,
    verification_image: bytes,
) -> dict:
    reference_embedding = get_face_embedding(reference_image)
    verification_embedding = get_face_embedding(verification_image)

    reference_norm = np.linalg.norm(reference_embedding)
    verification_norm = np.linalg.norm(verification_embedding)

    if reference_norm == 0 or verification_norm == 0:
        raise ValueError("Cannot compare invalid face embeddings")

    reference_embedding = reference_embedding / reference_norm
    verification_embedding = verification_embedding / verification_norm

    similarity = float(
        np.dot(reference_embedding, verification_embedding)
    )

    similarity = max(-1.0, min(1.0, similarity))

    # Convert cosine similarity to a percentage score.
    # Retains the original scoring convention.
    score_similarity = max(0.0, similarity)
    match_score = round(score_similarity * 100, 2)

    if score_similarity >= 0.50:
        status = "PASS"
    elif score_similarity >= 0.35:
        status = "REVIEW"
    else:
        status = "FAIL"

    return {
        "match_score": match_score,
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

    face = faces[0]
    landmarks = getattr(face, "landmark_2d_106", None)

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

        return float(
            (vertical_1 + vertical_2) / (2.0 * horizontal)
        )

    left_ear = eye_aspect_ratio(left_eye)
    right_ear = eye_aspect_ratio(right_eye)

    ear = (left_ear + right_ear) / 2.0

    return ear < 0.20


def detect_liveness_sequence(frames: list[bytes]) -> bool:
    if len(frames) < 3:
        return False

    nose_positions = []
    face_widths = []

    for image_bytes in frames:
        image = decode_image(image_bytes)

        if image is None:
            continue

        faces = get_face_app().get(image)

        if len(faces) != 1:
            continue

        face = faces[0]
        landmarks = getattr(face, "landmark_2d_106", None)

        if landmarks is None or len(landmarks) <= 46:
            continue

        nose = landmarks[46]
        bbox = face.bbox

        face_width = float(bbox[2] - bbox[0])

        if not np.isfinite(face_width) or face_width <= 0:
            continue

        # Normalize nose position relative to the face bounding box.
        normalized_nose_x = (
            float(nose[0]) - float(bbox[0])
        ) / face_width

        nose_positions.append(normalized_nose_x)
        face_widths.append(face_width)

    if len(nose_positions) < 3:
        return False

    movement = max(nose_positions) - min(nose_positions)
    average_face_width = sum(face_widths) / len(face_widths)

    if average_face_width <= 0:
        return False

    # Normalize movement by average face width.
    relative_movement = movement / average_face_width

    return relative_movement > 0.04
