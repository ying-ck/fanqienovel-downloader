import requests as req
from lxml import etree
import json,time,random
from os.path import exists

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

def filencl(s):
    a = ''
    for i in s:
        if i == '*':
            a += '＊'
        elif i == '/':
            a += '／'
        elif i == '\\':
            a += '＼'
        elif i == '?':
            a += '？'
        elif i == ':':
            a += '：'
        elif i == '>':
            a += '＞'
        elif i == '<':
            a += '＜'
        elif i == '"':
            a += '＂'
        elif i == '|':
            a += '｜'
        else:
            a += i
    return a

def down_zj(it):
    global headers
    an = {}
    ele = etree.HTML(req.get('https://fanqienovel.com/page/'+str(it),headers=headers).text)
    a = ele.xpath('//div[@class="chapter"]/div/a')
    for i in range(len(a)):
        an[a[i].text] = a[i].xpath('@href')[0].split('/')[-1]
    if ele.xpath('//h1/text()')==[]:
        return ['err',0,0]
    return [filencl(ele.xpath('//h1/text()')[0]),an,ele.xpath('//span[@class="info-label-yellow"]/text()')]

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
    return s.replace('<\/p>','').replace('<p>', '').replace('</p>', '\n')

def down_book(it):
    f = False
    name,zj,zt = down_zj(it)
    if name=='err':
        return 'err'
    zt = zt[0]
    print('开始下载《%s》，状态‘%s’'%(name,zt))
    if exists(name+'.json'):
        f = True
        ozj = json.loads(open(name+'.json','r',encoding='UTF-8').read())
    for i in zj:
        if f and i in ozj and len(ozj[i])>30:
            zj[i] = ozj[i]
        else:
            print('下载',i)
            zj[i] = down_text(zj[i])
            time.sleep(random.random()/2)
            open(name+'.json','w',encoding='UTF-8').write(json.dumps(zj))
    f = open(name+'.txt','w',encoding='UTF-8')
    for i in zj:
        f.writelines(i+'\n')
        f.writelines(zj[i]+'\n')
    f.close()
    return zt

print('本程序完全免费。\nGithub: https://github.com/ying-ck/fanqienovel-downloader\n作者：Yck')
while True:
    print('\n请输入书的id(输gx更新):')
    inp = input()
    if inp=='gx':
        re = json.loads(open('record.json','r',encoding='UTF-8').read())
        for i in re:
            if down_book(i)=='已完结':
                re.pop(re.index(i))
        print('更新完成')
    else:
        try:
            int(inp)
        except:
            print('请输入纯数字')
            continue
        if exists('record.json'):
            re = json.loads(open('record.json','r',encoding='UTF-8').read())
            if not inp in re:
                re.append(inp)
        else:
            re = [inp]
        open('record.json','w',encoding='UTF-8').write(json.dumps(re))
        if down_book(inp)=='err':
            print('找不到此书')
        else:
            print('下载完成')


















