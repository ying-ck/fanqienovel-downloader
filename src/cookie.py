import json, os, time, random

def _get_testid(self) -> int:
    """Get an initial chapter ID for cookie testing"""
    test_novel_id = 7143038691944959011  # Example novel ID
    chapters = self._get_chapter_list(test_novel_id)
    if chapters and len(chapters[1]) > 21:
        return int(random.choice(list(chapters[1].values())[21:]))
    raise Exception("Failed to get initial chapter ID")

def _test(self, chapter_id: int, cookie: str) -> bool:
    """Test if cookie is valid"""
    self.cookie = cookie
    if len(self._download_chapter_content(chapter_id, test_mode=True)) > 200:
        return True
    return False

def init(self):
    """Initialize cookie for downloads"""
    self.log_callback('正在获取cookie')
    tzj = _get_testid(self)

    if os.path.exists(self.cookie_path):
        with open(self.cookie_path, 'r', encoding='UTF-8') as f:
            self.cookie = json.load(f)
            if not _test(self, tzj, self.cookie):
                get(self, tzj)
    else:
        get(self, tzj)

    self.log_callback('Cookie获取成功')

def get(self, chapter_id: int):
    """Generate new cookie"""
    bas = 1000000000000000000
    for i in range(random.randint(bas * 6, bas * 8), bas * 9):
        time.sleep(random.randint(50, 150) / 1000)
        self.cookie = f'novel_web_id={i}'
        if len(self._download_chapter_content(chapter_id, test_mode=True)) > 200:
            with open(self.cookie_path, 'w', encoding='UTF-8') as f:
                json.dump(self.cookie, f)
            return