import requests as req
from lxml import etree
import json,time,random,os

CODE_ST = 58344
CODE_ED = 58715
charset=[
"D",
"在",
"主",
"特",
"家",
"军",
"然",
"表",
"场",
"4",
"要",
"只",
"v",
"和",
"?",
"6",
"别",
"还",
"g",
"现",
"儿",
"岁",
"?",
"?",
"此",
"象",
"月",
"3",
"出",
"战",
"工",
"相",
"o",
"男",
"直",
"失",
"世",
"F",
"都",
"平",
"文",
"什",
"V",
"O",
"将",
"真",
"T",
"那",
"当",
"?",
"会",
"立",
"些",
"u",
"是",
"十",
"张",
"学",
"气",
"大",
"爱",
"两",
"命",
"全",
"后",
"东",
"性",
"通",
"被",
"1",
"它",
"乐",
"接",
"而",
"感",
"车",
"山",
"公",
"了",
"常",
"以",
"何",
"可",
"话",
"先",
"p",
"i",
"叫",
"轻",
"M",
"士",
"w",
"着",
"变",
"尔",
"快",
"l",
"个",
"说",
"少",
"色",
"里",
"安",
"花",
"远",
"7",
"难",
"师",
"放",
"t",
"报",
"认",
"面",
"道",
"S",
"?",
"克",
"地",
"度",
"I",
"好",
"机",
"U",
"民",
"写",
"把",
"万",
"同",
"水",
"新",
"没",
"书",
"电",
"吃",
"像",
"斯",
"5",
"为",
"y",
"白",
"几",
"日",
"教",
"看",
"但",
"第",
"加",
"候",
"作",
"上",
"拉",
"住",
"有",
"法",
"r",
"事",
"应",
"位",
"利",
"你",
"声",
"身",
"国",
"问",
"马",
"女",
"他",
"Y",
"比",
"父",
"x",
"A",
"H",
"N",
"s",
"X",
"边",
"美",
"对",
"所",
"金",
"活",
"回",
"意",
"到",
"z",
"从",
"j",
"知",
"又",
"内",
"因",
"点",
"Q",
"三",
"定",
"8",
"R",
"b",
"正",
"或",
"夫",
"向",
"德",
"听",
"更",
"?",
"得",
"告",
"并",
"本",
"q",
"过",
"记",
"L",
"让",
"打",
"f",
"人",
"就",
"者",
"去",
"原",
"满",
"体",
"做",
"经",
"K",
"走",
"如",
"孩",
"c",
"G",
"给",
"使",
"物",
"?",
"最",
"笑",
"部",
"?",
"员",
"等",
"受",
"k",
"行",
"一",
"条",
"果",
"动",
"光",
"门",
"头",
"见",
"往",
"自",
"解",
"成",
"处",
"天",
"能",
"于",
"名",
"其",
"发",
"总",
"母",
"的",
"死",
"手",
"入",
"路",
"进",
"心",
"来",
"h",
"时",
"力",
"多",
"开",
"已",
"许",
"d",
"至",
"由",
"很",
"界",
"n",
"小",
"与",
"Z",
"想",
"代",
"么",
"分",
"生",
"口",
"再",
"妈",
"望",
"次",
"西",
"风",
"种",
"带",
"J",
"?",
"实",
"情",
"才",
"这",
"?",
"E",
"我",
"神",
"格",
"长",
"觉",
"间",
"年",
"眼",
"无",
"不",
"亲",
"关",
"结",
"0",
"友",
"信",
"下",
"却",
"重",
"己",
"老",
"2",
"音",
"字",
"m",
"呢",
"明",
"之",
"前",
"高",
"P",
"B",
"目",
"太",
"e",
"9",
"起",
"稜",
"她",
"也",
"W",
"用",
"方",
"子",
"英",
"每",
"理",
"便",
"四",
"数",
"期",
"中",
"C",
"外",
"样",
"a",
"海",
"们",
"任"
]

headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
}

def down_zj(it):
    global headers
    an = {}
    ele = etree.HTML(req.get('https://fanqienovel.com/page/'+str(it),headers=headers).text)
    a = ele.xpath('//div[@class="chapter"]/div/a')
    for i in range(len(a)):
        an[a[i].text] = a[i].xpath('@href')[0].split('/')[-1]
    if ele.xpath('//h1/text()')==[]:
        return ['err',0,0]
    return [ele.xpath('//h1/text()')[0],an,ele.xpath('//span[@class="info-label-yellow"]/text()')]

def interpreter(uni):
    global CODE_ST,charset
    bias = uni - CODE_ST
    if bias < 0 or bias >= len(charset) or charset[bias] =='?':
        return chr(uni)
    return charset[bias]

def down_text(it):
    global CODE_ST,CODE_ED,headers
    headers2 = headers
    headers2['cookie'] = 'novel_web_id=7357767624615331362'
    while True:
        res = req.get('https://fanqienovel.com/api/reader/full?itemId='+str(it),headers=headers2)
        n = json.loads(res.text)['data']
        if 'chapterData' in n:
            break
        time.sleep(0.5)
    n = n['chapterData']['content']
    s = ''
    for i in range(len(n)):
        uni = ord(n[i])
        if CODE_ST <= uni <= CODE_ED:
            s += interpreter(uni)
        else:
            s += n[i]
    try:
        return '\n'.join(etree.HTML(s).xpath('//p/text()'))
    except:
        s = s[6:]
        tmp = 1
        a = ''
        for i in s:
            if i=='<':
                tmp += 1
            elif i=='>':
                tmp -= 1
            elif tmp==0:
                a += i
            elif tmp==1 and i=='p':
                a = (a+'\n').replace('\n\n','\n')
        return a

