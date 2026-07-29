import hashlib
from pathlib import Path
from typing import Dict

import numpy as np
from PIL import Image

from app.config import (
    MODEL_PATH, CLASS_NAMES, LOW_CONFIDENCE_THRESHOLD,
    MODEL_VERSION, MODEL_ACCURACY, HEATMAP_DIR
)


class MLService:
    def __init__(self):
        self.model = None
        self.mock_mode = True
        self.load_error = None
        self.load_model()

    def load_model(self) -> None:
        if not Path(MODEL_PATH).exists():
            self.load_error = f"Model file not found at {MODEL_PATH}"
            print(f"[MLService] WARNING: {self.load_error}. Running in DEMO MODE.")
            return
        try:
            from tensorflow.keras.models import load_model
            self.model = load_model(MODEL_PATH)
            self.mock_mode = False
            self.load_error = None
            print(f"[MLService] Model loaded successfully from '{MODEL_PATH}'.")
        except Exception as exc:
            self.load_error = str(exc)
            self.model = None
            self.mock_mode = True
            print(f"[MLService] WARNING: Could not load model. Running in DEMO MODE. Error: {exc}")

    def preprocess_image(self, image_path: str) -> np.ndarray:
        image = Image.open(image_path).convert("RGB").resize((224, 224))
        image_array = np.array(image).astype("float32") / 255.0
        return np.expand_dims(image_array, axis=0)

    def predict(self, image_path: str) -> Dict:
        if self.mock_mode or self.model is None:
            # Stable demo output for the same file; never presented as a clinical result.
            digest = hashlib.sha256(Path(image_path).read_bytes()).digest()
            class_index = digest[0] % len(CLASS_NAMES)
            predicted_class = CLASS_NAMES[class_index]
            confidence = round(55 + (digest[1] / 255) * 40, 2)
        else:
            image_array = self.preprocess_image(image_path)
            prediction = np.asarray(self.model.predict(image_array, verbose=0))
            class_index = int(np.argmax(prediction, axis=1)[0])
            confidence = round(float(np.max(prediction)) * 100, 2)
            predicted_class = CLASS_NAMES[class_index]

        ai_status = "No Tumor Detected" if predicted_class == "notumor" else "Tumor Detected"
        risk_level = self._risk_level(predicted_class, confidence)
        review_status = "needs_attention" if confidence < LOW_CONFIDENCE_THRESHOLD else "pending_review"
        explanation = self._explanation(predicted_class, confidence)
        heatmap_path = None if self.mock_mode else self.generate_gradcam(image_path, class_index)

        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "status": ai_status,
            "risk_level": risk_level,
            "review_status": review_status,
            "explanation": explanation,
            "heatmap_path": heatmap_path,
            "mock_mode": self.mock_mode,
            "model_version": MODEL_VERSION,
        }

    def _risk_level(self, predicted_class: str, confidence: float) -> str:
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            return "review_required"
        if predicted_class == "notumor":
            return "low"
        if confidence >= 90:
            return "high"
        return "moderate"

    def _explanation(self, predicted_class: str, confidence: float) -> str:
        label = "no-tumor pattern" if predicted_class == "notumor" else f"{predicted_class} pattern"
        return (
            f"The model's strongest output was the {label} with {confidence:.2f}% confidence. "
            "This AI result is a decision-support output and must be reviewed with the original scan by a qualified clinician."
        )

    def generate_gradcam(self, image_path: str, class_index: int) -> str | None:
        """Best-effort generic Grad-CAM. Returns None for unsupported architectures."""
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Model

            last_conv_layer = next(
                layer for layer in reversed(self.model.layers)
                if len(getattr(layer.output, "shape", [])) == 4
            )
            grad_model = Model(self.model.inputs, [last_conv_layer.output, self.model.output])
            image_array = self.preprocess_image(image_path)
            with tf.GradientTape() as tape:
                conv_outputs, predictions = grad_model(image_array)
                class_channel = predictions[:, class_index]
            gradients = tape.gradient(class_channel, conv_outputs)
            pooled_gradients = tf.reduce_mean(gradients, axis=(0, 1, 2))
            conv_outputs = conv_outputs[0]
            heatmap = tf.reduce_sum(conv_outputs * pooled_gradients, axis=-1)
            heatmap = tf.maximum(heatmap, 0)
            max_value = tf.reduce_max(heatmap)
            if float(max_value) == 0:
                return None
            heatmap = (heatmap / max_value).numpy()

            base = Image.open(image_path).convert("RGB")
            resized = Image.fromarray(np.uint8(255 * heatmap)).resize(base.size)
            heat = np.asarray(resized).astype("float32") / 255.0
            overlay = np.asarray(base).astype("float32")
            red_layer = np.zeros_like(overlay)
            red_layer[..., 0] = heat * 255
            output = np.clip(0.65 * overlay + 0.35 * red_layer, 0, 255).astype("uint8")
            output_path = HEATMAP_DIR / f"gradcam_{Path(image_path).stem}.png"
            Image.fromarray(output).save(output_path)
            return str(output_path)
        except Exception as exc:
            print(f"[MLService] Grad-CAM unavailable for this model: {exc}")
            return None

    def info(self) -> dict:
        return {
            "model_loaded": not self.mock_mode,
            "mock_mode": self.mock_mode,
            "model_path": str(MODEL_PATH),
            "model_version": MODEL_VERSION,
            "configured_accuracy": float(MODEL_ACCURACY) if MODEL_ACCURACY else None,
            "low_confidence_threshold": LOW_CONFIDENCE_THRESHOLD,
            "load_error": self.load_error,
        }


ml_service = MLService()
