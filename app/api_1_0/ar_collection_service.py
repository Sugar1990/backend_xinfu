#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json

import requests
from flask import jsonify, request
from . import api_ar_collection_service as blue_print
from .utils import success_res, fail_res
from ..conf import ES_SERVER_PORT, LOCAL_IP, ES_SERVER_IP
from .. import db
from ..models import DocMarkRelationProperty
from sqlalchemy import or_

# 保存关系
@blue_print.route('save_edge_collection', methods=['POST'])
def save_edge_collection():
    try:
        uuid = request.json.get('uuid', None)
        collection_type = request.json.get('collection_type', 0) # 1表示实体关系集合,2表示事件关系集合
        source_uuid = request.json.get('source_uuid', None)
        target_uuid = request.json.get('target_uuid', None)
        start_time = request.json.get('start_time', None)
        end_time = request.json.get('end_time', None)
        relation_uuid = request.json.get('relation_uuid', None)
        relation_name = request.json.get('relation_name', '')
        doc_uuid = request.json.get('doc_uuid', None)
        collection = 'entity_relation' if collection_type == 1 else 'event_relation'
        node_collection = 'entity' if collection_type == 1 else 'event'
        # print("UUID:", uuid)
        paras = {
            "_key": uuid,
            "_from": node_collection + '/' + source_uuid,
            "_to": node_collection + '/' + target_uuid,
            'start_time': start_time,
            'end_time': end_time,
            "relation_uuid": relation_uuid,
            "relation_name": relation_name,
            "doc_uuid": doc_uuid
        }

        # print("paras:", paras)

        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/insert_edge_data'
        body = {"collection": collection,
                "data": [paras]}
        data = json.dumps(body)
        result = requests.post(url=url, data=data, headers=header)
        if result.status_code in (200, 201):
            print(json.loads(result.text))
            result = json.loads(result.text)
            if result.get('code') == 0:
                res = fail_res(msg=result.get('msg'))
            else:
                res = success_res()
        else:
            res = fail_res("接口调用失败！")
    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


#查询所有事件关系
@blue_print.route('get_all_relations', methods=['GET'])
def get_all_relations():
    try:
        collection_type = request.args.get('collection_type', 0, type=int)  # 1表示实体关系集合,2表示事件关系集合
        collection = 'entity_relation' if collection_type == 1 else 'event_relation'
        para = {
            "collection": collection
        }
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/query_all'
        # data = json.dumps(para)
        result = requests.get(url=url, params=para)
        if result.status_code in (200, 201):
            res = success_res(data=json.loads(result.text))
        else:
            res = fail_res(msg="接口调用失败！")

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


# 根据实体ID和文章ID获取关系
@blue_print.route('/get_article_relationship_entity_by_entityid_and_docid', methods=['GET'])
def get_article_relationship_entity_by_entityid_and_docid():
    try:
        entity_uuid = request.args.get('entity_uuid', None)
        doc_uuid = request.args.get('doc_uuid', None)
        record_uuid = request.args.get('record_uuid', None)
        paras = {}
        if doc_uuid:
            paras = {
                "doc_uuid": doc_uuid
            }
        if record_uuid:
            paras['_key'] = record_uuid

        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/query_data'
        body = {"collection": "entity_relation",
                "filter_dict": paras}
        data = json.dumps(body)
        result = requests.post(url=url, data=data, headers=header)
        if result.status_code in (200,201):
            if entity_uuid:
                entity_uuid = 'entity/'+entity_uuid
                data = json.loads(result.text)
                temp = []
                for item in data:
                    if item.get("_from") == entity_uuid or item.get("_to") == entity_uuid:
                        temp.append(item)
                res = success_res(data=temp)
            else:
                res = success_res(data=json.loads(result.text))
        else:
            res = fail_res(msg='调用arango基础服务失败')

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


