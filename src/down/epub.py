from . import *
from ebooklib import epub

def down_book_epub(it: str) -> bool:
    ozj,chapter,name=utils.down_init(it)
    if not name:
        return False
    book_json_path=os.path.join(config.bookstore_dir,name+'.json')
    book = epub.EpubBook()
    book.set_title(name)
    book.set_language('zh')

    # 创建目录列表
    toc=[]
    tcs,cs=0,0
    pbar=tqdm(total=len(chapter))
    for title,idx in chapter.items():
        if utils.check_redown(title,ozj):

            tqdm.write(f'下载 {title}')
            content,st=utils.down_text(idx)
            time.sleep(random.randint(config.config['delay'][0],config.config['delay'][1])/1000)
            tcs,cs=utils.update_save(st,tcs,cs,book_json_path,chapter)
            formatted_content=content.replace('\n','<br/>')
            epub_chapter=epub.EpubHtml(title=title,file_name=f'{title}.xhtml',content=f'<h1>{title}</h1><p>{formatted_content}</p>')
            book.add_item(epub_chapter)
            toc.append((epub.Section(title),[epub_chapter]))
            book.spine.append(epub_chapter)
        else:
            chapter[title]=ozj[title]
        pbar.update(1)
    utils.savejson(book_json_path,chapter)
    # 设置目录
    book.toc=toc
    # 添加目录文件
    book.add_item(epub.EpubNcx())
    # 编写 EPUB 文件
    epub.write_epub(os.path.join(config.save_path, f'{name}.epub'), book, {})

    return True
