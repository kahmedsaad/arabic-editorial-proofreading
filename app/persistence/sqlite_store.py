"""Backward-compatible alias — ReviewStore is now DemoStore. """

from app.persistence.demo_store import DemoStore as ReviewStore

__all__ = ["ReviewStore"]
