# -*- coding: UTF-8 -*-
import datetime
from flask import jsonify, request
from . import api_doc_mark_place as blue_print
from ..models import DocMarkPlace
from .. import db
from .utils import success_res, fail_res
@blue_print.route('/get_doc_mark_place_by_doc_id', methods=['GET'])
def get_doc_mark_place_by_doc_id():
    try:
        doc_mark_place_doc_id = request.args.get('doc_id', 0, type=int)
        if isinstance(doc_mark_place_doc_id, int):
            doc_mark_places = DocMarkPlace.query.filter_by(id=doc_mark_place_doc_id, valid=1).all()
            res = success_res(data=[{
                "id": doc_mark_place.id,
                "doc_id": doc_mark_place.doc_id,
                "word": doc_mark_place.word,
                "type": doc_mark_place.type,
                "place_id": doc_mark_place.place_id,
                "direction": doc_mark_place.direction,
                "place_lon": doc_mark_place.place_lon,
                "place_lat": doc_mark_place.place_lat,
                "height": doc_mark_place.height,
                "unit": doc_mark_place.unit,
                "dms": doc_mark_place.dms,
                "distance": doc_mark_place.distance,
                "relation": doc_mark_place.relation,
                "create_by": doc_mark_place.create_by,
                "create_time": doc_mark_place.create_time,
                "update_by": doc_mark_place.update_by,
                "update_time": doc_mark_place.update_time,
                "valid": doc_mark_place.valid,
                "entity_or_sys": doc_mark_place.entity_or_sys,
                "appear_index_in_text": doc_mark_place.appear_index_in_text
            } for doc_mark_place in doc_mark_places])
    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)



@blue_print.route('/get_doc_mark_place_by_doc_id', methods=['GET'])
def get_doc_mark_place_by_doc_id():
    try:
        doc_mark_place_doc_id = request.args.get('doc_id', 0, type=int)
        if isinstance(doc_mark_place_doc_id, int):
            doc_mark_places = DocMarkPlace.query.filter_by(id=doc_mark_place_doc_id, valid=1).all()
            res = success_res(data=[{
                "id": doc_mark_place.id,
                "doc_id": doc_mark_place.doc_id,
                "word": doc_mark_place.word,
                "type": doc_mark_place.type,
                "place_id": doc_mark_place.place_id,
                "direction": doc_mark_place.direction,
                "place_lon": doc_mark_place.place_lon,
                "place_lat": doc_mark_place.place_lat,
                "height": doc_mark_place.height,
                "unit": doc_mark_place.unit,
                "dms": doc_mark_place.dms,
                "distance": doc_mark_place.distance,
                "relation": doc_mark_place.relation,
                "create_by": doc_mark_place.create_by,
                "create_time": doc_mark_place.create_time,
                "update_by": doc_mark_place.update_by,
                "update_time": doc_mark_place.update_time,
                "valid": doc_mark_place.valid,
                "entity_or_sys": doc_mark_place.entity_or_sys,
                "appear_index_in_text": doc_mark_place.appear_index_in_text
            } for doc_mark_place in doc_mark_places])
    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


@blue_print.route('/get_one_doc_mark_place_by_id', methods=['GET'])
def get_one_doc_mark_place_by_id():
    try:
        doc_mark_place_id = request.args.get('id', 0, type=int)
        if isinstance(doc_mark_place_id, int):
            doc_mark_place = DocMarkPlace.query.filter_by(id=doc_mark_place_id, valid=1).first()
            res = {
                "id": doc_mark_place.id,
                "doc_id": doc_mark_place.doc_id,
                "word": doc_mark_place.word,
                "type": doc_mark_place.type,
                "place_id": doc_mark_place.place_id,
                "direction": doc_mark_place.direction,
                "place_lon": doc_mark_place.place_lon,
                "place_lat": doc_mark_place.place_lat,
                "height": doc_mark_place.height,
                "unit": doc_mark_place.unit,
                "dms": doc_mark_place.dms,
                "distance": doc_mark_place.distance,
                "relation": doc_mark_place.relation,
                "create_by": doc_mark_place.create_by,
                "create_time": doc_mark_place.create_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if doc_mark_place.create_time else None,
                "update_by": doc_mark_place.update_by,
                "update_time": doc_mark_place.update_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if doc_mark_place.update_time else None,
                "valid": doc_mark_place.valid,
                "entity_or_sys": doc_mark_place.entity_or_sys,
                "appear_index_in_text": doc_mark_place.appear_index_in_text
            }
    except Exception as e:
        print(str(e))
        res = {
            "id": -1,
            "doc_id": "",
            "word": "",
            "type": "",
            "place_id": "",
            "direction": "",
            "place_lon": "",
            "place_lat": "",
            "height": "",
            "unit": "",
            "dms": "",
            "distance": 0.0,
            "relation": "",
            "create_by": -1,
            "create_time": "",
            "update_by": -1,
            "update_time": "",
            "valid": -1,
            "entity_or_sys": -1,
            "appear_index_in_text": -1
        }
    return jsonify(res)


