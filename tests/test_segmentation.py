from app.models.schemas import Document
from app.segmentation.article import segment_article


def test_stable_segment_ids_and_zones():
    doc = Document(
        document_id="DOC-001",
        headline="عنوان تجريبي",
        body="الفقرة الأولى.\n\nالفقرة الثانية.",
    )
    segments = segment_article(doc)
    assert [s.segment_id for s in segments] == ["SEG-001", "SEG-002", "SEG-003"]
    assert segments[0].zone.value == "headline"
    assert segments[1].zone.value == "body"
    assert segments[0].start_offset == 0
    assert segments[0].end_offset == len(segments[0].text)
    assert segments[0].text == "عنوان تجريبي"
