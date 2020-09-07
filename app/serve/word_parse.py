#!/c/Users/dell/Anaconda3/python
# _*_ coding: utf-8 _*_

import os
import re
import docx  # pip install python-docx on linux


def extract_word_content(path):
    """
    处理 word 文档
    """
    if path.endswith('docx'):
        doc = docx.Document(path)  # parse docx to Document
        content_paragraphs = []  # create paragraph list
        # add para to paragraphs
        for paragraph in doc.paragraphs:
            content_paragraphs.append(paragraph)
        # clean paragraph
        contents = []
        for para_idx, paragraph in enumerate(content_paragraphs):
            # 标题部分 paragraph.style.name: style 包含 Heading，Normal 等
            if paragraph.style.name.startswith('Heading'):
                title = paragraph.text
                title = re.sub("[\n\t\r]", "", title)  # 清除空格等

                # 根据格式信息获取标题内容
                if paragraph.style.name.startswith('Heading 1'):  # 一级标题
                    title = 'Heading 1:' + title
                elif paragraph.style.name.startswith('Heading 2'):  # 二级标题
                    title = 'Heading 2:' + title
                elif paragraph.style.name.startswith('Heading 3'):  # 三级标题
                    title = 'Heading 3:' + title
                else:
                    raise ValueError('标题最多为3级')  # TODO 支持多级

                contents.append(title)

            else:  # 正文部分
                para_text = paragraph.text
                para_text = re.sub("[\n\t\r]", "", para_text)  # 清除空格等
                if para_text == '' or para_text == None:
                    pass
                else:
                    contents.append(para_text)
        return contents
    else:
        print("File is not docx!!!")
        return None
