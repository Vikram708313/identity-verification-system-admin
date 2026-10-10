
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


def get_face_embedding(image_bytes: bytes) -> np.ndarray:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Invalid image")

    faces = get_face_app().get(image)

    if len(faces) == 0:
        raise ValueError("No face detected")

    if len(faces) > 1:
        raise ValueError("Multiple faces detected")

    return faces[0].embedding


def compare_faces(
    reference_image: bytes,
    verification_image: bytes,
) -> dict:
    reference_embedding = get_face_embedding(reference_image)
    verification_embedding = get_face_embedding(verification_image)

    reference_embedding = reference_embedding / np.linalg.norm(
        reference_embedding
    )

    verification_embedding = verification_embedding / np.linalg.norm(
        verification_embedding
    )

    similarity = float(
        np.dot(reference_embedding, verification_embedding)
    )

    similarity = max(0.0, min(1.0, similarity))

    match_score = round(similarity * 100, 2)

    if similarity >= 0.50:
        status = "PASS"
    elif similarity >= 0.35:
        status = "REVIEW"
    else:
        status = "FAIL"

    return {
        "match_score": match_score,
        "similarity": round(similarity, 4),
        "status": status,
    }


def detect_blink(image_bytes: bytes) -> bool:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        return False

    faces = get_face_app().get(image)

    if len(faces) != 1:
        return False

    face = faces[0]

    if not hasattr(face, "landmark_2d_106"):
        return False

    landmarks = face.landmark_2d_106

    left_eye = landmarks[[35, 36, 37, 38, 39, 40]]
    right_eye = landmarks[[89, 90, 91, 92, 93, 94]]

    def eye_aspect_ratio(eye):
        vertical_1 = np.linalg.norm(eye[1] - eye[5])
        vertical_2 = np.linalg.norm(eye[2] - eye[4])
        horizontal = np.linalg.norm(eye[0] - eye[3])

        if horizontal == 0:
            return 1.0

        return (vertical_1 + vertical_2) / (2.0 * horizontal)

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
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            continue

        faces = get_face_app().get(image)

        if len(faces) != 1:
            continue

        face = faces[0]
        landmarks = getattr(face, "landmark_2d_106", None)

        if landmarks is None:
            continue

        nose = landmarks[46]
        nose_positions.append(float(nose[0]))

        bbox = face.bbox
        face_widths.append(float(bbox[2] - bbox[0]))

    if len(nose_positions) < 3 or not face_widths:
        return False

    movement = max(nose_positions) - min(nose_positions)
    average_face_width = sum(face_widths) / len(face_widths)

    if average_face_width <= 0:
        return False

    # Normalize movement to face size.
    relative_movement = movement / average_face_width

    return relative_movement > 0.04
