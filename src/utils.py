import os, json


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for different platforms"""
    illegal_chars=['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    illegal_chars_rep=['＜', '＞', '：', '＂', '／', '＼', '｜', '？', '＊']
    for old, new in zip(illegal_chars, illegal_chars_rep):
        filename=filename.replace(old, new)
    return filename


def decode_content(self, content: str, mode: int = 0) -> str:
    """Decode novel content using both charset modes"""
    result=''
    for char in content:
        uni=ord(char)
        if self.CODE[mode][0]<=uni<=self.CODE[mode][1]:
            bias=uni-self.CODE[mode][0]
            if 0<=bias<len(self.charset[mode]) and self.charset[mode][bias]!='?':
                result+=self.charset[mode][bias]
            else:
                result+=char
        else:
            result+=char
    return result


def update_records(self, novel_id: int):
    """Update download records"""
    if os.path.exists(self.record_path):
        with open(self.record_path, 'r', encoding='UTF-8') as f:
            records=json.load(f)
    else:
        records=[]

    if novel_id not in records:
        records.append(novel_id)
        with open(self.record_path, 'w', encoding='UTF-8') as f:
            json.dump(records, f)


def save_progress(self, title: str, content: str):
    """Save download progress"""
    self.zj[title]=content
    with open(self.book_json_path, 'w', encoding='UTF-8') as f:
        json.dump(self.zj, f, ensure_ascii=False)

def parse_novel_id(self, novel_id: str) -> int | None:
    """Parse novel ID from input (URL or ID)"""
    if isinstance(novel_id, str) and novel_id.startswith('http'):
        novel_id = novel_id.split('?')[0].split('/')[-1]
    try:
        return int(novel_id)
    except ValueError:
        self.log_callback(f'Invalid novel ID: {novel_id}')
        return None