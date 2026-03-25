import os
import tempfile
import logging
from libs.logging import configure_logging


def test_configure_logging():
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = configure_logging(temp_dir)
        assert isinstance(logger, logging.Logger)
        assert logger.name == "buildanddeploy"
        assert logger.level == logging.DEBUG

        # Check files
        log_file = os.path.join(temp_dir, "build.log")
        assert os.path.exists(log_file)

        # Test writing
        logger.info("Test message")
        with open(log_file, "r") as f:
            content = f.read()
            assert "Test message" in content
