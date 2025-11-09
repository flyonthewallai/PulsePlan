"""
Logging Utilities for Intent Classifier

Provides structured logging configuration for the ML training pipeline.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import yaml


def setup_logger(
    logger_name: str,
    log_file_path: Optional[Path] = None,
    log_level: str = "INFO",
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Set up structured logger with file and console handlers.

    Args:
        logger_name: Name for the logger instance
        log_file_path: Optional path to log file (creates parent dirs)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Optional custom format string

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Default format with timestamp and correlation info
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if path provided
    if log_file_path:
        log_file_path = Path(log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def load_config(config_path: Path) -> dict:
    """
    Load YAML configuration file with validation.

    Args:
        config_path: Path to YAML config file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config is invalid YAML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def validate_config(config: dict) -> None:
    """
    Validate configuration has required fields.

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If required fields are missing
    """
    required_sections = ["model", "training", "data", "paths", "labels"]

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: {section}")

    # Validate model config
    if "base_model_name" not in config["model"]:
        raise ValueError("Missing model.base_model_name in config")

    # Validate data paths
    required_data_keys = ["train_file", "dev_file", "test_file"]
    for key in required_data_keys:
        if key not in config["data"]:
            raise ValueError(f"Missing data.{key} in config")

    # Validate labels
    if not config["labels"] or not isinstance(config["labels"], list):
        raise ValueError("labels must be a non-empty list")

    # Validate num_labels matches labels list
    if config["model"]["num_labels"] != len(config["labels"]):
        raise ValueError(
            f"model.num_labels ({config['model']['num_labels']}) "
            f"doesn't match labels list length ({len(config['labels'])})"
        )


def get_device_info(logger: logging.Logger) -> str:
    """
    Get and log device information (CPU/GPU).

    Args:
        logger: Logger instance

    Returns:
        Device string ('cuda' or 'cpu')
    """
    try:
        import torch

        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            device_count = torch.cuda.device_count()
            memory_allocated = torch.cuda.memory_allocated(0) / 1e9
            memory_reserved = torch.cuda.memory_reserved(0) / 1e9

            logger.info(f"GPU detected: {device_name}")
            logger.info(f"GPU count: {device_count}")
            logger.info(f"CUDA version: {torch.version.cuda}")
            logger.info(f"GPU memory allocated: {memory_allocated:.2f} GB")
            logger.info(f"GPU memory reserved: {memory_reserved:.2f} GB")

            return "cuda"
        else:
            logger.warning("CUDA not available, using CPU")
            return "cpu"

    except ImportError:
        logger.warning("PyTorch not installed, cannot detect GPU")
        return "cpu"
