"""
Web 资源上传+处理逻辑
"""
import re
import string
import json
import os

import xlrd

from teaching_helper import gdata
from wx_client import models
from teaching_helper import glog

_logger = glog.get_logger(__name__)


def fetch_path_and_name(file_item):
    """获取文件路径和原生文件名
    :param file_item:
                    {
                      'file_url': xxxxxx,
                      'file_name': xxxxx,
                    }
    :return:
            file_path, file_name
    """
    _, file_path = re.split('\/group\d+\/', file_item['file_url'])
    return file_path, file_item['file_name']


def resolving_excel(file_path) -> list:
    """解析试卷excel

    :param file_path:  excel路径
    :return:

    [
        {
            'chapter': 章节
            'p_type': 类型
            'stem': 题干
            'score': 分值
            'difficult': 难度
            'related_knowledge': 关联知识点
            'analysis': 解析
            'answer': 答案
            'choices': 选项
        },
        ...
    ]
    """

    def __format_choices(choices: list) -> list:
        predefine_name = string.ascii_uppercase[:15]  # 选项范围 A->O
        return [{'key': i[1], 'content': i[0]}
                for i in zip(filter(lambda __c: __c != '', choices), predefine_name)]

    def __get_difficulty_level(difficult: str):
        if '简单' in difficult:
            return gdata.DIFFICULTY_SIMPLE
        if '一般' in difficult:
            return gdata.DIFFICULTY_MIDDLE
        if '困难' in difficult:
            return gdata.DIFFICULTY_COMPLEX
        return gdata.DIFFICULTY_UNKNOWN

    workbook = xlrd.open_workbook(file_path)
    worksheet = workbook.sheet_by_index(0)

    valid_row_len = 22
    result = list()
    for row_idx in range(1, worksheet.nrows):
        row_info = [str(worksheet.cell_value(row_idx, offset)) for offset in range(valid_row_len)]
        one_question = {
            'chapter': row_info[0],  # 章节
            'p_type': row_info[1],  # 类型
            'stem': row_info[2],  # 题干
            'score': int(row_info[3]) if row_info[3] else 0,  # 分值
            'difficult': __get_difficulty_level(row_info[4]),  # 难度
            'related_knowledge': re.split(r'[，,]', row_info[5]),  # 关联知识点
            'analysis': '无解析' if not row_info[6] else row_info[6],  # 解析
            'answer': row_info[7],  # 答案
            'choices': __format_choices(row_info[8:]),  # 选项
        }
        result.append(one_question)
    return result


class ResourceStorage(object):

    @staticmethod
    def flush_resource_2_db(resource_type, files_array, lesson_obj):
        for file_item in files_array:
            getattr(ResourceStorage, '_{}'.format(resource_type))(file_item, lesson_obj)

    @staticmethod
    def _exam(file_item: dict, lesson_obj):
        """试卷资源类型
        """
        file_path, f_name = fetch_path_and_name(file_item)
        exam_data = resolving_excel(os.path.join(gdata.BASE_RESOURCE_PATH, file_path))
        _logger.info('examination information: {}'.format(exam_data))

        # 试卷相关
        exam = models.Examination.objects.create(title=f_name, lesson=lesson_obj)

        # 题目相关
        for _q in exam_data:
            models.ExamQuestion.objects.create(examination=exam,
                                               content=_q['stem'],
                                               related_point=_q['related_knowledge'],
                                               related_section=_q['chapter'],
                                               difficulty=_q['difficult'],
                                               score=_q['score'],
                                               answer='{}|（{}）'.format(_q['answer'], _q['analysis']),
                                               questions=json.dumps(_q['choices']))

        # 生成课堂资源
        ext_info = {
            'resource_addr': None,
            'examination_id': exam.id  # 试卷id
        }
        models.LessonResource.objects.create(resource_type=gdata.RESOURCE_TYPE_EXAMINATION,
                                             remark='试卷资源，无备注',
                                             lesson=lesson_obj,
                                             visibility=False,
                                             ext_info=json.dumps(ext_info))

    @staticmethod
    def _normal(file_item: dict, lesson_obj):
        """普通资源类型

        普通资源类型又分为一下几种类型：
        1. 图片
        2. 文档
        3. 音频
        4. 视频
        5. 其他
        """
        f_url, f_name = file_item['file_url'], file_item['file_name']
        suffix = f_url.split('.')[-1]
        basic_ext_info = {'resource_addr': f_url, 'examination_id': None}

        resource_type = gdata.RESOURCE_TYPE_OTHER
        if suffix in gdata.IMAGES_FILES_SUFFIX:
            resource_type = gdata.RESOURCE_TYPE_IMG
        if suffix in gdata.DOCX_FILES_SUFFIX:
            resource_type = gdata.RESOURCE_TYPE_DOC
        if suffix in gdata.AUDIO_FILES_SUFFIX:
            resource_type = gdata.RESOURCE_TYPE_VOICE
        if suffix in gdata.VEDIO_FILES_SUFFIX:
            resource_type = gdata.RESOURCE_TYPE_VIDEO

        # 生成课堂资源
        models.LessonResource.objects.create(resource_type=resource_type,
                                             lesson=lesson_obj,
                                             visibility=False,
                                             ext_info=json.dumps(basic_ext_info))