# 根据实体ID获取事件关系
@blue_print.route('/get_event_relationships_by_eventid', methods=['GET'])
def get_article_relationship_entity_by_entityid():
    try:
        event_uuid = request.args.get('event_uuid', None)
        event_uuid = 'event/'+event_uuid
        #header = {"Content-Type": "application/json; charset=UTF-8"}
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/query_all'
        body = {"collection": "event_relation"}
        #data = json.dumps(body)
        result = requests.get(url=url, params=body)
        if result.status_code in (200,201):
            if event_uuid:
                data = json.loads(result.text)
                temp = []
                for item in data:
                    if item.get("_from") == event_uuid or item.get("_to") == event_uuid:
                        temp.append(item)
                res = success_res(data=temp)
            else:
                res = success_res(data=json.loads(result.text))
        else:
            res = fail_res(msg='调用arango基础服务失败')

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


# 根据实体ids和relation_uuid获取事件关系
@blue_print.route('/get_event_relations_by_event_ids_and_relation_id', methods=['POST'])
def get_event_relations_by_event_id_and_relation_id():
    try:
        event_uuids = request.json.get('event_uuids', [])
        relation_uuid = request.json.get('relation_uuid', None)
        if relation_uuid:
            paras = {
                "relation_uuid": relation_uuid
            }
        else:
            paras={}

        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/query_data'
        body = {"collection": "event_relation",
                "filter_dict": paras}
        data = json.dumps(body)
        result = requests.post(url=url, data=data, headers=header)
        if result.status_code in (200,201):
            if event_uuids:
                data = json.loads(result.text)
                temp = []
                for item in data:
                    if item.get("_from").split("/")[-1] in event_uuids or item.get("_to").split("/")[-1] in event_uuids:
                        temp.append(item)
                res = success_res(data=temp)
            else:
                res = success_res(data=json.loads(result.text))
        else:
            res = fail_res(msg='调用arango基础服务失败')

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


# 根据开始节点、结束节点、关系ID、类型返回关系列表
@blue_print.route('/get_article_relationship_entity_by_entity_time_parameter', methods=['POST'])
def get_article_relationship_entity_by_entity_time_parameter():
    try:
        entity_uuid = request.json.get('entity_uuid', None)
        entity_type = request.json.get('entity_type', 0)
        relation_type = request.json.get('relation_type', '')
        start_time = request.json.get('start_time', None)
        end_time = request.json.get('end_time', None)
        paras = {
            "entity_type": entity_type,
            "relation_type": relation_type,
            "start_time": start_time,
            "end_time": end_time,
        }
        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/query_data'
        body = {"collection": "entity_relation",
                "filter_dict": paras}
        data = json.dumps(body)
        result = requests.post(url=url, data=data, headers=header)
        if result.status_code in (200, 201):
            data = json.loads(result.text)
            temp = []
            for item in data:
                if item.get("_from") == entity_uuid or item.get("_to") == entity_uuid:
                    temp.append(item)
            res = success_res(data=temp)
        else:
            res = fail_res(msg='调用arango基础服务失败')

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


# 根据关系删除实体关系,可以复用根据doc_uuid删除
@blue_print.route('/delete_entity_relation_by_edge_id', methods=['POST'])
def delete_entity_relation_by_edge_id():
    try:
        collection_type = request.json.get('collection_type', 0)
        doc_mark_relation_property_uuid = request.json.get('relation_id', '')
        if doc_mark_relation_property_uuid:
            doc_mark_relation_property = DocMarkRelationProperty.query.filter_by(uuid=doc_mark_relation_property_uuid,
                                                                                 valid=1).first()
            if doc_mark_relation_property:
                doc_mark_relation_property.valid = 0

            header = {"Content-Type": "application/json; charset=UTF-8"}
            url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/edge/delete_relation'
            body = {"collection_name": "entity_relation" if collection_type==1 else "event_relation",
                    "key": [doc_mark_relation_property_uuid]}
            data = json.dumps(body)
            result = requests.post(url=url, data=data, headers=header)
            if result.status_code in (200, 201):
                res = success_res("删除成功！")
            else:
                res = fail_res("删除失败！")
        else:
            res = fail_res(msg='doc_mark_relation_property_uuid参数不能为空')

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 根据开始节点、结束节点、关系ID、类型返回关系列表
@blue_print.route('/get_relation_by_source_target_and_relation_id', methods=['POST'])
def get_relation_by_source_target_and_relation_id():
    try:
        collection_type = request.json.get('collection_type', 0)  # 1表示实体关系集合,2表示事件关系集合
        source_uuid = request.json.get('source_uuid', None)
        target_uuid = request.json.get('target_uuid', None)
        relation_uuid = request.json.get('relation_uuid', None)
        collection = 'entity_relation' if collection_type == 1 else 'event_relation'
        para = {
            "collection": collection,
            "filter_dict": {"_from": collection + '/' +source_uuid,
                            "_to": collection + '/' + target_uuid,
                            "relation_uuid": relation_uuid}
        }
        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/query_data'
        data = json.dumps(para)
        result = requests.post(url=url, data=data, headers=header)
        if result.status_code in (200, 201):
            res = success_res(data=json.loads(result.text))
        else:
            res = fail_res(msg="接口调用失败！")

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


