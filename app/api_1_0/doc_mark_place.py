# -*- coding: UTF-8 -*-
import datetime
import time
import uuid

from flask import jsonify, request

from . import api_doc_mark_place as blue_print
from .utils import success_res, fail_res
from .. import db
from ..models import DocMarkPlace, Entity


@blue_print.route('/get_doc_mark_place_by_doc_id', methods=['GET'])
def get_doc_mark_place_by_doc_id():
    try:
        doc_mark_place_doc_uuid = request.args.get('doc_uuid', None)
        doc_mark_places = DocMarkPlace.query.filter_by(doc_uuid=doc_mark_place_doc_uuid, valid=1).all()
        res = success_res(data=[{
            "uuid": doc_mark_place.uuid,
            "doc_uuid": doc_mark_place.doc_uuid,
            "word": doc_mark_place.word,
            "type": doc_mark_place.type,
            "place_uuid": doc_mark_place.place_uuid,
            "direction": doc_mark_place.direction,
            "place_lon": doc_mark_place.place_lon,
            "place_lat": doc_mark_place.place_lat,
            "height": doc_mark_place.height,
            "unit": doc_mark_place.unit,
            "dms": doc_mark_place.dms,
            "distance": doc_mark_place.distance,
            "relation": doc_mark_place.relation,
            "create_by_uuid": doc_mark_place.create_by_uuid,
            "create_time": doc_mark_place.create_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.create_time else None,
            "update_by_uuid": doc_mark_place.update_by_uuid,
            "update_time": doc_mark_place.update_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.update_time else None,
            "valid": doc_mark_place.valid,
            "entity_or_sys": doc_mark_place.entity_or_sys,
            "appear_index_in_text": doc_mark_place.appear_index_in_text,
            "word_count": doc_mark_place.word_count,
            "word_sentence": doc_mark_place.word_sentence,
            "source_type": doc_mark_place.source_type,
            "place_name": Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid,
                                              Entity.valid == 1).first().name
            if Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid, Entity.valid == 1).first() else ""
        } for doc_mark_place in doc_mark_places])
    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


@blue_print.route('/get_one_doc_mark_place_by_id', methods=['GET'])
def get_one_doc_mark_place_by_id():
    try:
        doc_mark_place_uuid = request.args.get('uuid', None)
        doc_mark_place = DocMarkPlace.query.filter_by(uuid=doc_mark_place_uuid, valid=1).first()
        if doc_mark_place:
            res = {
            "uuid": doc_mark_place.uuid,
            "doc_uuid": doc_mark_place.doc_uuid,
            "word": doc_mark_place.word,
            "type": doc_mark_place.type,
            "place_uuid": doc_mark_place.place_uuid,
            "direction": doc_mark_place.direction,
            "place_lon": doc_mark_place.place_lon,
            "place_lat": doc_mark_place.place_lat,
            "height": doc_mark_place.height,
            "unit": doc_mark_place.unit,
            "dms": doc_mark_place.dms,
            "distance": doc_mark_place.distance,
            "relation": doc_mark_place.relation,
            "create_by_uuid": doc_mark_place.create_by_uuid,
            "create_time": doc_mark_place.create_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_place.create_time else None,
            "update_by_uuid": doc_mark_place.update_by_uuid,
            "update_time": doc_mark_place.update_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_place.update_time else None,
            "valid": doc_mark_place.valid,
            "entity_or_sys": doc_mark_place.entity_or_sys,
            "appear_index_in_text": doc_mark_place.appear_index_in_text,
            "word_count": doc_mark_place.word_count,
            "word_sentence": doc_mark_place.word_sentence,
            "source_type": doc_mark_place.source_type,
            "place_name": Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid,
                                              Entity.valid == 1).first().name
            if Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid, Entity.valid == 1).first() else ""
        }
        else:
            res = fail_res(msg="地点信息不存在")
    except Exception as e:
        print(str(e))
        res = {
            "uuid": '',
            "doc_uuid": "",
            "word": "",
            "type": "",
            "place_uuid": "",
            "direction": "",
            "place_lon": "",
            "place_lat": "",
            "height": "",
            "unit": "",
            "dms": "",
            "distance": 0.0,
            "relation": "",
            "create_by_uuid": "",
            "create_time": None,
            "update_by_uuid": "",
            "update_time": None,
            "valid": -1,
            "entity_or_sys": -1,
            "appear_index_in_text": -1,
            "word_count": "",
            "word_sentence": "",
            "source_type": "",
            "place_name": ""
        }
    return jsonify(res)


