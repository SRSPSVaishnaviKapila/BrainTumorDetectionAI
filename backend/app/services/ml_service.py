import hashlib
from pathlib import Path
from typing import Dict

import numpy as np
from PIL import Image

from app.config import (
    MODEL_PATH,
    CLASS_NAMES,
    LOW_CONFIDENCE_THRESHOLD,
    MODEL_VERSION,
    MODEL_ACCURACY,
    HEATMAP_DIR,
)


class MLService:
    def __init__(self):
        self.model = None
        self.mock_mode = True
        self.load_error = None
        self.image_size = (224, 224)

        self.load_model()

    def load_model(self) -> None:
        if not Path(MODEL_PATH).exists():
            self.load_error = f"Model file not found at {MODEL_PATH}"

            print(
                f"[MLService] WARNING: {self.load_error}. "
                "Running in DEMO MODE."
            )
            return

        try:
            from tensorflow.keras.models import load_model

            self.model = load_model(MODEL_PATH)

            # Read the input size directly from the model.
            input_shape = self.model.input_shape

            if isinstance(input_shape, tuple) and len(input_shape) == 4:
                height = input_shape[1] or 224
                width = input_shape[2] or 224
                self.image_size = (width, height)

            # Warm up the model once.
            dummy_input = np.zeros(
                (
                    1,
                    self.image_size[1],
                    self.image_size[0],
                    3,
                ),
                dtype=np.float32,
            )

            self.model.predict(dummy_input, verbose=0)

            self.mock_mode = False
            self.load_error = None

            print(
                f"[MLService] Model loaded successfully from "
                f"'{MODEL_PATH}'."
            )
            print(
                f"[MLService] Model input size: "
                f"{self.image_size[0]} x {self.image_size[1]}"
            )
            print(f"[MLService] Class names: {CLASS_NAMES}")

        except Exception as exc:
            self.load_error = str(exc)
            self.model = None
            self.mock_mode = True

            print(
                "[MLService] WARNING: Could not load model. "
                f"Running in DEMO MODE. Error: {exc}"
            )

    def preprocess_image(self, image_path: str) -> np.ndarray:
        image = Image.open(image_path).convert("RGB")

        image = image.resize(
            self.image_size,
            Image.Resampling.LANCZOS,
        )

        image_array = np.asarray(
            image,
            dtype=np.float32,
        )

        # Do not divide by 255 here.
        # The uploaded model already contains a Rescaling layer.
        image_array = np.expand_dims(
            image_array,
            axis=0,
        )

        return image_array

    def _convert_to_probabilities(
        self,
        prediction: np.ndarray,
    ) -> np.ndarray:
        values = np.asarray(
            prediction,
            dtype=np.float32,
        ).reshape(-1)

        if len(values) != len(CLASS_NAMES):
            raise ValueError(
                "The model produced "
                f"{len(values)} outputs, but CLASS_NAMES contains "
                f"{len(CLASS_NAMES)} classes."
            )

        values_are_probabilities = (
            np.all(values >= 0)
            and np.all(values <= 1)
            and np.isclose(
                np.sum(values),
                1.0,
                atol=0.01,
            )
        )

        if values_are_probabilities:
            return values

        # Convert model logits into probabilities.
        shifted_values = values - np.max(values)
        exponential_values = np.exp(shifted_values)

        return exponential_values / np.sum(exponential_values)

    def predict(self, image_path: str) -> Dict:
        if self.mock_mode or self.model is None:
            digest = hashlib.sha256(
                Path(image_path).read_bytes()
            ).digest()

            class_index = digest[0] % len(CLASS_NAMES)
            predicted_class = CLASS_NAMES[class_index]

            confidence = round(
                55 + (digest[1] / 255) * 40,
                2,
            )

        else:
            image_array = self.preprocess_image(image_path)

            raw_prediction = self.model.predict(
                image_array,
                verbose=0,
            )

            probabilities = self._convert_to_probabilities(
                raw_prediction
            )

            class_index = int(
                np.argmax(probabilities)
            )

            predicted_class = CLASS_NAMES[class_index]

            confidence = round(
                float(probabilities[class_index]) * 100,
                2,
            )

            print("\n========== MODEL DEBUG ==========")
            print("Image:", image_path)
            print(
                "Input shape:",
                image_array.shape,
            )
            print(
                "Input minimum:",
                float(image_array.min()),
            )
            print(
                "Input maximum:",
                float(image_array.max()),
            )
            print(
                "Input mean:",
                float(image_array.mean()),
            )
            print(
                "Raw model output:",
                np.asarray(raw_prediction).reshape(-1).tolist(),
            )
            print(
                "Probabilities:",
                probabilities.tolist(),
            )
            print(
                "Probability sum:",
                float(np.sum(probabilities)),
            )
            print(
                "Class names:",
                CLASS_NAMES,
            )
            print(
                "Predicted index:",
                class_index,
            )
            print(
                "Predicted class:",
                predicted_class,
            )
            print(
                "Confidence:",
                confidence,
            )
            print("=================================\n")

        ai_status = (
            "No Tumor Detected"
            if predicted_class == "notumor"
            else "Tumor Detected"
        )

        risk_level = self._risk_level(
            predicted_class,
            confidence,
        )

        review_status = (
            "needs_attention"
            if confidence < LOW_CONFIDENCE_THRESHOLD
            else "pending_review"
        )

        explanation = self._explanation(
            predicted_class,
            confidence,
        )

        heatmap_path = None

        if not self.mock_mode:
            heatmap_path = self.generate_gradcam(
                image_path,
                class_index,
            )

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

    def _risk_level(
        self,
        predicted_class: str,
        confidence: float,
    ) -> str:
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            return "review_required"

        if predicted_class == "notumor":
            return "low"

        if confidence >= 90:
            return "high"

        return "moderate"

    def _explanation(
        self,
        predicted_class: str,
        confidence: float,
    ) -> str:
        if predicted_class == "notumor":
            label = "no-tumour pattern"
        else:
            label = f"{predicted_class} pattern"

        return (
            f"The model's strongest output was the {label} "
            f"with {confidence:.2f}% confidence. "
            "This AI result is a decision-support output and "
            "must be reviewed with the original scan by a "
            "qualified clinician."
        )

    def generate_gradcam(
        self,
        image_path: str,
        class_index: int,
    ) -> str | None:
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Model

            last_conv_layer = None

            for layer in reversed(self.model.layers):
                try:
                    output_shape = layer.output.shape

                    if len(output_shape) == 4:
                        last_conv_layer = layer
                        break
                except Exception:
                    continue

            if last_conv_layer is None:
                print(
                    "[MLService] Grad-CAM unavailable: "
                    "No convolutional layer was found."
                )
                return None

            grad_model = Model(
                inputs=self.model.inputs,
                outputs=[
                    last_conv_layer.output,
                    self.model.output,
                ],
            )

            image_array = self.preprocess_image(
                image_path
            )

            with tf.GradientTape() as tape:
                conv_outputs, predictions = grad_model(
                    image_array
                )

                class_channel = predictions[
                    :,
                    class_index,
                ]

            gradients = tape.gradient(
                class_channel,
                conv_outputs,
            )

            if gradients is None:
                return None

            pooled_gradients = tf.reduce_mean(
                gradients,
                axis=(0, 1, 2),
            )

            conv_outputs = conv_outputs[0]

            heatmap = tf.reduce_sum(
                conv_outputs * pooled_gradients,
                axis=-1,
            )

            heatmap = tf.maximum(
                heatmap,
                0,
            )

            maximum_value = tf.reduce_max(
                heatmap
            )

            if float(maximum_value) == 0:
                return None

            heatmap = (
                heatmap / maximum_value
            ).numpy()

            base_image = Image.open(
                image_path
            ).convert("RGB")

            resized_heatmap = Image.fromarray(
                np.uint8(255 * heatmap)
            ).resize(base_image.size)

            heat = (
                np.asarray(resized_heatmap)
                .astype("float32")
                / 255.0
            )

            original = np.asarray(
                base_image
            ).astype("float32")

            red_layer = np.zeros_like(
                original
            )

            red_layer[..., 0] = heat * 255

            output = np.clip(
                (0.65 * original)
                + (0.35 * red_layer),
                0,
                255,
            ).astype("uint8")

            HEATMAP_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )

            output_path = (
                HEATMAP_DIR
                / f"gradcam_{Path(image_path).stem}.png"
            )

            Image.fromarray(output).save(
                output_path
            )

            return str(output_path)

        except Exception as exc:
            print(
                "[MLService] Grad-CAM unavailable "
                f"for this model: {exc}"
            )
            return None

    def info(self) -> dict:
        return {
            "model_loaded": not self.mock_mode,
            "mock_mode": self.mock_mode,
            "model_path": str(MODEL_PATH),
            "model_version": MODEL_VERSION,
            "configured_accuracy": (
                float(MODEL_ACCURACY)
                if MODEL_ACCURACY
                else None
            ),
            "low_confidence_threshold":
                LOW_CONFIDENCE_THRESHOLD,
            "load_error": self.load_error,
        }


ml_service = MLService()
