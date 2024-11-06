from ebooklib import epub
from bs4 import BeautifulSoup
import requests as req
import json
from src import settings

def get_cover_url(self, novel_id: int) -> str | None:
    """Get cover image URL from novel page"""
    url = f'https://fanqienovel.com/page/{novel_id}'
    try:
        response = req.get(url, headers=settings.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', type="application/ld+json")
        if script_tag:
            data = json.loads(script_tag.string)
            if 'image' in data:
                return data['image'][0]
    except Exception as e:
        self.log_callback(f"获取封面图片失败: {str(e)}")
    return None


def add_cover(self, book: epub.EpubBook, cover_url: str):
    """Add cover image to EPUB book"""
    try:
        response = req.get(cover_url)
        if response.status_code == 200:
            book.set_cover('cover.jpg', response.content)

            # Add cover page
            cover_content = f'''
                    <div style="text-align: center; padding: 0; margin: 0;">
                        <img src="cover.jpg" alt="Cover" style="max-width: 100%; height: auto;"/>
                    </div>
                '''
            cover_page = epub.EpubHtml(
                title='Cover',
                file_name='cover.xhtml',
                content=cover_content,
                media_type='image/jpeg'
            )
            book.add_item(cover_page)
            book.spine.insert(0, cover_page)
    except Exception as e:
        self.log_callback(f"添加封面失败: {str(e)}")