@blue_print.route('/get_one_doc_mark_place_by_doc_id', methods=['GET'])
def get_one_doc_mark_place_by_doc_id():
    try:
        doc_mark_place_doc_uuid = request.args.get('doc_uuid', None)
        doc_mark_place = DocMarkPlace.query.filter_by(doc_uuid=doc_mark_place_doc_uuid, valid=1).first()
        if doc_mark_place:
            res = {
                "uuid": doc_mark_place.uuid,
                "doc_uuid": doc_mark_place.doc_uuid,
                "word": doc_mark_place.word,
                "type": doc_mark_place.type,
                "place_uuid": doc_mark_place.place_uuid,
                "direction": doc_mark_place.direction,
                "place_lon": doc_mark_place.place_lon,
                "place_lat": doc_mark_place.place_lat,
                "height": doc_mark_place.height,
                "unit": doc_mark_place.unit,
                "dms": doc_mark_place.dms,
                "distance": doc_mark_place.distance,
                "relation": doc_mark_place.relation,
                "create_by_uuid": doc_mark_place.create_by_uuid,
                "create_time": doc_mark_place.create_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_place.create_time else None,
                "update_by_uuid": doc_mark_place.update_by_uuid,
                "update_time": doc_mark_place.update_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_place.update_time else None,
                "valid": doc_mark_place.valid,
                "entity_or_sys": doc_mark_place.entity_or_sys,
                "appear_index_in_text": doc_mark_place.appear_index_in_text,
                "word_count": doc_mark_place.word_count,
                "word_sentence": doc_mark_place.word_sentence,
                "source_type": doc_mark_place.source_type,
                "place_name": Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid,
                                                  Entity.valid == 1).first().name
                if Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid, Entity.valid == 1).first() else ""
            }
        else:
            res = fail_res(msg="地点信息不存在")
    except Exception as e:
        print(str(e))
        res = {
            "uuid": "",
            "doc_uuid": "",
            "word": "",
            "type": "",
            "place_uuid": "",
            "direction": "",
            "place_lon": "",
            "place_lat": "",
            "height": "",
            "unit": "",
            "dms": "",
            "distance": 0.0,
            "relation": "",
            "create_by_uuid": "",
            "create_time": None,
            "update_by_uuid": "",
            "update_time": None,
            "valid": -1,
            "entity_or_sys": -1,
            "appear_index_in_text": [],
            "word_count": "",
            "word_sentence": "",
            "source_type": "",
            "place_name": ""
        }
    return jsonify(res)


