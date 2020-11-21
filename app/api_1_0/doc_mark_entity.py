# -*- coding: UTF-8 -*-
from flask import jsonify, request
from sqlalchemy import or_, and_
from . import api_doc_mark_entity as blue_print
from ..models import DocMarkEntity, Entity
from .. import db
from .utils import success_res, fail_res
import time
import uuid

# doc_mark_entity表中删除了entity_type、entity_type_id字段，添加了appear_index_in_text字段

# 按id查询
@blue_print.route('/get_doc_mark_entity_by_id', methods=['GET'])
def get_doc_mark_entity_by_id():
    try:
        uuid = request.args.get("uuid", None)
        doc_mark_entity = DocMarkEntity.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_entity:
            res = success_res(data={
                "uuid": doc_mark_entity.uuid,
                "doc_uuid": doc_mark_entity.doc_uuid,
                "word": doc_mark_entity.word,
                "entity_uuid": doc_mark_entity.entity_uuid,
                "source": doc_mark_entity.source,
                "create_by_uuid": doc_mark_entity.create_by_uuid,
                "create_time": doc_mark_entity.create_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_entity.create_time else None,
                "update_by_uuid": doc_mark_entity.update_by_uuid,
                "update_time": doc_mark_entity.update_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_entity.update_time else None,
                "entity_type_uuid": Entity.get_category_id(doc_mark_entity.entity_uuid),
                "appear_index_in_text": doc_mark_entity.appear_index_in_text
            })
        else:
            res = fail_res(msg="实体数据不存在")

    except Exception as e:
        print(str(e))
        res = fail_res(data={
            "uuid": '',
            "doc_uuid": '',
            "word": "",
            "entity_uuid": '',
            "source": -1,
            "create_by_uuid": '',
            "create_time": None,
            "update_by_uuid": '',
            "update_time": None,
            "entity_type_uuid": '',
            "appear_index_in_text": []
        })

    return jsonify(res)


# 按doc_id查询
@blue_print.route('/get_doc_mark_entity_by_doc_id', methods=['GET'])
def get_doc_mark_entity_by_doc_id():
    try:
        doc_uuid = request.args.get("doc_uuid", None)
        doc_mark_entity_list = DocMarkEntity.query.filter_by(doc_uuid=doc_uuid, valid=1).all()

        res = success_res(data=[{
            "uuid": i.uuid,
            "doc_uuid": i.doc_uuid,
            "word": i.word,
            "entity_uuid": i.entity_uuid,
            "source": i.source,
            "create_by_uuid": i.create_by_uuid,
            "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S") if i.create_time else None,
            "update_by_uuid": i.create_by_uuid,
            "update_time": i.update_time.strftime("%Y-%m-%d %H:%M:%S") if i.update_time else None,
            "entity_type_uuid": Entity.get_category_id(i.entity_uuid),
            "appear_index_in_text": i.appear_index_in_text
        } for i in doc_mark_entity_list])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


