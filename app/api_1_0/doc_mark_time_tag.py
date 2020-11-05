# -*- coding: UTF-8 -*-
import datetime
import uuid

from flask import jsonify, request
from . import api_doc_mark_time_tag as blue_print
from ..models import DocMarkTimeTag
from .. import db
from .utils import success_res, fail_res


@blue_print.route('/get_doc_mark_time_tag_by_doc_id', methods=['GET'])
def get_doc_mark_time_tag_by_doc_id():
    try:
        doc_mark_time_tag_doc_uuid = request.args.get('doc_uuid', '')
        doc_mark_time_tags = DocMarkTimeTag.query.filter_by(doc_uuid=doc_mark_time_tag_doc_uuid, valid=1).all()
        res = success_res(data=[{
            "uuid": doc_mark_time_tag.uuid,
            "doc_uuid": doc_mark_time_tag.doc_uuid,
            "word": doc_mark_time_tag.word,
            "format_date": doc_mark_time_tag.format_date.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_time_tag.format_date else None,
            "format_date_end": doc_mark_time_tag.format_date_end.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_time_tag.format_date_end else None,
            "mark_position": doc_mark_time_tag.mark_position,
            "time_type": doc_mark_time_tag.time_type,
            "reserve_fields": doc_mark_time_tag.reserve_fields,
            "arab_time": doc_mark_time_tag.arab_time,
            "update_by_uuid": doc_mark_time_tag.update_by_uuid,
            "update_time": doc_mark_time_tag.update_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_time_tag.update_time else None,
            "appear_index_in_text": doc_mark_time_tag.appear_index_in_text
        } for doc_mark_time_tag in doc_mark_time_tags])
    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


@blue_print.route('/get_one_doc_mark_time_tag_by_id', methods=['GET'])
def get_one_doc_mark_time_tag_by_id():
    try:
        doc_mark_time_tag_uuid = request.args.get('uuid', '')
        doc_mark_time_tag = DocMarkTimeTag.query.filter_by(uuid=doc_mark_time_tag_uuid, valid=1).first()
        res = {
            "uuid": doc_mark_time_tag.uuid,
            "doc_uuid": doc_mark_time_tag.doc_uuid,
            "word": doc_mark_time_tag.word,
            "format_date": doc_mark_time_tag.format_date.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_time_tag.format_date else None,
            "format_date_end": doc_mark_time_tag.format_date_end.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_time_tag.format_date_end else None,
            "mark_position": doc_mark_time_tag.mark_position,
            "time_type": doc_mark_time_tag.time_type,
            "reserve_fields": doc_mark_time_tag.reserve_fields,
            "arab_time": doc_mark_time_tag.arab_time,
            "update_by_uuid": doc_mark_time_tag.update_by_uuid,
            "update_time": doc_mark_time_tag.update_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_time_tag.update_time else None,
            "appear_index_in_text": doc_mark_time_tag.appear_index_in_text
        }
    except Exception as e:
        print(str(e))
        res = {
            "uuid": "-1",
            "doc_uuid": "",
            "word": "",
            "format_date": "",
            "format_date_end": "",
            "mark_position": "",
            "time_type": "",
            "reserve_fields": "",
            "arab_time": "",
            "update_by_uuid": "",
            "update_time": "",
            "appear_index_in_text": ""
        }
    return jsonify(res)


@blue_print.route('/get_one_doc_mark_time_tag_by_doc_id', methods=['GET'])
def get_one_doc_mark_time_tag_by_doc_id():
    try:
        doc_mark_time_tag_doc_uuid = request.args.get('doc_uuid', '')
        doc_mark_time_tag = DocMarkTimeTag.query.filter_by(doc_uuid=doc_mark_time_tag_doc_uuid, valid=1).first()
        res = {
            "uuid": doc_mark_time_tag.uuid,
            "doc_uuid": doc_mark_time_tag.doc_uuid,
            "word": doc_mark_time_tag.word,
            "format_date": doc_mark_time_tag.format_date,
            "format_date_end": doc_mark_time_tag.format_date_end,
            "mark_position": doc_mark_time_tag.mark_position,
            "time_type": doc_mark_time_tag.time_type,
            "reserve_fields": doc_mark_time_tag.reserve_fields,
            "arab_time": doc_mark_time_tag.arab_time,
            "update_by_uuid": doc_mark_time_tag.update_by_uuid,
            "update_time": doc_mark_time_tag.update_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_time_tag.update_time else None,
            "appear_index_in_text": doc_mark_time_tag.appear_index_in_text
        }
    except Exception as e:
        print(str(e))
        res = {
            "uuid": "-1",
            "doc_uuid": "",
            "word": "",
            "format_date": "",
            "format_date_end": "",
            "mark_position": "",
            "time_type": "",
            "reserve_fields": "",
            "arab_time": "",
            "update_by_uuid": "",
            "update_time": "",
            "appear_index_in_text": ""
        }
    return jsonify(res)