@blue_print.route('/add_doc_mark_place', methods=['POST'])
def add_doc_mark_place():
    try:
        doc_uuid = request.json.get('doc_uuid', None)
        word = request.json.get('word', '')
        type = request.json.get('type', 0)
        place_uuid = request.json.get('place_uuid', None)
        direction = request.json.get('direction', '')
        place_lon = request.json.get('place_lon', '')
        place_lat = request.json.get('place_lat', '')
        height = request.json.get('height', '')
        unit = request.json.get('unit', '')
        dms = request.json.get('dms', [])
        distance = request.json.get('distance', 0.0)
        relation = request.json.get('relation', '')
        create_by_uuid = request.json.get('create_by_uuid', None)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_by_uuid = request.json.get("update_by_uuid", None)
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        entity_or_sys = request.json.get('entity_or_sys', 0)
        appear_index_in_text = request.json.get('appear_index_in_text', [])
        word_count = request.json.get('word_count', '')
        word_sentence = request.json.get('word_sentence', '')
        source_type = request.json.get('source_type', 0)
        if not isinstance(dms, list):
            res = fail_res(msg="dms参数格式错误!")
        if not isinstance(appear_index_in_text, list):
            res = fail_res(msg="appear_index_in_text参数格式错误!")
        else:
            doc_mark_place = DocMarkPlace.query.filter_by(doc_uuid=doc_uuid, word=word, type=type,
                                                          place_uuid=place_uuid,
                                                          direction=direction, place_lon=place_lon, place_lat=place_lat,
                                                          height=height, unit=unit, dms=dms, distance=distance,
                                                          relation=relation, create_by_uuid=create_by_uuid,
                                                          create_time=create_time,
                                                          update_by_uuid=update_by_uuid, update_time=update_time,
                                                          entity_or_sys=entity_or_sys,
                                                          appear_index_in_text=appear_index_in_text,
                                                          word_count=word_count, word_sentence=word_sentence,
                                                          source_type=source_type, valid=1).first()
            if doc_mark_place:
                res = fail_res(msg="文档标记地点已存在!")
            else:
                docMarkPlace = DocMarkPlace(uuid=uuid.uuid1(), doc_uuid=doc_uuid, word=word, type=type,
                                            place_uuid=place_uuid,
                                            direction=direction, place_lon=place_lon, place_lat=place_lat,
                                            height=height,
                                            unit=unit, dms=dms, distance=distance, relation=relation,
                                            create_by_uuid=create_by_uuid, create_time=create_time,
                                            update_by_uuid=update_by_uuid, update_time=update_time,
                                            appear_index_in_text=appear_index_in_text,
                                            entity_or_sys=entity_or_sys, word_count=word_count,
                                            word_sentence=word_sentence,
                                            source_type=source_type, valid=1)
                db.session.add(docMarkPlace)
                db.session.commit()
                res = success_res(data={"uuid": docMarkPlace.uuid})
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/modify_doc_mark_place', methods=['PUT'])
def modify_doc_mark_place():
    try:
        uuid = request.json.get('uuid', None)
        doc_uuid = request.json.get('doc_uuid', None)
        word = request.json.get('word', '')
        type = request.json.get('type', 0)
        place_uuid = request.json.get('place_uuid', None)
        direction = request.json.get('direction', '')
        place_lon = request.json.get('place_lon', '')
        place_lat = request.json.get('place_lat', '')
        height = request.json.get('height', '')
        unit = request.json.get('unit', '')
        dms = request.json.get('dms', [])
        distance = request.json.get('distance', 0.0)
        relation = request.json.get('relation', '')
        update_by_uuid = request.json.get('update_by_uuid', None)  # 更新修改者
        entity_or_sys = request.json.get('entity_or_sys', 0)
        create_by_uuid = request.json.get('create_by_uuid', None)
        create_time = request.json.get('create_time', None)
        appear_index_in_text = request.json.get('appear_index_in_text', [])
        word_count = request.json.get('word_count', '')
        word_sentence = request.json.get('word_sentence', '')
        source_type = request.json.get('source_type', 0)

        if not isinstance(dms, list):
            res = fail_res(msg="dms参数格式错误!")
        if not isinstance(appear_index_in_text, list):
            res = fail_res(msg="appear_index_in_text参数格式错误!")
        else:
            doc_mark_place = DocMarkPlace.query.filter_by(uuid=uuid, valid=1).first()
            if doc_mark_place:
                doc_mark_place_same = DocMarkPlace.query.filter_by(doc_uuid=doc_uuid, word=word, type=type,
                                                               place_uuid=place_uuid,
                                                               direction=direction, place_lon=place_lon,
                                                               place_lat=place_lat, height=height,
                                                               unit=unit, dms=dms, distance=distance, relation=relation,
                                                               create_by_uuid=create_by_uuid,
                                                               entity_or_sys=entity_or_sys,
                                                               appear_index_in_text=appear_index_in_text,
                                                               word_count=word_count, word_sentence=word_sentence,
                                                               source_type=source_type,
                                                               valid=1).first()
                if doc_mark_place_same:
                    res = fail_res(msg="文档标记地点已存在")
                else:
                    if doc_uuid:
                        doc_mark_place.doc_id = doc_uuid
                    if word:
                        doc_mark_place.word = word
                    if type:
                        doc_mark_place.type = type
                    if place_uuid:
                        doc_mark_place.place_id = place_uuid
                    if direction:
                        doc_mark_place.direction = direction
                    if place_lon:
                        doc_mark_place.place_lon = place_lon
                    if place_lat:
                        doc_mark_place.place_lat = place_lat
                    if height:
                        doc_mark_place.height = height
                    if unit:
                        doc_mark_place.unit = unit
                    if dms:
                        doc_mark_place.dms = dms
                    if distance:
                        doc_mark_place.distance = distance
                    if relation:
                        doc_mark_place.relation = relation
                    if create_by_uuid:
                        doc_mark_place.create_by_uuid = create_by_uuid
                    if create_time:
                        doc_mark_place.create_time = create_time
                    if update_by_uuid:
                        doc_mark_place.update_by_uuid = update_by_uuid
                    # if update_time:
                    doc_mark_place.update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if entity_or_sys:
                        doc_mark_place.entity_or_sys = entity_or_sys
                    if appear_index_in_text:
                        doc_mark_place.appear_index_in_text = appear_index_in_text
                    if word_count:
                        doc_mark_place.word_count = word_count
                    if word_sentence:
                        doc_mark_place.word_sentence = word_sentence
                    if source_type:
                        doc_mark_place.source_type = source_type
                    db.session.commit()
                    res = success_res()
            else:
                res = fail_res(msg="文档标记地点id不存在!")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="修改失败！")
    return jsonify(res)


