import os, json
from bs4 import BeautifulSoup
import requests as req


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


def update_records(path: str, novel_id: int):
    """Update download records"""
    if os.path.exists(path):
        with open(path, 'r', encoding='UTF-8') as f:
            records=json.load(f)
    else:
        records=[]

    if novel_id not in records:
        records.append(novel_id)
        with open(path, 'w', encoding='UTF-8') as f:
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

def get_author_info(self, novel_id: int) -> str | None:
    """Get author information from novel page"""
    url = f'https://fanqienovel.com/page/{novel_id}'
    try:
        response = req.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', type="application/ld+json")
        if script_tag:
            data = json.loads(script_tag.string)
            if 'author' in data:
                return data['author'][0]['name']
    except Exception as e:
        self.log_callback(f"获取作者信息失败: {str(e)}")
    return None