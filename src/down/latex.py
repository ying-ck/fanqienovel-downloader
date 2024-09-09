from . import *

def down_book_latex(it: str) -> bool:
    ozj,chapter,name=utils.down_init(it)
    latex_content=""
    book_json_path:str=os.path.join(config.bookstore_dir,name+'.json')

    tcs,cs=0,0
    pbar=tqdm(total=len(chapter))
    for title,idx in chapter.items():
        if utils.check_redown(title,ozj):
            tqdm.write(f'下载 {title}')
            chapter[title],st=utils.down_text(idx)
            time.sleep(random.randint(config.config['delay'][0],config.config['delay'][1])/1000)
            tcs,cs=utils.update_save(st,tcs,cs,book_json_path,chapter)
            formatted_content = chapter[title].replace('\n', '\\newline ')
            latex_content += f"\\chapter{{{title}}}\n{formatted_content}\n"

        else:
            chapter[title]=ozj[title]
        pbar.update(1)
    utils.savejson(book_json_path,chapter)
    # 在脚本所在目录下输出 LaTeX 文件
    latex_file_path=os.path.join(config.save_path,f'{name}.tex')
    with open(latex_file_path,'w',encoding='UTF-8') as latex_file:
        latex_file.write(latex_content)

    return True