@blue_print.route('/delete_doc_mark_place', methods=['POST'])
def delete_doc_mark_place():
    try:
        uuid = request.json.get('uuid', None)
        doc_mark_place = DocMarkPlace.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_place:
            doc_mark_place.valid = 0
            db.session.commit()
            res = success_res()
        else:
            res = fail_res(msg="文档标记地点id不存在!")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


#根据标注词获取地点信息
@blue_print.route('/get_doc_mark_place_by_word', methods=['GET'])
def get_doc_mark_place_by_word():
    try:
        doc_mark_place_doc_uuid = request.args.get('doc_uuid', None)
        doc_mark_place_word = request.args.get('word', '')
        doc_mark_place = DocMarkPlace.query.filter_by(doc_uuid=doc_mark_place_doc_uuid,
                                                       word=doc_mark_place_word, valid=1).first()
        if doc_mark_place:
            res = success_res(data={
                "uuid": doc_mark_place.uuid,
                "doc_uuid": doc_mark_place.doc_uuid,
                "word": doc_mark_place.word,
                "type": doc_mark_place.type,
                "place_uuid": doc_mark_place.place_uuid,
                "direction": doc_mark_place.direction,
                "place_lon": doc_mark_place.place_lon,
                "place_lat": doc_mark_place.place_lat,
                "height": doc_mark_place.height,
                "unit": doc_mark_place.unit,
                "dms": doc_mark_place.dms,
                "distance": doc_mark_place.distance,
                "relation": doc_mark_place.relation,
                "create_by_uuid": doc_mark_place.create_by_uuid,
                "create_time": doc_mark_place.create_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_place.create_time else None,
                "update_by_uuid": doc_mark_place.update_by_uuid,
                "update_time": doc_mark_place.update_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_place.update_time else None,
                "valid": doc_mark_place.valid,
                "entity_or_sys": doc_mark_place.entity_or_sys,
                "appear_index_in_text": doc_mark_place.appear_index_in_text,
                "word_count": doc_mark_place.word_count,
                "word_sentence": doc_mark_place.word_sentence,
                "source_type": doc_mark_place.source_type,
                "place_name": Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid,
                                                  Entity.valid == 1).first().name
                if Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid, Entity.valid == 1).first() else ""
            })
        else:
            res = fail_res(msg="地点信息不存在！")

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


#根据文章标识和地点标识获取地点标注记录
@blue_print.route('/get_doc_mark_place', methods=['GET'])
def get_doc_mark_place():
    try:
        doc_mark_place_doc_uuid = request.args.get('doc_uuid', None)
        doc_mark_place_place_uuid= request.args.get('place_uuid', None)
        doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=doc_mark_place_place_uuid, doc_uuid=doc_mark_place_doc_uuid, valid=1).all()

        res = success_res(data=[{
            "uuid": doc_mark_place.uuid,
            "doc_uuid": doc_mark_place.doc_uuid,
            "word": doc_mark_place.word,
            "type": doc_mark_place.type,
            "place_uuid": doc_mark_place.place_uuid,
            "direction": doc_mark_place.direction,
            "place_lon": doc_mark_place.place_lon,
            "place_lat": doc_mark_place.place_lat,
            "height": doc_mark_place.height,
            "unit": doc_mark_place.unit,
            "dms": doc_mark_place.dms,
            "distance": doc_mark_place.distance,
            "relation": doc_mark_place.relation,
            "create_by_uuid": doc_mark_place.create_by_uuid,
            "create_time": doc_mark_place.create_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.create_time else None,
            "update_by_uuid": doc_mark_place.update_by_uuid,
            "update_time": doc_mark_place.update_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.update_time else None,
            "valid": doc_mark_place.valid,
            "entity_or_sys": doc_mark_place.entity_or_sys,
            "appear_index_in_text": doc_mark_place.appear_index_in_text,
            "word_count": doc_mark_place.word_count,
            "word_sentence": doc_mark_place.word_sentence,
            "source_type": doc_mark_place.source_type,
            "place_name": Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid,
                                              Entity.valid == 1).first().name
            if Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid, Entity.valid == 1).first() else ""
        } for doc_mark_place in doc_mark_places])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


