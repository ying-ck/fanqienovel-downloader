
def sanitize_filename(filename: str) -> str:
    """Sanitize filename for different platforms"""
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    illegal_chars_rep = ['＜', '＞', '：', '＂', '／', '＼', '｜', '？', '＊']
    for old, new in zip(illegal_chars, illegal_chars_rep):
        filename = filename.replace(old, new)
    return filename