@blue_print.route('/add_doc_mark_time_tag', methods=['POST'])
def add_doc_mark_time_tag():
    try:
        doc_uuid = request.json.get('doc_uuid', '')
        word = request.json.get('word', '')
        format_date = request.json.get('format_date', None)
        format_date_end = request.json.get('format_date_end', None)
        mark_position = request.json.get('mark_position', '')
        time_type = request.json.get('time_type', 0)
        reserve_fields = request.json.get('reserve_fields', '')
        arab_time = request.json.get('arab_time', '')
        update_by_uuid = request.json.get('update_by_uuid', ''),
        appear_index_in_text = request.json.get('appear_index_in_text', [])
        doc_mark_time_tag = DocMarkTimeTag.query.filter_by(doc_uuid=doc_uuid, word=word,
                                                           format_date=format_date,
                                                           format_date_end=format_date_end,
                                                           mark_position=mark_position, time_type=time_type,
                                                           reserve_fields=reserve_fields, arab_time=arab_time,
                                                           update_by_uuid=update_by_uuid, appear_index_in_text=appear_index_in_text, valid=1).first()
        if doc_mark_time_tag:
            res = fail_res(msg="文档标记时间信息已存在!")
        else:
            docMarkTimeTag = DocMarkTimeTag(doc_uuid=doc_uuid, word=word, format_date=format_date,
                                            uuid=uuid.uuid1(),
                                            format_date_end=format_date_end,
                                            mark_position=mark_position, time_type=time_type,
                                            reserve_fields=reserve_fields,
                                            arab_time=arab_time, update_by_uuid=update_by_uuid,
                                            appear_index_in_text=appear_index_in_text,
                                            update_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), valid=1)
            db.session.add(docMarkTimeTag)
            db.session.commit()
            res = success_res(data={"uuid": docMarkTimeTag.uuid})
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/modify_doc_mark_time_tag', methods=['PUT'])
def modify_doc_mark_time_tag():
    try:
        uuid = request.json.get('uuid', '')
        doc_uuid = request.json.get('doc_uuid', '')
        word = request.json.get('word', '')
        format_date = request.json.get('format_date', None)
        format_date_end = request.json.get('format_date_end', None)
        mark_position = request.json.get('mark_position', '')
        time_type = request.json.get('time_type', '')
        reserve_fields = request.json.get('reserve_fields', '')
        arab_time = request.json.get('arab_time', '')
        update_by_uuid = request.json.get('update_by_uuid', '')
        appear_index_in_text = request.json.get('appear_index_in_text', [])
        doc_mark_time_tag = DocMarkTimeTag.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_time_tag:
            doc_mark_time_tag1 = DocMarkTimeTag.query.filter_by(doc_uuid=doc_uuid, word=word, format_date=format_date,
                                                                format_date_end=format_date_end,
                                                                mark_position=mark_position, time_type=time_type,
                                                                reserve_fields=reserve_fields, arab_time=arab_time,
                                                                update_by_uuid=update_by_uuid,
                                                                appear_index_in_text=appear_index_in_text,
                                                                valid=1).first()
            if doc_mark_time_tag1:
                res = fail_res(msg="文档标记时间信息已存在")
            else:
                if doc_uuid:
                    doc_mark_time_tag.doc_uuid = doc_uuid
                if word:
                    doc_mark_time_tag.word = word
                if format_date:
                    doc_mark_time_tag.type = format_date
                if format_date_end:
                    doc_mark_time_tag.format_date_end = format_date_end
                if mark_position:
                    doc_mark_time_tag.mark_position = mark_position
                if time_type:
                    doc_mark_time_tag.time_type = time_type
                if reserve_fields:
                    doc_mark_time_tag.reserve_fields = reserve_fields
                if arab_time:
                    doc_mark_time_tag.arab_time = arab_time
                if update_by_uuid:
                    doc_mark_time_tag.update_by_uuid = update_by_uuid
                if appear_index_in_text:
                    doc_mark_time_tag.appear_index_in_text = appear_index_in_text
                doc_mark_time_tag.update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db.session.commit()
                res = success_res()
        else:
            res = fail_res(msg="文档标记时间信息uuid不存在!")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="修改失败！")
    return jsonify(res)


@blue_print.route('/delete_doc_mark_time_tag', methods=['POST'])
def delete_doc_mark_time_tag():
    try:
        uuid = request.json.get('uuid', '')
        doc_mark_time_tag = DocMarkTimeTag.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_time_tag:
            doc_mark_time_tag.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="文档标记时间信息uuid不存在!")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)
