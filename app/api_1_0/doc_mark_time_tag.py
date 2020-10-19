# -*- coding: UTF-8 -*-
import datetime
from flask import jsonify, request
from . import api_doc_mark_time_tag as blue_print
from ..models import DocMarkTimeTag
from .. import db
from .utils import success_res, fail_res


@blue_print.route('/get_doc_mark_time_tag_by_doc_id', methods=['GET'])
def get_doc_mark_time_tag_by_doc_id():
    try:
        doc_mark_time_tag_doc_id = request.args.get('doc_id', 0, type=int)
        if isinstance(doc_mark_time_tag_doc_id, int):
            doc_mark_time_tags = DocMarkTimeTag.query.filter_by(doc_id=doc_mark_time_tag_doc_id, valid=1).all()
            res = success_res(data=[{
                "id": doc_mark_time_tag.id,
                "doc_id": doc_mark_time_tag.doc_id,
                "word": doc_mark_time_tag.word,
                "format_date": doc_mark_time_tag.format_date,
                "format_date_end": doc_mark_time_tag.format_date_end,
                "mark_position": doc_mark_time_tag.mark_position,
                "time_type": doc_mark_time_tag.time_type,
                "reserve_fields": doc_mark_time_tag.reserve_fields,
                "arab_time": doc_mark_time_tag.arab_time,
                "update_by": doc_mark_time_tag.update_by,
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
        doc_mark_time_tag_id = request.args.get('id', 0, type=int)
        if isinstance(doc_mark_time_tag_id, int):
            doc_mark_time_tag = DocMarkTimeTag.query.filter_by(id=doc_mark_time_tag_id, valid=1).first()
            res = {
                "id": doc_mark_time_tag.id,
                "doc_id": doc_mark_time_tag.doc_id,
                "word":doc_mark_time_tag.word,
                "format_date":doc_mark_time_tag.format_date,
                "format_date_end":doc_mark_time_tag.format_date_end,
                "mark_position":doc_mark_time_tag.mark_position,
                "time_type":doc_mark_time_tag.time_type,
                "reserve_fields":doc_mark_time_tag.reserve_fields,
                "arab_time":doc_mark_time_tag.arab_time,
                "update_by":doc_mark_time_tag.update_by,
                "update_time":doc_mark_time_tag.update_time.strftime('%Y-%m-%d %H:%M:%S') if doc_mark_time_tag.update_time else None,
                "appear_index_in_text":doc_mark_time_tag.appear_index_in_text
            }
    except Exception as e:
        print(str(e))
        res = {
            "id": -1,
            "doc_id": "",
            "word":"",
            "format_date":"",
            "format_date_end":"",
            "mark_position":"",
            "time_type":"",
            "reserve_fields":"",
            "arab_time":"",
            "update_by":"",
            "update_time":"",
            "appear_index_in_text":""
        }
    return jsonify(res)

@blue_print.route('/get_one_doc_mark_time_tag_by_doc_id', methods=['GET'])
def get_one_doc_mark_time_tag_by_doc_id():
    try:
        doc_mark_time_tag_doc_id = request.args.get('doc_id', 0 , type=int)
        if isinstance(doc_mark_time_tag_doc_id, int):
            doc_mark_time_tag = DocMarkTimeTag.query.filter_by(doc_id=doc_mark_time_tag_doc_id, valid=1).first()
            res = {
                "id": doc_mark_time_tag.id,
                "doc_id": doc_mark_time_tag.doc_id,
                "word": doc_mark_time_tag.word,
                "format_date": doc_mark_time_tag.format_date,
                "format_date_end": doc_mark_time_tag.format_date_end,
                "mark_position": doc_mark_time_tag.mark_position,
                "time_type": doc_mark_time_tag.time_type,
                "reserve_fields": doc_mark_time_tag.reserve_fields,
                "arab_time": doc_mark_time_tag.arab_time,
                "update_by": doc_mark_time_tag.update_by,
                "update_time": doc_mark_time_tag.update_time.strftime('%Y-%m-%d %H:%M:%S') if doc_mark_time_tag.update_time else None,
                "appear_index_in_text": doc_mark_time_tag.appear_index_in_text
            }
    except Exception as e:
        print(str(e))
        res = {
            "id": -1,
            "doc_id": "",
            "word": "",
            "format_date": "",
            "format_date_end": "",
            "mark_position": "",
            "time_type": "",
            "reserve_fields": "",
            "arab_time": "",
            "update_by": "",
            "update_time": "",
            "appear_index_in_text":""
        }
    return jsonify(res)


@blue_print.route('/add_doc_mark_time_tag', methods=['POST'])
def add_doc_mark_time_tag():
    try:
        doc_id = request.json.get('doc_id',0)
        word = request.json.get('word', '')
        format_date = request.json.get('format_date', None)
        format_date_end = request.json.get('format_date_end', None)
        mark_position = request.json.get('mark_position', '')
        time_type = request.json.get('time_type', '')
        reserve_fields = request.json.get('reserve_fields', '')
        arab_time = request.json.get('arab_time', '')
        update_by = request.json.get('update_by', 0),
        appear_index_in_text = request.json.get('appear_index_in_text',[])
        doc_mark_time_tag = DocMarkTimeTag.query.filter_by(doc_id=doc_id, word=word,format_date=format_date,format_date_end=format_date_end,
                                                           mark_position=mark_position,time_type=time_type, reserve_fields=reserve_fields, arab_time=arab_time,
                                                           update_by=update_by,appear_index_in_text=appear_index_in_text,valid=1).first()
        if doc_mark_time_tag:
            res = fail_res(msg="文档标记时间信息已存在!")
        else:
            docMarkTimeTag = DocMarkTimeTag(doc_id=doc_id, word=word,format_date=format_date,format_date_end=format_date_end,
                                            mark_position=mark_position,time_type=time_type, reserve_fields=reserve_fields,
                                            arab_time=arab_time,update_by=update_by,appear_index_in_text=appear_index_in_text,
                                            update_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),valid=1)
            db.session.add(docMarkTimeTag)
            db.session.commit()
            res = success_res(data={"id": docMarkTimeTag.id})
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)

@blue_print.route('/modify_doc_mark_time_tag', methods=['PUT'])
def modify_doc_mark_time_tag():
    try:
        id = request.json.get('id', 0)
        doc_id = request.json.get('doc_id', 0)
        word = request.json.get('word', '')
        format_date = request.json.get('format_date', None)
        format_date_end = request.json.get('format_date_end', None)
        mark_position = request.json.get('mark_position', '')
        time_type = request.json.get('time_type', '')
        reserve_fields = request.json.get('reserve_fields', '')
        arab_time = request.json.get('arab_time', '')
        update_by = request.json.get('update_by', 0)
        appear_index_in_text = request.json.get('appear_index_in_text', [])
        doc_mark_time_tag = DocMarkTimeTag.query.filter_by(id=id, valid=1).first()
        if doc_mark_time_tag:
            doc_mark_time_tag1 = DocMarkTimeTag.query.filter_by(doc_id=doc_id, word=word, format_date=format_date,
                                                               format_date_end=format_date_end,
                                                               mark_position=mark_position, time_type=time_type,
                                                               reserve_fields=reserve_fields, arab_time=arab_time,
                                                               update_by=update_by, appear_index_in_text=appear_index_in_text,
                                                                valid=1).first()
            if doc_mark_time_tag1:
                res = fail_res(msg="文档标记时间信息已存在")
            else:
                if doc_id:
                    doc_mark_time_tag.doc_id = doc_id
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
                if update_by:
                    doc_mark_time_tag.update_by = update_by
                if appear_index_in_text:
                    doc_mark_time_tag.appear_index_in_text = appear_index_in_text
                doc_mark_time_tag.update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db.session.commit()
                res = success_res()
        else:
            res = fail_res(msg="文档标记时间信息id不存在!")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="修改失败！")
    return jsonify(res)

@blue_print.route('/delete_doc_mark_time_tag', methods=['POST'])
def delete_doc_mark_time_tag():
    try:
        id = request.json.get('id',0)
        doc_mark_time_tag = DocMarkTimeTag.query.filter_by(id=id, valid=1).first()
        if doc_mark_time_tag:
            doc_mark_time_tag.valid = 0
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)