# 根据关系relation_uuids返回关系列表
@blue_print.route('/get_relation_by_relation_ids', methods=['POST'])
def get_relation_by_relation_ids():
    try:
        relation_uuids = request.json.get('relation_uuids', [])
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/query_all'
        body = {"collection": "entity_relation"}
        result = requests.get(url=url, params=body)

        if result.status_code in (200, 201):
            if relation_uuids:
                data = json.loads(result.text)
                temp = []
                for item in data:
                    if item.get("relation_uuid") in relation_uuids:
                        temp.append(item)
                res = success_res(data=temp)
            else:
                res = success_res(data=json.loads(result.text))
        else:
            res = fail_res(msg='调用arango基础服务失败')

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


# 根据节点删除实体关系
@blue_print.route('/delete_entity_relation_by_entity_id', methods=['POST'])
def delete_entity_relation_by_entity_id():
    try:
        entity_uuid = request.json.get('entity_uuid', None)
        if entity_uuid:
            doc_mark_relation_property_list = DocMarkRelationProperty.query.filter(DocMarkRelationProperty.source_entity_uuid == entity_uuid,
                                                                                   DocMarkRelationProperty.valid == 1,
                                                                                   or_(DocMarkRelationProperty.target_entity_uuid == entity_uuid)).all()
            for doc_mark_relation_property in doc_mark_relation_property_list:
                if doc_mark_relation_property:
                    doc_mark_relation_property.valid = 0

            header = {"Content-Type": "application/json; charset=UTF-8"}
            url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/delete_entity_edges'
            body = {"uuid": entity_uuid,
                    "type": "entity"}
            data = json.dumps(body)
            result = requests.post(url=url, data=data, headers=header)
            if result.status_code in (200, 201):
                res = success_res("删除成功！")
            else:
                res = fail_res("删除失败！")
        else:
            res = fail_res(msg="entity_uuid参数不能为空！")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 根据doc_id返回一个整个图谱
@blue_print.route('/get_graph_by_doc_id', methods=['GET'])
def get_graph_by_doc_id():
    try:
        doc_uuid = request.args.get('doc_uuid', None)
        if doc_uuid:
            header = {"Content-Type": "application/json; charset=UTF-8"}
            url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/exec_aql'
            print("url：", url)
            aql = "let edges = (for e in entity_relation filter e.doc_uuid=='{0}' return e) let from_entities = (for e in entity_relation filter e.doc_uuid=='{1}' return e._from) " \
                  "let to_entities = (for e in entity_relation filter e.doc_uuid=='{2}' return e._to) let entities = (for v in entity filter v._id in to_entities or v._id in from_entities return v) " \
                  "return {{edges, entities}}".format(doc_uuid, doc_uuid, doc_uuid)
            body = {"aql": aql,}
            data = json.dumps(body)
            result = requests.post(url=url, data=data, headers=header)

            if result.status_code in (200,201):
                res = success_res(data=json.loads(result.text))
            else:
                res = fail_res(msg='调用arango基础服务失败')
        else:
            res = fail_res(msg="doc_uuid参数不能为空！")

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)