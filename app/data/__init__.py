"""Dataset I/O package.

External Arabic news corpora are for silence testing and structure — they are
NOT Al Jazeera house-style policy. Private gold and licensed material belong
in GCS private/ prefixes, never in GitHub.
"""

from app.data.loader import get_dataset_loader, resolve_loader_for_path
from app.data.models import (
    BeforeAfterRecord,
    CleanArticleRecord,
    DatasetManifest,
    EditorFeedbackRecord,
    SyntheticIssueRecord,
)

__all__ = [
    "BeforeAfterRecord",
    "CleanArticleRecord",
    "DatasetManifest",
    "EditorFeedbackRecord",
    "SyntheticIssueRecord",
    "get_dataset_loader",
    "resolve_loader_for_path",
]