@blue_print.route('/get_one_doc_mark_place_by_doc_id', methods=['GET'])
def get_one_doc_mark_place_by_doc_id():
    try:
        doc_mark_place_doc_id = request.args.get('doc_id', 0, type=int)
        if isinstance(doc_mark_place_doc_id, int):
            doc_mark_place = DocMarkPlace.query.filter_by(id=doc_mark_place_doc_id, valid=1).first()
            res = {
                "id": doc_mark_place.id,
                "doc_id": doc_mark_place.doc_id,
                "word": doc_mark_place.word,
                "type": doc_mark_place.type,
                "place_id": doc_mark_place.place_id,
                "direction": doc_mark_place.direction,
                "place_lon": doc_mark_place.place_lon,
                "place_lat": doc_mark_place.place_lat,
                "height": doc_mark_place.height,
                "unit": doc_mark_place.unit,
                "dms": doc_mark_place.dms,
                "distance": doc_mark_place.distance,
                "relation": doc_mark_place.relation,
                "create_by": doc_mark_place.create_by,
                "create_time": doc_mark_place.create_time,
                "update_by": doc_mark_place.update_by,
                "update_time": doc_mark_place.update_time,
                "valid": doc_mark_place.valid,
                "entity_or_sys": doc_mark_place.entity_or_sys,
                "appear_index_in_text": doc_mark_place.appear_index_in_text
            }
    except Exception as e:
        print(str(e))
        res = {
            "id": -1,
            "doc_id": "",
            "word": "",
            "type": "",
            "place_id": "",
            "direction": "",
            "place_lon": "",
            "place_lat": "",
            "height": "",
            "unit": "",
            "dms": "",
            "distance": 0.0,
            "relation": "",
            "create_by": -1,
            "create_time": "",
            "update_by": -1,
            "update_time": "",
            "valid": -1,
            "entity_or_sys": -1,
            "appear_index_in_text": []
        }
    return jsonify(res)



@blue_print.route('/add_doc_mark_place', methods=['POST'])
def add_doc_mark_place():
    try:
        doc_id = request.json.get('doc_id',0)
        word = request.json.get('word', '')
        type = request.json.get('type', 0)
        place_id = request.json.get('place_id', 0)
        direction = request.json.get('direction', '')
        place_lon = request.json.get('place_lon', '')
        place_lat = request.json.get('place_lat', '')
        height = request.json.get('height', '')
        unit = request.json.get('unit', '')
        dms = request.json.get('dms', [])
        distance = request.json.get('distance', 0.0)
        relation = request.json.get('relation', '')
        create_by = request.json.get('create_by', 0)
        entity_or_sys = request.json.get('entity_or_sys', 0)
        appear_index_in_text = request.json.get('appear_index_in_text',[])
        doc_mark_place = DocMarkPlace.query.filter_by(doc_id=doc_id, word=word,type=type,place_id=place_id,
                                                      direction=direction, place_lon=place_lon, place_lat=place_lat, height=height,
                                                      unit=unit,dms=dms,distance=distance,relation=relation,create_by=create_by,
                                                      entity_or_sys=entity_or_sys,appear_index_in_text=appear_index_in_text,valid=1).first()
        if doc_mark_place:
            res = fail_res(msg="文档标记地点已存在!")
        else:
            docMarkPlace = DocMarkPlace(doc_id=doc_id,word=word,type=type, place_id=place_id,
                                                      direction=direction, place_lon=place_lon, place_lat=place_lat, height=height,
                                                      unit=unit,dms=dms,distance=distance,relation=relation,create_by=create_by,
                                                      create_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                      appear_index_in_text=appear_index_in_text,
                                                      entity_or_sys=entity_or_sys,valid=1)
            db.session.add(docMarkPlace)
            db.session.commit()
            res = success_res(data={"id": docMarkPlace.id})
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/modify_doc_mark_place', methods=['PUT'])
def modify_doc_mark_place():
    try:
        id = request.json.get('id',0)
        doc_id = request.json.get('doc_id', 0)
        word = request.json.get('word', '')
        type = request.json.get('type', 0)
        place_id = request.json.get('place_id', 0)
        direction = request.json.get('direction', '')
        place_lon = request.json.get('place_lon', '')
        place_lat = request.json.get('place_lat', '')
        height = request.json.get('height', '')
        unit = request.json.get('unit', '')
        dms = request.json.get('dms', [])
        distance = request.json.get('distance', 0.0)
        relation = request.json.get('relation', '')
        update_by = request.json.get('update_by', 0)  # 更新修改者
        entity_or_sys = request.json.get('entity_or_sys', 0)
        create_by = request.json.get('create_by', 0)
        create_time = request.json.get('create_time', None)
        appear_index_in_text = request.json.get('appear_index_in_text', [])
        doc_mark_place = DocMarkPlace.query.filter_by(id=id, valid=1).first()
        if doc_mark_place:
            doc_mark_place1 = DocMarkPlace.query.filter_by(doc_id=doc_id,word=word,type=type, place_id=place_id,
                                                      direction=direction, place_lon=place_lon, place_lat=place_lat, height=height,
                                                      unit=unit,dms=dms,distance=distance,relation=relation,create_by=create_by,
                                                      entity_or_sys=entity_or_sys,appear_index_in_text=appear_index_in_text,valid=1).first()
            if doc_mark_place1:
                res = fail_res(msg="文档标记地点已存在")
            else:
                if doc_id:
                    doc_mark_place.doc_id = doc_id
                if word:
                    doc_mark_place.word = word
                if type:
                    doc_mark_place.type = type
                if place_id:
                    doc_mark_place.place_id = place_id
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
                if create_by:
                    doc_mark_place.create_by = create_by
                if create_time:
                    doc_mark_place.create_time = create_time
                if update_by:
                    doc_mark_place.update_by = update_by
                # if update_time:
                doc_mark_place.update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if entity_or_sys:
                    doc_mark_place.entity_or_sys  = entity_or_sys
                if appear_index_in_text:
                    doc_mark_place.appear_index_in_text = appear_index_in_text
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
        id = request.json.get('id',0)
        doc_mark_place = DocMarkPlace.query.filter_by(id=id, valid=1).first()
        if doc_mark_place:
            doc_mark_place.valid = 0
            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)

