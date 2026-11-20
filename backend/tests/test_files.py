from app.utils.files import safe_filename

def test_filename_is_sanitized():
    assert safe_filename("../../resume.pdf").endswith(".pdf")
    assert "/" not in safe_filename("resume.pdf")
