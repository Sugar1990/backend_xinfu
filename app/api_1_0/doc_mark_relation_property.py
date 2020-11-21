# -*- coding:utf-8 -*-
# @Author :MaYuhui
# work_location: Bei Jing
# @File : doc_mark_relation_property.py 
# @Time : 2020/10/12 16:20

from flask import jsonify, request
from . import api_doc_mark_relation_property as blue_print
from ..models import DocMarkRelationProperty, Entity, DocMarkEntity, DocMarkEvent
from .. import db
from .utils import success_res, fail_res
import uuid

@blue_print.route('/get_one_doc_mark_relation_property', methods=['GET'])
def get_one_doc_mark_relation_property():
    try:
        doc_mark_relation_property_uuid = request.args.get('uuid', None)

        doc_mark_relation_property = DocMarkRelationProperty.query.filter_by(uuid=doc_mark_relation_property_uuid,
                                                                             valid=1).first()
        if doc_mark_relation_property:
            res = success_res(data={
                "uuid": doc_mark_relation_property.uuid,
                "doc_uuid": doc_mark_relation_property.doc_uuid,
                "nid": doc_mark_relation_property.nid,
                "relation_uuid": doc_mark_relation_property.relation_uuid,
                "relation_name": doc_mark_relation_property.relation_name,
                "start_time": doc_mark_relation_property.start_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.start_time else None,
                "start_type": doc_mark_relation_property.start_type,
                "end_time": doc_mark_relation_property.end_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.end_time else None,
                "end_type": doc_mark_relation_property.end_type,
                "source_entity_uuid": doc_mark_relation_property.source_entity_uuid,
                "target_entity_uuid": doc_mark_relation_property.target_entity_uuid
            })
        else:
            res = fail_res(msg="关联数据不存在")
    except Exception as e:
        print(str(e))
        res = fail_res(data={
            "uuid": "-1",
            "doc_uuid": "-1",
            "nid": '',
            "relation_uuid": "-1",
            "relation_name": '',
            "start_time": None,
            "start_type": '',
            "end_time": None,
            "end_type": '',
            "source_entity_uuid": "-1",
            "target_entity_uuid": "-1"
        })
    return jsonify(res)


@blue_print.route('/get_doc_mark_relation_property_by_docId', methods=['GET'])
def get_doc_mark_relation_property_by_docId():
    try:
        doc_uuid = request.args.get('doc_uuid', None)

        doc_mark_relation_property_list = DocMarkRelationProperty.query.filter_by(doc_uuid=doc_uuid, valid=1).all()
        res = success_res(data=[{
            "uuid": doc_mark_relation_property.uuid,
            "doc_uuid": doc_mark_relation_property.doc_uuid,
            "nid": doc_mark_relation_property.nid,
            "relation_uuid": doc_mark_relation_property.relation_uuid,
            "relation_name": doc_mark_relation_property.relation_name,
            "start_time": doc_mark_relation_property.start_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.start_time else None,
            "start_type": doc_mark_relation_property.start_type,
            "end_time": doc_mark_relation_property.end_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.end_time else None,
            "end_type": doc_mark_relation_property.end_type,
            "source_entity_uuid": doc_mark_relation_property.source_entity_uuid,
            "target_entity_uuid": doc_mark_relation_property.target_entity_uuid
        } for doc_mark_relation_property in doc_mark_relation_property_list])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


