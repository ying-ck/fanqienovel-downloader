import json,os,random
import config,utils


def ensure_dir_exists(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)

def init_config() -> None:
    # 确保数据目录和书籍存储目录存在
    config.data_dir = os.path.join(config.script_dir, 'data')
    config.bookstore_dir = os.path.join(config.data_dir, 'bookstore')
    ensure_dir_exists(config.data_dir)
    ensure_dir_exists(config.bookstore_dir)

    # 初始化 record 文件
    config.record_path = os.path.join(config.data_dir, 'record.json')
    if not os.path.exists(config.record_path):
        with open(config.record_path, 'w', encoding='UTF-8') as f:
            json.dump([], f)

    config.cookie_path = os.path.join(config.data_dir, 'cookie.json')

    # 加载或初始化 config 文件
    config.config_path = os.path.join(config.data_dir, 'config.json')
    if os.path.exists(config.config_path):
        with open(config.config_path, 'r', encoding='UTF-8') as f:
            config.config = json.load(f)
        # 只添加缺失的配置项
        config.config.update({k: v for k, v in config.default_config.items() if k not in config.config})
    else:
        config.config = config.default_config
        with open(config.config_path, 'w', encoding='UTF-8') as f:
            json.dump(config.default_config, f)

    # 设置保存路径
    config.save_path = os.path.join(config.script_dir, str(config.config['save_path']))
    ensure_dir_exists(config.save_path)

    # 随机选择请求头
    config.headers = random.choice(config.headers_lib)

    # 初始化 cookie
    init_cookie()



def init_cookie() -> None:
    print('本程序完全免费。\nGithub: https://github.com/ying-ck/fanqienovel-downloader\n作者：Yck & qxqycb')
    print('modifyed by sstzer')
    print('正在获取cookie')

    config.tzj=random.choice(list(utils.down_chapter('7143038691944959011')[1].values())[21:])

    tmod=0

    if os.path.exists(config.cookie_path):
        with open(config.cookie_path,'r',encoding='UTF-8') as f:
            config.cookie=json.load(f)
        tmod=1

    if tmod==0 or not utils.get_cookie(config.tzj,config.cookie):
        utils.get_cookie(config.tzj)

    print('成功')
