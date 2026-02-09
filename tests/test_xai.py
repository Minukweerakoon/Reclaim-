import os
import pytest
from PIL import Image

from src.cross_modal.clip_validator import CLIPValidator


@pytest.mark.integration
def test_clip_alignment_smoke(tmp_path):
    """
    Smoke test for CLIP alignment. Skips unless explicitly enabled.
    """
    if os.getenv("RUN_CLIP_INTEGRATION_TESTS") != "1":
        pytest.skip("Set RUN_CLIP_INTEGRATION_TESTS=1 to run CLIP integration tests.")

    try:
        validator = CLIPValidator(enable_logging=False)
    except Exception as exc:
        pytest.skip(f"CLIP not available: {exc}")

    image_path = tmp_path / "red.jpg"
    Image.new("RGB", (224, 224), color="red").save(image_path)

    result = validator.validate_image_text_alignment(str(image_path), "a red object")

    assert "similarity" in result
    assert 0.0 <= result["similarity"] <= 1.0