@blue_print.route('/add_doc_mark_relation_property', methods=['POST'])
def add_doc_mark_relation_property():
    try:
        doc_uuid = request.json.get('doc_uuid', None)
        nid = request.json.get('nid', '')
        relation_uuid = request.json.get('relation_uuid', None)
        relation_name = request.json.get('relation_name', '')
        start_time = request.json.get('start_time', None)
        start_type = request.json.get('start_type', '')
        end_time = request.json.get('end_time', None)
        end_type = request.json.get('end_type', '')
        source_entity_uuid = request.json.get("source_entity_uuid", None)
        target_entity_uuid = request.json.get("target_entity_uuid", None)
        postion = request.json.get('position', [])
        if start_type == '1' and end_type == '1':
            source_entity = DocMarkEntity.query.filter_by(uuid=source_entity_uuid, valid=1).first()
            target_entity = DocMarkEntity.query.filter_by(uuid=target_entity_uuid, valid=1).first()
            if source_entity and target_entity:
                doc_mark_relation_property = DocMarkRelationProperty(
                    uuid=uuid.uuid1(),
                    doc_uuid=doc_uuid,
                    nid=nid,
                    relation_uuid=relation_uuid,
                    relation_name=relation_name,
                    start_time=start_time,
                    start_type=start_type,
                    end_time=end_time,
                    end_type=end_type,
                    source_entity_uuid=source_entity_uuid,
                    target_entity_uuid=target_entity_uuid,
                    position=postion,
                    valid=1)
                db.session.add(doc_mark_relation_property)
                db.session.commit()
                res = success_res(data={"uuid": doc_mark_relation_property.uuid})
            else:
                res = fail_res(msg="关联实体不存在")

        if start_type == '2' and end_type == '2':
            source_event = DocMarkEvent.query.filter_by(uuid=source_entity_uuid, valid=1).first()
            target_event = DocMarkEvent.query.filter_by(uuid=target_entity_uuid, valid=1).first()
            if source_event and target_event:
                doc_mark_relation_property = DocMarkRelationProperty(
                    uuid=uuid.uuid1(),
                    doc_uuid=doc_uuid,
                    nid=nid,
                    relation_uuid=relation_uuid,
                    relation_name=relation_name,
                    start_time=start_time,
                    start_type=start_type,
                    end_time=end_time,
                    end_type=end_type,
                    source_entity_uuid=source_entity_uuid,
                    target_entity_uuid=target_entity_uuid,
                    position=postion,
                    valid=1)
                db.session.add(doc_mark_relation_property)
                db.session.commit()
                res = success_res(data={"uuid": doc_mark_relation_property.uuid})
            else:
                res = fail_res(msg="关联事件不存在")

        else:
            res = fail_res(msg='请插入实体关系或事件关系数据')
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/modify_doc_mark_relation_property', methods=['PUT'])
def modify_doc_mark_relation_property():
    try:
        doc_mark_relation_property_uuid = request.json.get('uuid', None)
        doc_uuid = request.json.get('doc_uuid', None)
        nid = request.json.get('nid', '')
        relation_uuid = request.json.get('relation_uuid', None)
        relation_name = request.json.get('relation_name', '')
        start_time = request.json.get('start_time', None)
        start_type = request.json.get('start_type', '')
        end_time = request.json.get('end_time', None)
        end_type = request.json.get('end_type', 1)
        source_entity_uuid = request.json.get("source_entity_uuid", None)
        target_entity_uuid = request.json.get("target_entity_uuid", None)
        position = request.json.get('position', [])

        source_entity = Entity.query.filter_by(uuid=source_entity_uuid, valid=1).first()
        target_entity = Entity.query.filter_by(uuid=target_entity_uuid, valid=1).first()
        if source_entity and target_entity:
            doc_mark_place_expand = DocMarkRelationProperty.query.filter_by(uuid=doc_mark_relation_property_uuid,
                                                                            valid=1).first()
            if doc_mark_place_expand:
                if doc_uuid:
                    doc_mark_place_expand.doc_uuid = doc_uuid
                if nid:
                    doc_mark_place_expand.nid = nid
                if relation_uuid:
                    doc_mark_place_expand.relation_uuid = relation_uuid
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
                if source_entity_uuid:
                    doc_mark_place_expand.source_entity_uuid = source_entity_uuid
                if target_entity_uuid:
                    doc_mark_place_expand.source_entity_uuid = target_entity_uuid
                if position:
                    doc_mark_place_expand.position = position

                db.session.commit()
                res = success_res()
            else:
                res = fail_res(msg="uuid不存在!")
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
        doc_mark_relation_property_uuid = request.json.get("uuid", None)
        doc_mark_relation_property = DocMarkRelationProperty.query.filter_by(uuid=doc_mark_relation_property_uuid,
                                                                             valid=1).first()
        if doc_mark_relation_property:
            doc_mark_relation_property.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="操作对象不存在!")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


@blue_print.route('/get_graph_by_entity_id', methods=['GET'])
def get_graph_by_entity_id():
    try:
        center_entity_uuid = request.args.get("uuid", None)
        nodes, edges, exist_entity_uuids = [], [], []

        center_entity = Entity.query.filter_by(uuid=center_entity_uuid, valid=1).first()
        if center_entity:
            nodes.append({"uuid": center_entity.uuid,
                          "label": center_entity.name})
            exist_entity_uuids.append(center_entity_uuid)

            # 入关系
            relations = DocMarkRelationProperty.query.filter_by(target_entity_uuid=center_entity_uuid, valid=1).all()
            for e in relations:
                if e.source_entity_uuid not in exist_entity_uuids:
                    entity = Entity.query.filter_by(uuid=e.source_entity_uuid, valid=1).first()
                    if entity:
                        exist_entity_uuids.append(entity.uuid)
                        nodes.append({"uuid": entity.uuid,
                                      "label": entity.name})
                        edges.append({"source": str(entity.uuid),
                                      "target": center_entity_uuid,
                                      "label": e.relation_name})
            # 出关系
            relations = DocMarkRelationProperty.query.filter_by(source_entity_uuid=center_entity_uuid, valid=1).all()
            for e in relations:
                if e.source_entity_uuid not in exist_entity_uuids:
                    entity = Entity.query.filter_by(uuid=e.target_entity_uuid, valid=1).first()
                    if entity:
                        exist_entity_uuids.append(entity.uuid)
                        nodes.append({"uuid": entity.uuid,
                                      "label": entity.name})
                        edges.append({"source": entity.uuid,
                                      "target": center_entity_uuid,
                                      "label": e.relation_name})
            res = success_res(data={"nodes": nodes, "edges": edges})
        else:
            res = fail_res(msg="中心实体不存在",
                           data={"nodes": [], "edges": []})

    except Exception as e:
        print(str(e))
        res = fail_res(data={"nodes": [], "edges": []})

    return jsonify(res)