#根据文档标识和地点类型获取地点词信息
@blue_print.route('/get_doc_mark_place_by_types', methods=['POST'])
def get_doc_mark_place_by_types():
    try:
        doc_mark_place_doc_uuid = request.json.get('doc_uuid', None)
        doc_mark_place_types = request.json.get('types', [])
        doc_mark_places = db.session.query(DocMarkPlace).filter(
            DocMarkPlace.type.in_(doc_mark_place_types),
            DocMarkPlace.doc_uuid == doc_mark_place_doc_uuid,
            DocMarkPlace.valid == 1).all()

        res = success_res(data=[{
            "uuid": doc_mark_place.uuid,
            "doc_uuid": doc_mark_place.doc_uuid,
            "word": doc_mark_place.word,
            "type": doc_mark_place.type,
            "place_uuid": doc_mark_place.place_uuid,
            "direction": doc_mark_place.direction,
            "place_lon": doc_mark_place.place_lon,
            "place_lat": doc_mark_place.place_lat,
            "height": doc_mark_place.height,
            "unit": doc_mark_place.unit,
            "dms": doc_mark_place.dms,
            "distance": doc_mark_place.distance,
            "relation": doc_mark_place.relation,
            "create_by_uuid": doc_mark_place.create_by_uuid,
            "create_time": doc_mark_place.create_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.create_time else None,
            "update_by_uuid": doc_mark_place.update_by_uuid,
            "update_time": doc_mark_place.update_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.update_time else None,
            "valid": doc_mark_place.valid,
            "entity_or_sys": doc_mark_place.entity_or_sys,
            "appear_index_in_text": doc_mark_place.appear_index_in_text,
            "word_count": doc_mark_place.word_count,
            "word_sentence": doc_mark_place.word_sentence,
            "source_type": doc_mark_place.source_type,
            "place_name": Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid,
                                              Entity.valid == 1).first().name
            if Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid, Entity.valid == 1).first() else ""
        } for doc_mark_place in doc_mark_places])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


#根据标注记录标识查询地点标注信息
@blue_print.route('/get_doc_mark_place_by_ids', methods=['POST'])
def get_doc_mark_place_by_ids():
    try:
        doc_mark_place_uuids = request.json.get('ids', [])
        doc_mark_places = db.session.query(DocMarkPlace).filter(
            DocMarkPlace.uuid.in_(doc_mark_place_uuids), DocMarkPlace.valid == 1).all()

        res = success_res(data=[{
            "uuid": doc_mark_place.uuid,
            "doc_uuid": doc_mark_place.doc_uuid,
            "word": doc_mark_place.word,
            "type": doc_mark_place.type,
            "place_uuid": doc_mark_place.place_uuid,
            "direction": doc_mark_place.direction,
            "place_lon": doc_mark_place.place_lon,
            "place_lat": doc_mark_place.place_lat,
            "height": doc_mark_place.height,
            "unit": doc_mark_place.unit,
            "dms": doc_mark_place.dms,
            "distance": doc_mark_place.distance,
            "relation": doc_mark_place.relation,
            "create_by_uuid": doc_mark_place.create_by_uuid,
            "create_time": doc_mark_place.create_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.create_time else None,
            "update_by_uuid": doc_mark_place.update_by_uuid,
            "update_time": doc_mark_place.update_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.update_time else None,
            "valid": doc_mark_place.valid,
            "entity_or_sys": doc_mark_place.entity_or_sys,
            "appear_index_in_text": doc_mark_place.appear_index_in_text,
            "word_count": doc_mark_place.word_count,
            "word_sentence": doc_mark_place.word_sentence,
            "source_type": doc_mark_place.source_type,
            "place_name": Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid,
                                              Entity.valid == 1).first().name
            if Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid, Entity.valid == 1).first() else ""
        } for doc_mark_place in doc_mark_places])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


