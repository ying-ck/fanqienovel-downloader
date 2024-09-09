from . import *
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# 注册字体和粗体字体
pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))  # 正常字体
pdfmetrics.registerFont(TTFont('SimHei', 'simhei.ttf'))  # 粗体字体

def down_book_pdf(it: str) -> bool:
    ozj, chapter, name = utils.down_init(it)
    if not name:
        return False
    book_json_path = os.path.join(config.bookstore_dir, name + '.json')

    pdf_file_path = os.path.join(config.save_path, f'{name}.pdf')
    doc = SimpleDocTemplate(pdf_file_path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=64, bottomMargin=64)

    # 样式设置
    styles = getSampleStyleSheet()

    # 设置书名样式为粗体
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        fontName='SimHei',  # 使用粗体字体
        alignment=TA_CENTER,
        fontSize=24,
        spaceAfter=12,  # 增加书名后的间距
    )

    # 设置章节标题样式为粗体
    chapter_style = ParagraphStyle(
        name="ChapterStyle",
        parent=styles["Heading2"],
        fontName='SimHei',  # 使用粗体字体
        fontSize=22,
        spaceAfter=10,  # 增加章节标题后的间距
    )

    # 正文样式使用普通字体
    content_style = ParagraphStyle(
        name="ContentStyle",
        parent=styles["BodyText"],
        fontName='SimSun',
        fontSize=18,
        leading=22,  # 行间距
        spaceAfter=8,  # 段落间距
    )

    # 添加书名
    story = [Paragraph(name, title_style), Spacer(1, 24)]
    tcs,cs=0,0
    pbar = tqdm(total=len(chapter))
    for title, idx in chapter.items():
        if utils.check_redown(title, ozj):
            tqdm.write(f'下载 {title}')
            content, st = utils.down_text(idx)
            time.sleep(random.randint(config.config['delay'][0], config.config['delay'][1]) / 1000)
            tcs,cs=utils.update_save(st,tcs,cs,book_json_path,chapter)
            story.append(PageBreak())
            story.append(Paragraph(title, chapter_style))
            story.append(Paragraph(content, content_style))
        else:
            chapter[title] = ozj[title]
        pbar.update(1)

    utils.savejson(book_json_path, chapter)

    # 保存为 PDF 文件
    doc.build(story)

    return True