@blue_print.route('/delete_doc_mark_relation_property_by_doc_uuid_and_nid', methods=['POST'])
def delete_doc_mark_relation_property_by_doc_uuid_and_nid():
    try:
        doc_uuid = request.json.get("doc_uuid", None)
        nid = request.json.get('nid', '')
        doc_mark_relation_property = DocMarkRelationProperty.query.filter_by(doc_uuid=doc_uuid, nid=nid, valid=1).first()
        if doc_mark_relation_property:
            doc_mark_relation_property.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="操作对象不存在!")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


@blue_print.route('/delete_doc_mark_relation_property_by_nid', methods=['POST'])
def delete_doc_mark_relation_property_by_nid():
    try:
        nid = request.json.get('nid', '')
        doc_mark_relation_property = DocMarkRelationProperty.query.filter_by(nid=nid, valid=1).first()
        if doc_mark_relation_property:
            doc_mark_relation_property.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="操作对象不存在!")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


@blue_print.route('/get_doc_mark_relation_property_by_doc_uuid_and_nid', methods=['GET'])
def get_doc_mark_relation_property_by_doc_uuid_and_nid():
    try:
        doc_uuid = request.args.get('doc_uuid', None)
        nid = request.args.get('nid', '')
        doc_mark_relation_property = DocMarkRelationProperty.query.filter_by(doc_uuid=doc_uuid, nid=nid, valid=1).first()
        if doc_mark_relation_property:
            res = success_res(data={
                "uuid": doc_mark_relation_property.uuid,
                "doc_uuid": doc_mark_relation_property.doc_uuid,
                "nid": doc_mark_relation_property.nid,
                "relation_uuid": doc_mark_relation_property.relation_uuid,
                "relation_name": doc_mark_relation_property.relation_name,
                "start_time": doc_mark_relation_property.start_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.start_time else None,
                "start_type": doc_mark_relation_property.start_type,
                "end_time": doc_mark_relation_property.end_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.end_time else None,
                "end_type": doc_mark_relation_property.end_type,
                "source_entity_uuid": doc_mark_relation_property.source_entity_uuid,
                "target_entity_uuid": doc_mark_relation_property.target_entity_uuid,
                "position": doc_mark_relation_property.position
            })
        else:
            res = fail_res(msg="关联数据不存在")
    except Exception as e:
        print(str(e))
        res = fail_res(data={
            "uuid": "-1",
            "doc_uuid": "-1",
            "nid": '',
            "relation_uuid": "-1",
            "relation_name": '',
            "start_time": None,
            "start_type": '',
            "end_time": None,
            "end_type": '',
            "source_entity_uuid": "-1",
            "target_entity_uuid": "-1",
            "position": []
        })
    return jsonify(res)


@blue_print.route('/get_doc_mark_relation_property_by_nids', methods=['POST'])
def get_doc_mark_relation_property_by_nids():
    try:
        nids = request.json.get('nids', [])
        doc_mark_relation_property_list = DocMarkRelationProperty.query.filter(DocMarkRelationProperty.nid.in_(nids),
                                                                               DocMarkRelationProperty.valid==1).all()
        res = success_res(data=[{
            "uuid": doc_mark_relation_property.uuid,
            "doc_uuid": doc_mark_relation_property.doc_uuid,
            "nid": doc_mark_relation_property.nid,
            "relation_uuid": doc_mark_relation_property.relation_uuid,
            "relation_name": doc_mark_relation_property.relation_name,
            "start_time": doc_mark_relation_property.start_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.start_time else None,
            "start_type": doc_mark_relation_property.start_type,
            "end_time": doc_mark_relation_property.end_time.strftime(
                '%Y-%m-%d %H:%M:%S') if doc_mark_relation_property.end_time else None,
            "end_type": doc_mark_relation_property.end_type,
            "source_entity_uuid": doc_mark_relation_property.source_entity_uuid,
            "target_entity_uuid": doc_mark_relation_property.target_entity_uuid,
            "position": doc_mark_relation_property.position} for doc_mark_relation_property in doc_mark_relation_property_list])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)