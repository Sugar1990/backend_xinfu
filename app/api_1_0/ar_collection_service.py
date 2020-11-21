#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json

import requests
from flask import jsonify, request
from . import api_ar_collection_service as blue_print
from .utils import success_res, fail_res
from ..conf import ES_SERVER_PORT, LOCAL_IP, ES_SERVER_IP


@blue_print.route('save_entity_relation', methods=['POST'])
def save_entity_relation():
    try:
        source_entity_uuid = request.json.get('source_entity_uuid', None)
        target_entity_uuid = request.json.get('target_entity_uuid', None)
        start_time = request.json.get('start_time', None)
        end_time = request.json.get('end_time', None)
        relation_uuid = request.json.get('relation_uuid', None)
        paras = {
            "_from": source_entity_uuid,
            "_to": target_entity_uuid,
            'start_time': start_time,
            'end_time': end_time,
            "type": relation_uuid
        }
        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/insert_edge_data'
        body = {"collection": "entity_relation",
                "data": [paras]}
        data = json.dumps(body)
        result = requests.post(url=url, data=data, headers=header)
        if result.status_code in (200, 201):
            res = success_res()
        else:
            res = fail_res("接口调用失败！")
    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


@blue_print.route('get_entities_by_doc_uuid', methods=['GET'])
def get_entities_by_doc_uuid():
    try:
        doc_uuid = request.json.get('doc_uuid', None)
        para = {
            "collection": "entity",
            "filter_dict": {"doc_uuid": doc_uuid}
        }
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/query_data'
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


@blue_print.route('get_all_event_relations', methods=['GET'])
def get_all_event_relations():
    try:
        para = {
            "collection": "event_relation"
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


@blue_print.route('/get_article_relationship_entity_by_entityid_and_docid', methods=['GET'])
def get_article_relationship_entity_by_entityid_and_docid():
    try:
        entity_uuid = request.args.get('entity_uuid', None)
        doc_uuid = request.args.get('doc_uuid', None)
        paras = {
            "entity_uuid": entity_uuid,
            "doc_uuid": doc_uuid,
        }

        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/query_data'
        body = {"collection": "entity_relation",
                "filter_dict": paras}
        # data = json.dumps(body)
        result = requests.get(url=url, params=body)
        if result.status_code in (200,201):
            res = success_res(data=json.loads(result.text))
        else:
            res = fail_res(msg='调用arango基础服务失败')

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)

@blue_print.route('/get_article_relationship_entity_by_entity_time_parameter', methods=['POST'])
def get_article_relationship_entity_by_entity_time_parameter():
    try:
        entity_uuid = request.json.get('entity_uuid', None)
        entity_type = request.json.get('entity_type', 0)
        relation_type = request.json.get('relation_type', '')
        start_time = request.json.get('start_time', None)
        end_time = request.json.get('end_time', None)
        paras = {
            "entity_uuid": entity_uuid,
            "entity_type": entity_type,
            "relation_type": relation_type,
            "start_time": start_time,
            "end_time": end_time,
        }
        # header = {"Content-Type": "application/json; charset=UTF-8"}
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/query_data'
        body = {"collection": "entity_relation",
                "filter_dict": paras}
        # data = json.dumps(body)
        result = requests.get(url=url, params=body)
        if result.status_code in (200, 201):
            res = success_res(data=json.loads(result.text))
        else:
            res = fail_res(msg='调用arango基础接口失败')

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


# 根据关系删除实体关系
@blue_print.route('/delete_entity_relation_by_edge_id', methods=['POST'])
def delete_entity_relation_by_entity_id():
    try:
        relation_id = request.json.get('relation_id', '')
        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/edge/delete_relation'
        body = {"collection_name": "entity_relation",
                "key": [relation_id]}
        data = json.dumps(body)
        result = requests.post(url=url, data=data, headers=header)
        if result.status_code in (200, 201):
            res = success_res()
        else:
            res = fail_res("删除失败！")

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)
