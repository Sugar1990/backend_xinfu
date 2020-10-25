# -*- coding:utf-8 -*-
# @Author :MaYuhui
# work_location: Bei Jing
# @File : doc_mark_relation_property.py 
# @Time : 2020/10/12 16:20

from flask import jsonify, request
from . import api_doc_mark_relation_property as blue_print
from ..models import DocMarkRelationProperty, Entity
from .. import db
from .utils import success_res, fail_res


@blue_print.route('/get_one_doc_mark_relation_property', methods=['GET'])
def get_one_doc_mark_relation_property():
    try:
        doc_mark_relation_property_id = request.args.get('id', 0, type=int)

        doc_mark_relation_property = DocMarkRelationProperty.query.filter_by(id=doc_mark_relation_property_id,
                                                                             valid=1).first()
        if doc_mark_relation_property:
            res = success_res(data={
                "id": doc_mark_relation_property.id,
                "doc_id": doc_mark_relation_property.doc_id,
                "nid": doc_mark_relation_property.nid,
                "relation_id": doc_mark_relation_property.relation_id,
                "relation_name": doc_mark_relation_property.relation_name,
                "start_time": doc_mark_relation_property.start_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.start_time else None,
                "start_type": doc_mark_relation_property.start_type,
                "end_time": doc_mark_relation_property.end_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.end_time else None,
                "end_type": doc_mark_relation_property.end_type,
                "source_entity_id": doc_mark_relation_property.source_entity_id,
                "target_entity_id": doc_mark_relation_property.target_entity_id
            })
        else:
            res = fail_res(msg="关联数据不存在")
    except Exception as e:
        print(str(e))
        res = fail_res(data={
            "id": -1,
            "doc_id": -1,
            "nid": '',
            "relation_id": -1,
            "relation_name": '',
            "start_time": None,
            "start_type": '',
            "end_time": None,
            "end_type": '',
            "source_entity_id": -1,
            "target_entity_id": -1
        })
    return jsonify(res)


@blue_print.route('/get_doc_mark_relation_property_by_docId', methods=['GET'])
def get_doc_mark_relation_property_by_docId():
    try:
        doc_id = request.args.get('doc_id', 0, type=int)

        doc_mark_relation_property_list = DocMarkRelationProperty.query.filter_by(doc_id=doc_id, valid=1).all()
        res = success_res(data=[{
            "id": doc_mark_relation_property.id,
            "doc_id": doc_mark_relation_property.doc_id,
            "nid": doc_mark_relation_property.nid,
            "relation_id": doc_mark_relation_property.relation_id,
            "relation_name": doc_mark_relation_property.relation_name,
            "start_time": doc_mark_relation_property.start_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.start_time else None,
            "start_type": doc_mark_relation_property.start_type,
            "end_time": doc_mark_relation_property.end_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.end_time else None,
            "end_type": doc_mark_relation_property.end_type,
            "source_entity_id": doc_mark_relation_property.source_entity_id,
            "target_entity_id": doc_mark_relation_property.target_entity_id
        } for doc_mark_relation_property in doc_mark_relation_property_list])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


@blue_print.route('/add_doc_mark_relation_property', methods=['POST'])
def add_doc_mark_relation_property():
    try:
        doc_id = request.json.get('doc_id', 0)
        nid = request.json.get('nid', 0)
        relation_id = request.json.get('relation_id', 0)
        relation_name = request.json.get('relation_name', 0)
        start_time = request.json.get('start_time', None)
        start_type = request.json.get('start_type', '')
        end_time = request.json.get('end_time', None)
        end_type = request.json.get('end_type', '')
        source_entity_id = request.json.get("source_entity_id", 0)
        target_entity_id = request.json.get("target_entity_id", 0)
        source_entity = Entity.query.filter_by(id=source_entity_id, valid=1).first()
        target_entity = Entity.query.filter_by(id=target_entity_id, valid=1).first()
        if source_entity and target_entity:
            doc_mark_relation_property = DocMarkRelationProperty(
                doc_id=doc_id,
                nid=nid,
                relation_id=relation_id,
                relation_name=relation_name,
                start_time=start_time,
                start_type=start_type,
                end_time=end_time,
                end_type=end_type,
                source_entity_id=source_entity_id,
                target_entity_id=target_entity_id,
                valid=1)
            db.session.add(doc_mark_relation_property)
            db.session.commit()
            res = success_res(data={"id": doc_mark_relation_property.id})
        else:
            res = fail_res(msg="关联实体不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/modify_doc_mark_relation_property', methods=['PUT'])
def modify_doc_mark_relation_property():
    try:
        doc_mark_relation_property_id = request.json.get('id', 0)
        doc_id = request.json.get('doc_id', 0)
        nid = request.json.get('nid', 0)
        relation_id = request.json.get('relation_id', 0)
        relation_name = request.json.get('relation_name', 0)
        start_time = request.json.get('start_time', None)
        start_type = request.json.get('start_type', '')
        end_time = request.json.get('end_time', None)
        end_type = request.json.get('end_type', '')
        source_entity_id = request.json.get("source_entity_id", 0)
        target_entity_id = request.json.get("target_entity_id", 0)

        source_entity = Entity.query.filter_by(id=source_entity_id, valid=1).first()
        target_entity = Entity.query.filter_by(id=target_entity_id, valid=1).first()
        if source_entity and target_entity:
            if isinstance(doc_mark_relation_property_id, int):
                doc_mark_place_expand = DocMarkRelationProperty.query.filter_by(id=doc_mark_relation_property_id,
                                                                                valid=1).first()
                if doc_mark_place_expand:
                    if doc_id:
                        doc_mark_place_expand.doc_id = doc_id
                    if nid:
                        doc_mark_place_expand.nid = nid
                    if relation_id:
                        doc_mark_place_expand.relation_id = relation_id
                    if relation_name:
                        doc_mark_place_expand.relation_name = relation_name
                    if start_time:
                        doc_mark_place_expand.start_time = start_time
                    if start_type:
                        doc_mark_place_expand.start_type = start_type
                    if end_time:
                        doc_mark_place_expand.end_time = end_time
                    if end_type:
                        doc_mark_place_expand.end_type = end_type
                    if source_entity_id:
                        doc_mark_place_expand.source_entity_id = source_entity_id
                    if target_entity_id:
                        doc_mark_place_expand.source_entity_id = target_entity_id
                    db.session.commit()
                    res = success_res()
                else:
                    res = fail_res(msg="id不存在!")
            else:
                res = fail_res("paramter \"id\" is not int type")
        else:
            res = fail_res(msg="关联实体不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="修改失败！")
    return jsonify(res)


@blue_print.route('/delete_doc_mark_relation_property', methods=['POST'])
def delete_doc_mark_relation_property():
    try:
        doc_mark_relation_property_id = request.json.get("id", 0)
        if isinstance(doc_mark_relation_property_id, int):
            doc_mark_relation_property = DocMarkRelationProperty.query.filter_by(id=doc_mark_relation_property_id,
                                                                                 valid=1).first()
            if doc_mark_relation_property:
                doc_mark_relation_property.valid = 0
                res = success_res()
            else:
                res = fail_res(msg="操作对象不存在!")
        else:
            res = fail_res("paramter \"id\" is not int type")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)