#查询地点标注所有未删除的记录
@blue_print.route('/get_doc_mark_place_all', methods=['GET'])
def get_doc_mark_place_all():
    try:
        doc_mark_places = DocMarkPlace.query.filter_by(valid=1).all()

        res = success_res(data=[{
            "uuid": doc_mark_place.uuid,
            "doc_uuid": doc_mark_place.doc_uuid,
            "word": doc_mark_place.word,
            "type": doc_mark_place.type,
            "place_uuid": doc_mark_place.place_uuid,
            "direction": doc_mark_place.direction,
            "place_lon": doc_mark_place.place_lon,
            "place_lat": doc_mark_place.place_lat,
            "height": doc_mark_place.height,
            "unit": doc_mark_place.unit,
            "dms": doc_mark_place.dms,
            "distance": doc_mark_place.distance,
            "relation": doc_mark_place.relation,
            "create_by_uuid": doc_mark_place.create_by_uuid,
            "create_time": doc_mark_place.create_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.create_time else None,
            "update_by_uuid": doc_mark_place.update_by_uuid,
            "update_time": doc_mark_place.update_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.update_time else None,
            "valid": doc_mark_place.valid,
            "entity_or_sys": doc_mark_place.entity_or_sys,
            "appear_index_in_text": doc_mark_place.appear_index_in_text,
            "word_count": doc_mark_place.word_count,
            "word_sentence": doc_mark_place.word_sentence,
            "source_type": doc_mark_place.source_type,
            "place_name": Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid,
                                              Entity.valid == 1).first().name
            if Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid, Entity.valid == 1).first() else ""
        } for doc_mark_place in doc_mark_places])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


#根据文档标识删除地点标注记录
@blue_print.route('/delete_doc_mark_place_by_doc_id', methods=['POST'])
def delete_doc_mark_place_by_doc_id():
    try:
        doc_uuid = request.json.get('doc_uuid', None)
        doc_mark_places = DocMarkPlace.query.filter_by(doc_uuid=doc_uuid, valid=1).all()

        for doc_mark_place in doc_mark_places:
            doc_mark_place.valid = 0
            db.session.commit()
            res = success_res()

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


#根据place_uuids查询记录信息
@blue_print.route('/get_doc_mark_place_by_place_uuids', methods=['POST'])
def get_doc_mark_place_by_place_uuids():
    try:
        doc_mark_place_place_uuids = request.json.get('place_uuids', [])
        doc_mark_places = db.session.query(DocMarkPlace).filter(
            DocMarkPlace.place_uuid.in_(doc_mark_place_place_uuids), DocMarkPlace.valid == 1).all()

        res = success_res(data=[{
            "uuid": doc_mark_place.uuid,
            "doc_uuid": doc_mark_place.doc_uuid,
            "word": doc_mark_place.word,
            "type": doc_mark_place.type,
            "place_uuid": doc_mark_place.place_uuid,
            "direction": doc_mark_place.direction,
            "place_lon": doc_mark_place.place_lon,
            "place_lat": doc_mark_place.place_lat,
            "height": doc_mark_place.height,
            "unit": doc_mark_place.unit,
            "dms": doc_mark_place.dms,
            "distance": doc_mark_place.distance,
            "relation": doc_mark_place.relation,
            "create_by_uuid": doc_mark_place.create_by_uuid,
            "create_time": doc_mark_place.create_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.create_time else None,
            "update_by_uuid": doc_mark_place.update_by_uuid,
            "update_time": doc_mark_place.update_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_place.update_time else None,
            "valid": doc_mark_place.valid,
            "entity_or_sys": doc_mark_place.entity_or_sys,
            "appear_index_in_text": doc_mark_place.appear_index_in_text,
            "word_count": doc_mark_place.word_count,
            "word_sentence": doc_mark_place.word_sentence,
            "source_type": doc_mark_place.source_type,
            "place_name": Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid,
                                              Entity.valid == 1).first().name
            if Entity.query.filter(Entity.uuid == doc_mark_place.place_uuid, Entity.valid == 1).first() else ""
        } for doc_mark_place in doc_mark_places])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)