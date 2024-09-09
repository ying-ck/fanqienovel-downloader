from . import *
import htmlformat as html


def down_book_html(it: str) -> bool:
    ozj,chapter,name=utils.down_init(it)
    book_dir=os.path.join(config.save_path,f"{name}(html)")
    if not os.path.exists(book_dir):
        os.makedirs(book_dir)

    # 将目录内容写入文件
    with open(os.path.join(book_dir,"index.html"),"w",encoding='UTF-8') as toc_file:
        toc_file.write(html.get_toc_content(chapter))

    book_json_path:str=os.path.join(config.bookstore_dir,name+'.json')

    tcs,cs=0,0
    pbar=tqdm(total=len(chapter))
    for title,idx in chapter.items():
        if utils.check_redown(title,ozj):
            tqdm.write(f'下载 {title}')
            chapter[title],st=utils.down_text(idx)
            time.sleep(random.randint(config.config['delay'][0],config.config['delay'][1])/1000)
            tcs,cs=utils.update_save(st,tcs,cs,book_json_path,chapter)
            with open(os.path.join(book_dir,f"{title}.html"),"w",encoding='UTF-8') as chapter_file:
                chapter_file.write(html.get_chapter_htmlcontent(title,chapter[title],chapter))
        else:
            chapter[title]=ozj[title]
        pbar.update(1)
    utils.savejson(book_json_path,chapter)
    return True