# add
@blue_print.route('/add_doc_mark_entity', methods=['POST'])
def add_doc_mark_entity():
    try:
        doc_uuid = request.json.get("doc_uuid", None)
        word = request.json.get("word", "")
        entity_uuid = request.json.get("entity_uuid", None)
        source = request.json.get("source", 0)
        create_by_uuid = request.json.get("create_by_uuid", None)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_by_uuid = request.json.get("update_by_uuid", None)
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        appear_index_in_text = request.json.get("appear_index_in_text", [])

        doc_mark_entity_same = DocMarkEntity.query.filter_by(doc_uuid=doc_uuid, word=word,
                                                             entity_uuid=entity_uuid, valid=1).first()
        if doc_mark_entity_same:
            res = fail_res(msg="相同标注实体已存在")
        else:
            doc_mark_entity = DocMarkEntity(uuid=uuid.uuid1(),doc_uuid=doc_uuid, word=word, entity_uuid=entity_uuid, source=source,
                                            create_by_uuid=create_by_uuid, create_time=create_time,
                                            update_by_uuid=update_by_uuid, update_time=update_time,
                                            appear_index_in_text=appear_index_in_text,
                                            valid=1)
            db.session.add(doc_mark_entity)
            db.session.commit()
            res = success_res(data={"uuid": doc_mark_entity.uuid})

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# modify
@blue_print.route('/modify_doc_mark_entity', methods=['PUT'])
def modify_doc_mark_entity():
    try:
        uuid = request.json.get("uuid", None)
        doc_uuid = request.json.get("doc_uuid", None)
        word = request.json.get("word", "")
        entity_uuid = request.json.get("entity_uuid", None)
        source = request.json.get("source", 0)
        create_by_uuid = request.json.get("create_by_uuid", None)
        create_time = request.json.get("create_time", None)
        update_by_uuid = request.json.get("update_by_uuid", None)
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        appear_index_in_text = request.json.get("appear_index_in_text", [])

        doc_mark_entity_same = DocMarkEntity.query.filter_by(doc_uuid=doc_uuid, word=word,
                                                             entity_uuid=entity_uuid, valid=1).first()
        if doc_mark_entity_same:
            res = fail_res(msg="相同标注实体已存在")
        else:
            doc_mark_entity = DocMarkEntity.query.filter_by(uuid=uuid, valid=1).first()
            if doc_mark_entity:
                if doc_uuid:
                    doc_mark_entity.doc_uuid = doc_uuid
                if word:
                    doc_mark_entity.word = word
                if entity_uuid:
                    doc_mark_entity.entity_uuid = entity_uuid
                if source:
                    doc_mark_entity.source = source
                if create_by_uuid:
                    doc_mark_entity.create_by_uuid = create_by_uuid
                if create_time:
                    doc_mark_entity.create_time = create_time
                if update_by_uuid:
                    doc_mark_entity.update_by_uuid = update_by_uuid
                if update_time:
                    doc_mark_entity.update_time = update_time
                if appear_index_in_text:
                    doc_mark_entity.appear_index_in_text = appear_index_in_text
                db.session.commit()
                res = success_res()
            else:
                res = fail_res(msg="实体数据不存在")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


# delete
@blue_print.route('/delete_doc_mark_entity_by_id', methods=['POST'])
def delete_doc_mark_entity_by_id():
    try:
        uuid = request.json.get("uuid", None)
        doc_mark_entity = DocMarkEntity.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_entity:
            doc_mark_entity.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="实体数据不存在")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


#根据标注词和doc_uuid获取是否被标注
@blue_print.route('/get_doc_mark_entity_by_word_and_doc_id', methods=['GET'])
def get_doc_mark_entity_by_word_and_doc_id():
    try:
        doc_mark_entity_doc_uuid = request.args.get('doc_uuid', None)
        doc_mark_entity_word = request.args.get('word', '')
        doc_mark_entity = DocMarkEntity.query.filter_by(doc_uuid=doc_mark_entity_doc_uuid,
                                                       word=doc_mark_entity_word, valid=1).first()
        if doc_mark_entity:
            res = success_res(data={"flag": 1})
        else:
            res = fail_res(data={"flag": 0}, msg="标注实体信息不存在！")

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


# 按doc_id和entity_id查询
@blue_print.route('/get_doc_mark_entity_by_doc_id_and_entity_id', methods=['GET'])
def get_doc_mark_entity_by_doc_id_and_entity_id():
    try:
        doc_uuid = request.args.get("doc_uuid", None)
        entity_uuid = request.args.get("entity_uuid", None)
        doc_mark_entity_list = DocMarkEntity.query.filter_by(doc_uuid=doc_uuid, entity_uuid=entity_uuid, valid=1).all()

        res = success_res(data=[{
            "uuid": i.uuid,
            "doc_uuid": i.doc_uuid,
            "word": i.word,
            "entity_uuid": i.entity_uuid,
            "source": i.source,
            "create_by_uuid": i.create_by_uuid,
            "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S") if i.create_time else None,
            "update_by_uuid": i.create_by_uuid,
            "update_time": i.update_time.strftime("%Y-%m-%d %H:%M:%S") if i.update_time else None,
            "entity_type_uuid": Entity.get_category_id(i.entity_uuid),
            "appear_index_in_text": i.appear_index_in_text
        } for i in doc_mark_entity_list])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)