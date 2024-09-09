import random,time,json,os
from tkinter import Tk,filedialog
import requests as req
from lxml import etree

import config

def sanitize_filename(filename: str) -> str:
    illegal_chars=['<','>',':','"','/','\\','|','?','*']
    illegal_chars_rep=['＜','＞','：','＂','／','＼','｜','？','＊']
    for i in range(len(illegal_chars)):
        filename=filename.replace(illegal_chars[i],illegal_chars_rep[i])
    return filename


def interpreter(uni: int,mode: int) -> str:
    bias=uni-config.CODE[mode][0]
    if bias<0 or bias>=len(config.charset[mode]) or config.charset[mode][bias]=='?':
        return chr(uni)
    return config.charset[mode][bias]


def str_interpreter(n: str,mode: int) -> str:
    s=''
    for i in range(len(n)):
        uni=ord(n[i])
        if config.CODE[mode][0]<=uni<=config.CODE[mode][1]:
            s+=interpreter(uni,mode)
        else:
            s+=n[i]
    return s


def select_save_directory() -> str:
    root=Tk()
    root.withdraw()  # 隐藏主窗口
    return filedialog.askdirectory(title='请选择保存小说的文件夹')


def loadjson(path: str) -> [dict]:
    with open(path,'r',encoding='UTF-8') as f:
        file=json.load(f)
    return file


def savejson(path: str,file: dict) -> None:
    with open(path,'w',encoding='UTF-8') as f:
        json.dump(file,f,ensure_ascii=False)


def down_init(it: str) -> tuple[dict,dict[str,str],str]:
    name,zj,status=down_chapter(it)
    if not name:
        return {},{},''
    status=status[0]
    name=sanitize_filename(name)
    print('\n开始下载《%s》，状态‘%s’'%(name,status))
    book_json_path=os.path.join(config.bookstore_dir,name+'.json')

    if os.path.exists(book_json_path):
        with open(book_json_path,'r',encoding='UTF-8') as json_file:
            ozj=json.load(json_file)
    else:
        ozj={}
    return ozj,zj,name


def check_redown(title: str,ozj: dict) -> bool:
    if title in ozj:
        try:
            int(ozj[title])
            return False
        except ValueError:
            return True
    return True


def get_cookie(chapter: str,t: str='') -> bool:
    bas=1000000000000000000
    if not t:
        for i in range(random.randint(bas*6,bas*8),bas*9):
            time.sleep(random.randint(50,150)/1000)
            config.cookie='novel_web_id='+str(i)
            if len(down_text(chapter,2)[0])>200:
                with open(config.cookie_path,'w',encoding='UTF-8') as f:
                    json.dump(config.cookie,f)
                return True
    else:
        if len(down_text(chapter,2)[0])>200:
            config.cookit=t
            return True
        else:
            return False


def down_chapter(it: str)->tuple[str,dict[str,str],list[str]]:

    an:dict[str:str]={}

    ele=etree.HTML(req.get('https://fanqienovel.com/page/'+it,headers=config.headers).text)
    a=ele.xpath('//div[@class="chapter"]/div/a')
    for t in a:
        an[t.text]=t.xpath('@href')[0].split('/')[-1]
    if not ele.xpath('//h1/text()'):
        return '',{},[]
    return ele.xpath('//h1/text()')[0],an,ele.xpath('//span[@class="info-label-yellow"]/text()')


def update_save(st:int,tcs:int,cs:int,book_json_path:str,chapter:dict)->tuple[int,int]:
    if st:
        tcs += 1
        if tcs > 7:
            tcs = 0
            get_cookie(config.tzj)
    cs += 1
    if cs >= 5:
        cs = 0
        savejson(book_json_path, chapter)
    return tcs,cs

def down_text(idx:str,mod:int=1) -> tuple[str,bool]:
    headers2=config.headers
    headers2['cookie']=config.cookie
    f=False
    while True:
        try:
            res=req.get('https://fanqienovel.com/api/reader/full?itemId='+idx,headers=headers2)
            n=res.json()['data']['chapterData']['content']
            break
        except:  # 捕获所有异常
            if mod == 2:
                return 'err',f
            f = True
            time.sleep(0.4)
    if mod==1:
        s=str_interpreter(n,0)
    else:
        s=n
    try:
        return '\n'.join(etree.HTML(s).xpath('//p/text()')),f
    except:
        s=s[6:]
        tmp=1
        a=''
        for i in s:
            if i=='<':
                tmp+=1
            elif i=='>':
                tmp-=1
            elif tmp==0:
                a+=i
            elif tmp==1 and i=='p':
                a=(a+'\n').replace('\n\n','\n')
        return a,f
