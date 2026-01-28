#!/usr/bin/env python3
"""Centralized configuration for RhinoMCP scripts."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("rhinomcp.config")

# Config file location (relative to scripts/ dir, NOT clawdbot/ dir)
CONFIG_PATH = Path(__file__).parent.parent / "config.json"


@dataclass
class ConnectionConfig:
    host: str = "172.31.96.1"
    port: int = 1999
    timeout: float = 15.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class ScreenshotConfig:
    default_width: int = 1920
    default_height: int = 1080
    linux_dir: str = ""
    windows_dir: str = ""


@dataclass
class DefaultsConfig:
    layer: str = "Default"
    color: List[int] = field(default_factory=lambda: [128, 128, 128])


@dataclass
class LoggingConfig:
    log_file: str = ""
    tail_lines: int = 30


class Config:
    """Singleton configuration manager."""

    _instance: Optional['Config'] = None

    def __init__(self) -> None:
        self.connection = ConnectionConfig()
        self.screenshots = ScreenshotConfig()
        self.defaults = DefaultsConfig()
        self.logging = LoggingConfig()
        self._raw: dict = {}
        self._load()

    @classmethod
    def get(cls) -> 'Config':
        """Get the singleton config instance."""
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def _load(self) -> None:
        """Load configuration from config.json."""
        if not CONFIG_PATH.exists():
            logger.warning(f"Config file not found: {CONFIG_PATH}")
            return

        try:
            with open(CONFIG_PATH) as f:
                self._raw = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load config: {e}")
            return

        # Connection
        conn = self._raw.get("connection", {})
        self.connection = ConnectionConfig(
            host=conn.get("host", self.connection.host),
            port=conn.get("port", self.connection.port),
            timeout=conn.get("timeout", self.connection.timeout),
            max_retries=conn.get("max_retries", self.connection.max_retries),
            retry_delay=conn.get("retry_delay", self.connection.retry_delay),
        )

        # Screenshots
        ss = self._raw.get("screenshots", {})
        self.screenshots = ScreenshotConfig(
            default_width=ss.get("default_width", self.screenshots.default_width),
            default_height=ss.get("default_height", self.screenshots.default_height),
            linux_dir=ss.get("linux_dir", self.screenshots.linux_dir),
            windows_dir=ss.get("windows_dir", self.screenshots.windows_dir),
        )

        # Defaults
        defs = self._raw.get("defaults", {})
        self.defaults = DefaultsConfig(
            layer=defs.get("layer", self.defaults.layer),
            color=defs.get("color", self.defaults.color),
        )

        # Logging
        log = self._raw.get("logging", {})
        self.logging = LoggingConfig(
            log_file=log.get("log_file", self.logging.log_file),
            tail_lines=log.get("tail_lines", self.logging.tail_lines),
        )

        logger.debug(f"Config loaded from {CONFIG_PATH}")

    @property
    def raw(self) -> dict:
        """Access raw config dict for backward compatibility."""
        return self._raw
