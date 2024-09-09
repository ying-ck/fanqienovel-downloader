from . import *

def down_book(it:str) -> bool:
    ozj,chapter,name=utils.down_init(it)
    if not name:
        return False
    book_json_path:str=os.path.join(config.bookstore_dir,name+'.json')
    tcs,cs=0,0
    pbar=tqdm(total=len(chapter))
    for title,idx in chapter.items():
        if utils.check_redown(title,ozj):
            tqdm.write(f'下载 {title}')
            chapter[title],st=utils.down_text(idx)
            time.sleep(random.randint(config.config['delay'][0],config.config['delay'][1])/1000)
            tcs,cs=utils.update_save(st,tcs,cs,book_json_path,chapter)
        else:
            chapter[title]=ozj[title]
        pbar.update(1)
    utils.savejson(book_json_path,chapter)

    fg='\n'+config.config['kgf']*config.config['kg']
    if config.config['save_mode']==1:
        text_file_path=os.path.join(config.save_path,name+'.txt')
        with open(text_file_path,'w',encoding='UTF-8') as text_file:
            for chapter_title in chapter:
                text_file.write('\n'+chapter_title+fg)
                if config.config['kg']==0:
                    text_file.write(chapter[chapter_title]+'\n')
                else:
                    text_file.write(chapter[chapter_title].replace('\n',fg)+'\n')
    elif config.config['save_mode']==2:
        text_dir_path=os.path.join(config.save_path,name)
        if not os.path.exists(text_dir_path):
            os.makedirs(text_dir_path)
        for chapter_title in chapter:
            text_file_path=os.path.join(text_dir_path,utils.sanitize_filename(chapter_title)+'.txt')
            with open(text_file_path,'w',encoding='UTF-8') as text_file:
                text_file.write(fg)
                if config.config['kg']==0:
                    text_file.write(chapter[chapter_title]+'\n')
                else:
                    text_file.write(chapter[chapter_title].replace('\n',fg)+'\n')

    else:
        print('保存模式出错！')

    return True