def sanitize_filename(filename):
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    illegal_chars_rep = ['＜','＞','：','＂','／','＼','｜','？','＊']
    for i in range(len(illegal_chars)):
        filename = filename.replace(illegal_chars[i], illegal_chars_rep[i])
    return filename


def down_book(it, config_obj):
    name, zj, zt = down_zj(it)
    if name == 'err':
        return 'err'
    zt = zt[0]

    safe_name = sanitize_filename(name)
    book_dir = os.path.join(script_dir, safe_name)

    print('\n开始下载《%s》，状态‘%s’' % (name, zt))
    book_json_path = os.path.join(bookstore_dir, safe_name + '.json')

    if os.path.exists(book_json_path):
        with open(book_json_path, 'r', encoding='UTF-8') as json_file:
            ozj = json.load(json_file)
    else:
        ozj = {}
    
    cs = 0
    for i in zj:
        f = False
        if i in ozj:
            try:
                int(ozj[i])
                f = True
            except:
                zj[i] = ozj[i]
        else:
            f = True
        if f:
            print('下载', i)
            zj[i] = down_text(zj[i])
            time.sleep(random.random() / 3)
            cs += 1
            if cs>=5:
                cs = 0
                with open(book_json_path, 'w', encoding='UTF-8') as json_file:
                    json.dump(zj, json_file,ensure_ascii=False)

    with open(book_json_path, 'w', encoding='UTF-8') as json_file:
        json.dump(zj, json_file,ensure_ascii=False)

    text_file_path = os.path.join(script_dir, safe_name + '.txt')
    with open(text_file_path, 'w', encoding='UTF-8') as text_file:
        fg = '\n' + ' ' * config_obj['kg']
        for chapter_title in zj:
            text_file.write(chapter_title + fg)
            if config_obj['kg'] == 0:
                text_file.write(zj[chapter_title] + '\n')
            else:
                text_file.write(zj[chapter_title].replace('\n', fg) + '\n')

    return zt

#script_dir = os.path.dirname(os.path.abspath(__file__))
script_dir = ''

# 设置data文件夹的路径
data_dir = os.path.join(script_dir, 'data')

# 检查data文件夹是否存在，如果不存在则创建
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 设置bookstore文件夹的路径
bookstore_dir = os.path.join(data_dir,'bookstore')

# 检查bookstore文件夹是否存在，如果不存在则创建
if not os.path.exists(bookstore_dir):
    os.makedirs(bookstore_dir)

# 更新record.json和config.json的文件路径
record_path = os.path.join(data_dir, 'record.json')
config_path = os.path.join(data_dir, 'config.json')

# 打印程序信息
# 打印程序信息
os.popen('title fanqienovel-downloader v1.0.6')
print('本程序完全免费。\nGithub: https://github.com/ying-ck/fanqienovel-downloader\n作者：Yck & qxqycb')

# 检查并创建配置文件config.json
config_path = os.path.join(data_dir, 'config.json')
if not os.path.exists(config_path):
    if os.path.exists('config.json'):
        os.replace('config.json',config_path)
    else:
        with open(config_path, 'w', encoding='UTF-8') as f:
            json.dump({'kg': 0}, f)
else:
    with open(config_path, 'r', encoding='UTF-8') as f:
        config = json.load(f)

# 检查并创建记录文件record.json
record_path = os.path.join(data_dir, 'record.json')
if not os.path.exists(record_path):
    if os.path.exists('record.json'):
        os.replace('record.json',record_path)
    else:
        with open(record_path, 'w', encoding='UTF-8') as f:
            json.dump([], f)

# 主循环
while True:
    print('\n输入书的id直接下载\n输入下面的数字进入其他功能:')
    print('''
1. 更新小说列表
2. 设置
3. 退出
''')

    inp = input()

    if inp == '1':
        # 更新操作
        with open(record_path, 'r', encoding='UTF-8') as f:
            records = json.load(f)
        for book_id in records:
            with open(config_path, 'r', encoding='UTF-8') as f:
                config = json.load(f)
            status = down_book(book_id, config)
            if status == 'err' or status == '已完结':
                records.remove(book_id)
        with open(record_path, 'w', encoding='UTF-8') as f:
            json.dump(records, f)
        print('更新完成')

    elif inp == '2':
        # 设置操作
        with open(config_path, 'r', encoding='UTF-8') as f:
            config = json.load(f)
        config['kg'] = int(input('请输入正文段首空格数（当前为%d）：' % config['kg']))
        with open(config_path, 'w', encoding='UTF-8') as f:
            json.dump(config, f)
            
    elif inp == '3':
        break
    
    else:
        # 下载新书或更新现有书籍
        try:
            book_id = int(inp)
            with open(record_path, 'r', encoding='UTF-8') as f:
                records = json.load(f)
            if book_id not in records:
                records.append(book_id)
            with open(record_path, 'w', encoding='UTF-8') as f:
                json.dump(records, f)
            with open(config_path, 'r', encoding='UTF-8') as f:
                config = json.load(f)
            status = down_book(book_id, config)
            if status == 'err':
                print('找不到此书')
            else:
                print('下载完成')
        except ValueError:
            print('请输入有效的选项或书籍ID。')
