from . import *


def down_book_md(it: str) -> bool:
    ozj,chapter,name=utils.down_init(it)
    if not name:
        return False
    book_json_path=os.path.join(config.bookstore_dir,name+'.json')
    md_content=f"# {name}\n\n"

    tcs,cs=0,0
    pbar=tqdm(total=len(chapter))
    for title,idx in chapter.items():
        if utils.check_redown(title,ozj):
            tqdm.write(f'下载 {title}')
            content,st=utils.down_text(idx)
            time.sleep(random.randint(config.config['delay'][0],config.config['delay'][1])/1000)
            tcs,cs=utils.update_save(st,tcs,cs,book_json_path,chapter)
            content=content.replace('\n','  \n')
            md_content+=f"## {title}\n\n{content}\n\n"
        else:
            chapter[title]=ozj[title]
        pbar.update(1)
    utils.savejson(book_json_path,chapter)
    # 保存为Markdown文件
    md_file_path=os.path.join(config.save_path,f'{name}.md')
    with open(md_file_path,'w',encoding='utf-8') as md_file:
        md_file.write(md_content)

    return True
