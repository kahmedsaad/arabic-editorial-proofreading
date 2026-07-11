"""Phase 7 GCP adapters — stubs only. Not wired yet.

When Phase 7 starts, implement:
- Cloud Storage for documents/datasets
- Firestore for rules/reviews
- Vertex AI Gemini configuration
- Cloud Run Dockerfile adjustments

Local mode must keep working with USE_GCP=false.
"""

from __future__ import annotations


class NotImplementedGCPAdapter:
    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        raise NotImplementedError(
            "GCP adapters are not implemented yet. Set USE_GCP=false and continue locally."
        )


CloudStorageAdapter = NotImplementedGCPAdapter
FirestoreAdapter = NotImplementedGCPAdapter
VertexGeminiConfig = NotImplementedGCPAdapter
