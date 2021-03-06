# -*- coding: UTF-8 -*-
import datetime
import jieba
import jieba.analyse as analyse
import json
import os
import re
import requests
import xlrd
import math
import uuid
# from flasgger import swag_from
from flask import request, jsonify
from pypinyin import lazy_pinyin
from sqlalchemy import or_, and_, not_
from werkzeug.utils import secure_filename
# from ..swagger.entity_dict import *
from . import api_entity as blue_print
from .utils import success_res, fail_res
from .. import db
from ..conf import ES_SERVER_IP, ES_SERVER_PORT, YC_ROOT_URL, YC_ROOT_URL_PYTHON, PLACE_BASE_NAME, USE_PLACE_SERVER
from ..models import Entity, EntityCategory, DocMarkPlace, DocMarkEntity, DocMarkEvent, Document, Customer, \
    DocMarkTimeTag
from .place import get_place_from_base_server
import zipfile


# from ..serve.neo4j_imp import create_node, update_node, delete_node


# -*- coding:utf-8 -*-
# author: Scandium
# work_location: Bei Jing
# File : entity_port.py
# time: 2020/8/28 8:56


# get_entity
@blue_print.route('/get_all', methods=['GET'])
# @swag_from(get_all_dict)
def get_all():
    ### 重要参数:(当前页和每页条目数)
    current_page = request.args.get('cur_page', 1, type=int)
    page_size = request.args.get('page_size', 15, type=int)
    category_uuid = request.args.get('category_uuid', None)
    type = request.args.get('type', 0, type=int)

    category = EntityCategory.query.filter_by(uuid=category_uuid, name=PLACE_BASE_NAME, valid=1).first()
    if category and int(USE_PLACE_SERVER):
        data, total_count = get_place_from_base_server(page_size=page_size, cur_page=current_page, search='')
        page_count = math.ceil(total_count / page_size)

    else:
        conditions = [Entity.valid == 1]
        if category_uuid:
            conditions.append(Entity.category_uuid == category_uuid)
        else:
            category_uuids = EntityCategory.query.with_entities(EntityCategory.uuid).filter_by(type=type, valid=1).all()
            category_uuids = [str(i[0]) for i in category_uuids]
            conditions.append(Entity.category_uuid.in_(category_uuids))

        conditions = tuple(conditions)
        pagination = Entity.query.filter(and_(*conditions)).paginate(current_page, page_size, False)

        data = [{
            "uuid": item.uuid,
            "name": item.name,
            'props': item.props if item.props else {},
            'synonyms': item.synonyms if item.synonyms else [],
            "summary": item.summary,
            'category': item.category_name(),
            'category_uuid': item.category_uuid,
            'longitude': item.longitude,
            'latitude': item.latitude
        } for item in pagination.items]
        total_count = pagination.total
        page_count = pagination.pages

    res = {
        "total_count": total_count,
        "page_count": page_count,
        "data": data,
        "cur_page": current_page
    }

    return jsonify(res)


@blue_print.route('/insert_entity', methods=['POST'])
# @swag_from(insert_entity_dict)
def insert_entity():
    try:
        name = request.json.get('name', "")
        category_uuid = request.json.get('category_uuid', '')
        props = request.json.get('props', {})
        synonyms = request.json.get('synonyms', [])
        summary = request.json.get('summary', '')
        sync = request.json.get('sync', 1)

        category = EntityCategory.query.filter_by(uuid=category_uuid, valid=1).first()
        if not category:
            res = fail_res(msg="实体类型不存在，添加失败！")
            return jsonify(res)

        # if category.name == PLACE_BASE_NAME:
        #     res = fail_res(msg="地名库由专业团队维护,不能添加！")
        #     return jsonify(res)
        if not name:
            res = fail_res(msg="实体名称不能为空，添加失败！")
            return jsonify(res)

        entity = Entity.query.filter(Entity.name == name, Entity.valid == 1,
                                     Entity.category_uuid == category_uuid).first()

        if not entity:
            props = props if props else {}
            if name in synonyms:
                synonyms.remove(name)
            entity = Entity(uuid=uuid.uuid1(), name=name, category_uuid=category_uuid, props=props, synonyms=synonyms,
                            summary=summary,
                            valid=1)

            # es 插入操作
            longitude, latitude = 0, 0
            # 地名实体获取经纬度
            if EntityCategory.get_category_name(category_uuid) == PLACE_BASE_NAME:
                longitude = request.json.get('longitude', 0)
                latitude = request.json.get('latitude', 0)
                if longitude and latitude:
                    entity.longitude = longitude
                    entity.latitude = latitude
                else:
                    res = fail_res(msg="地名实体经纬度不能为空")
                    return jsonify(res)

            db.session.add(entity)
            db.session.commit()
            # es_insert_item = {}
            #
            # if entity.uuid:
            #     es_insert_item = {"uuid": entity.uuid}
            # es 插入操作
            es_insert_item = {'uuid': str(entity.uuid)}
            if name:
                es_insert_item["name"] = name
            if category_uuid:
                es_insert_item["category_uuid"] = str(category_uuid)
            if summary:
                es_insert_item["summary"] = summary

            es_insert_item["props"] = props if props else {}
            if synonyms:
                es_insert_item["synonyms"] = synonyms

            if longitude:
                es_insert_item["longitude"] = longitude
            if latitude:
                es_insert_item["latitude"] = latitude

            data_insert_json = [es_insert_item]
            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'

            header = {"Content-Type": "application/json; charset=UTF-8"}

            # print(data_insert_json)
            para = {"data_insert_index": "entity", "data_insert_json": data_insert_json}
            search_result = requests.post(url + '/dataInsert', data=json.dumps(para), headers=header)
            # print(data_insert_json, search_result.text)

            # <editor-fold desc="yc insert name & synonyms">
            sync_yc_add_name(name, str(entity.uuid), str(entity.category_uuid), entity.get_yc_mark_category(),
                             longitude, latitude)

            sync_yc_add_synonyms(synonyms, str(entity.uuid), str(entity.category_uuid), entity.get_yc_mark_category(),
                                 longitude,
                                 latitude)
            # </editor-fold>

            # neo4j同步
            # create_node(entity.id, entity.name, entity.category_id)

            # arango 同步
            root_url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            header = {"Content-Type": "application/json"}
            serve_url = root_url + "/arango/insert_data"
            nodes = {
                "_key": str(entity.uuid),
                "uuid": str(entity.uuid),
                "name": entity.name,
                "category_uuid": str(entity.category_uuid)
            }
            para = {"collection": "entity", "data": nodes}
            search_result = requests.post(url=serve_url, data=json.dumps(para), headers=header)
            # print(search_result.status_code, flush=True)
            # print(search_result.text, flush=True)
            if search_result.status_code != 200 or not json.loads(search_result.text).get("code", 0):
                return fail_res(msg="arango serve error: {}".format(json.loads(search_result.text).get("msg", "")))

            res = success_res(data={"entity_uuid": str(entity.uuid)})
        else:
            res = fail_res(msg="该实体名称已存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/update_entity', methods=['PUT'])
# @swag_from(update_entity_dict)
def update_entity():
    try:
        uuid = request.json.get('uuid', None)
        name = request.json.get('name', '')
        category_uuid = request.json.get('category_uuid', None)
        props = request.json.get('props', {})
        synonyms = request.json.get('synonyms', [])
        summary = request.json.get('summary', '')
        sync = request.json.get('sync', 1)

        category = EntityCategory.query.filter_by(uuid=category_uuid, valid=1).first()
        if not category:
            res = fail_res(msg="实体类型不存在，修改失败！")
            return jsonify(res)

        if not name:
            res = fail_res(msg="实体名称不能为空，修改失败！")
            return jsonify(res)

        # if category_id == EntityCategory.get_category_id(PLACE_BASE_NAME):
        #     res = fail_res(msg="地名库由专业团队维护,不能修改！")
        #     return jsonify(res)

        # entityPlace = Entity.query.filter_by(id=id, valid=1).first()
        # category_place = EntityCategory.query.filter_by(id=entityPlace.category_id, valid=1).first()
        # if category_place.name == PLACE_BASE_NAME:
        #     res = fail_res(msg="地名库由专业团队维护,不能修改！")
        #     return jsonify(res)

        entity = Entity.query.filter_by(uuid=uuid, valid=1).first()

        if entity:
            entity_same = Entity.query.filter(Entity.name == name, Entity.valid == 1, Entity.uuid != uuid,
                                              Entity.category_uuid == category_uuid).first()
            if entity_same:
                res = fail_res(msg="相同实体名称已存在")
                return jsonify(res)

            key_value_json = {}
            longitude, latitude = 0, 0
            # 地名实体获取经纬度
            if EntityCategory.get_category_name(category_uuid) == PLACE_BASE_NAME:
                longitude = request.json.get('longitude', 0)
                latitude = request.json.get('latitude', 0)
                if longitude and latitude:
                    entity.longitude = longitude
                    key_value_json['longitude'] = longitude
                    entity.latitude = latitude
                    key_value_json['latitude'] = latitude
                else:
                    res = fail_res(msg="地名实体经纬度不能为空")
                    return jsonify(res)

            yc_update_data, add_synonyms, remove_synonyms = [], [], []
            if name:
                # <editor-fold desc="yc update name">
                if name != entity.name:
                    sync_yc_update_name(entity.name, name, entity.uuid, entity.get_yc_mark_category(), longitude,
                                        latitude)
                # </editor-fold>
                entity.name = name
                key_value_json['name'] = name
            if category_uuid:
                # <editor-fold desc="yc update category_id">
                if category_uuid != entity.category_uuid:
                    sync_yc_update_category_id(entity.uuid, entity.category_uuid, category_uuid,
                                               entity.get_yc_mark_category(), longitude, latitude)
                # </editor-fold>
                entity.category_uuid = category_uuid
                key_value_json['category_uuid'] = category_uuid
            if isinstance(props, dict):
                entity.props = props
                key_value_json['props'] = props
            if summary:
                entity.summary = summary
                key_value_json['summary'] = summary
            if isinstance(synonyms, list) and synonyms:
                # <editor-fold desc="yc add & del synonyms">
                add_synonyms = list(set(synonyms).difference(set(entity.synonyms if entity.synonyms else [])))
                remove_synonyms = list(set(entity.synonyms if entity.synonyms else []).difference(set(synonyms)))

                sync_yc_add_synonyms(add_synonyms, entity.uuid, entity.category_uuid,
                                     entity.get_yc_mark_category(), longitude, latitude)
                if remove_synonyms:
                    # 删除别名
                    sync_yc_del_synonyms(remove_synonyms, entity.uuid, entity.get_yc_mark_category())
                # </editor-fold>
                if name in synonyms:
                    synonyms.remove(name)
                entity.synonyms = synonyms
                key_value_json['synonyms'] = entity.synonyms
            db.session.commit()

            # 获得es对应实体
            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            search_json = {
                "uuid": {"type": "term", "value": str(entity.uuid)}
            }
            es_id_para = {"search_index": "entity", "search_json": search_json}

            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)
            es_id = search_result.json()['data']['dataList'][0]
            # 更新ES实体
            update_para = {"update_index": 'entity',
                           "data_update_json": [{es_id: key_value_json}]}
            print("key_value_json", key_value_json, flush=True)
            update_result = requests.post(url + '/updatebyId', data=json.dumps(update_para), headers=header)

            # neo4j同步
            # update_node(entity.id, entity.name, entity.category_id)

            res = success_res(msg="修改成功")
        else:
            res = fail_res(msg='实体不存在')
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/delete_entity', methods=['POST'])
# @swag_from(delete_entity_dict)
def delete_entity():
    try:
        uuid = request.json.get('uuid', None)

        entity = Entity.query.filter_by(uuid=uuid, valid=1).first()
        if entity:
            # category_place = EntityCategory.query.filter_by(id=entity.category_id, valid=1).first()
            # if category_place.name == PLACE_BASE_NAME:
            #     res = fail_res(msg="地名库由专业团队维护,不能删除！")
            #     return jsonify(res)

            try:
                entity.valid = 0
                category_place = EntityCategory.query.filter_by(uuid=entity.category_uuid, valid=1).first()
                if category_place.name == PLACE_BASE_NAME:
                    doc_mark_place = DocMarkPlace.query.filter_by(place_uuid=entity.uuid, valid=1).all()
                    for place_item in doc_mark_place:
                        place_item.valid = 0
                else:
                    doc_mark_entity = DocMarkEntity.query.filter_by(entity_uuid=entity.uuid, valid=1).all()
                    for entity_item in doc_mark_entity:
                        entity_item.valid = 0
            except:
                print(uuid, 'not delete_done')

            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            search_json = {
                "uuid": {"type": "term", "value": str(uuid)}
            }
            es_id_para = {"search_index": "entity", "search_json": search_json}
            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)

            es_id = []
            try:
                if search_result.json()['data']['dataList']:
                    es_id = [search_result.json()['data']['dataList'][0]]
            except Exception as e:
                print("es /searchId 结果有误", search_result.text, str(e))
            delete_para = {"delete_index": "entity", "id_json": es_id}
            search_result = requests.post(url + '/deletebyId', data=json.dumps(delete_para), headers=header)
            # print(search_result.text)

            # <editor-fold desc="yc del entity">
            sync_yc_del_name(entity.name, entity.uuid, entity.get_yc_mark_category())
            if entity.synonyms:
                sync_yc_del_synonyms(entity.synonyms, entity.uuid, entity.get_yc_mark_category())
            # </editor-fold>

            # neo4j同步
            # delete_node(entity.id)

            # arango同步
            para = {
                "collection": "entity",
                "key": str(entity.uuid)
            }
            header = {"Content-Type": "application/json; charset=UTF-8"}
            url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/delete_data'
            data = json.dumps(para)
            result = requests.post(url=url, data=data, headers=header)

            res = success_res()
        else:
            res = fail_res(msg="实体不存在")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/delete_entity_by_ids', methods=['POST'])
# @swag_from(delete_entity_by_ids_dict)
def delete_entity_by_ids():
    try:
        uuids = request.json.get('uuids', [])
        if uuids:
            entity = db.session.query(Entity).filter(Entity.uuid.in_(uuids), Entity.valid == 1).all()
            valid_uuids = []
            # feedback = set()
            if entity:
                for uni_entity in entity:
                    try:
                        # category_place = EntityCategory.query.filter_by(id=uni_entity.category_id, valid=1).first()
                        # if category_place.name == PLACE_BASE_NAME:
                        #     feedback.add(PLACE_BASE_NAME)
                        # else:

                        # <editor-fold desc="yc del entity">
                        sync_yc_del_name(uni_entity.name, uni_entity.uuid, uni_entity.get_yc_mark_category())
                        if uni_entity.synonyms:
                            sync_yc_del_synonyms(uni_entity.synonyms, uni_entity.uuid,
                                                 uni_entity.get_yc_mark_category())
                        # </editor-fold>

                        valid_uuids.append(uni_entity.uuid)
                        uni_entity.valid = 0
                        category_place = EntityCategory.query.filter_by(uuid=uni_entity.category_uuid, valid=1).first()
                        if category_place.name == PLACE_BASE_NAME:
                            doc_mark_place = DocMarkPlace.query.filter_by(place_uuid=uni_entity.uuid, valid=1).all()
                            for place_item in doc_mark_place:
                                place_item.valid = 0
                        else:
                            doc_mark_entity = DocMarkEntity.query.filter_by(entity_uuid=uni_entity.uuid, valid=1).all()
                            for entity_item in doc_mark_entity:
                                entity_item.valid = 0
                        # feedback.add(category_place.name)

                        # arango同步
                        para = {
                            "collection": "entity",
                            "key": str(uni_entity.uuid)
                        }
                        header = {"Content-Type": "application/json; charset=UTF-8"}
                        url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/delete_data'
                        data = json.dumps(para)
                        result = requests.post(url=url, data=data, headers=header)

                        res = success_res()
                    except Exception as e:
                        res = fail_res(msg=str(e))
            else:
                res = fail_res(msg="对应实体不存在")

            # db.session.commit()

            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            for uuid in valid_uuids:
                search_json = {
                    'uuid': {'type': 'term', 'value': str(uuid)}}
                header_es = {"Content-Type": "application/json; charset=UTF-8"}
                es_id_para = {"search_index": "entity", "search_json": search_json}
                search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header_es)
                try:
                    es_id = [search_result.json()['data']['dataList'][0]]

                except:
                    es_id = []

                # es_ids.append(es_id)
                delete_para = {"delete_index": "entity", "id_json": es_id}
                delete_result = requests.post(url + '/deletebyId', data=json.dumps(delete_para), headers=header_es)
            # if len(feedback) == 1 and PLACE_BASE_NAME in feedback:
            #     res = success_res("删除项均在地名库中，由专业团队维护,不能删除！")
            # elif PLACE_BASE_NAME in feedback:
            #     res = success_res("非地名已成功删除，地名由于地名库由专业团队维护,不能删除！")
            # else:
            #     res = success_res("全部成功删除！")
        else:
            res = fail_res(msg="参数不能为空")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/add_synonyms', methods=['PUT'])
# @swag_from(add_synonyms_dict)
def add_synonyms():
    try:
        uuid = request.json.get('uuid', '')
        synonyms = request.json.get('synonyms', [])
        sync = request.json.get('sync', 1)

        entity = Entity.query.filter_by(uuid=uuid, valid=1).first()
        if entity.synonyms:
            synonyms.extend(entity.synonyms)

        if entity.name in synonyms:
            synonyms.remove(entity.name)
        entity.synonyms = synonyms

        db.session.commit()

        # 获得es对应实体

        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        header = {"Content-Type": "application/json; charset=UTF-8"}
        search_json = {
            "uuid": {"type": "term", "value": str(entity.uuid)}
        }
        es_id_para = {"search_index": "entity", "search_json": search_json}
        search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)
        es_id = search_result.json()['data']['dataList'][0]

        # 更新ES实体
        key_value_json = {'synonyms': entity.synonyms}
        inesert_para = {"update_index": 'entity',
                        "data_update_json": [{es_id: key_value_json}]}
        search_result = requests.post(url + '/updatebyId', params=json.dumps(inesert_para), headers=header)

        # <editor-fold desc="sync yc del synonyms">
        sync_yc_add_synonyms(synonyms, str(entity.uuid), str(entity.category_uuid), entity.get_yc_mark_category())
        # </editor-fold>

        res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/delete_synonyms', methods=['PUT'])
# @swag_from(delete_synonyms_dict)
def delete_synonyms():
    try:
        uuid = request.json.get('uuid', '')
        synonyms = request.json.get('synonyms', [])
        sync = request.json.get('sync', 1)
        entity = Entity.query.filter_by(uuid=uuid, valid=1).first()
        if entity:
            entity_synonyms = [item for item in entity.synonyms if item not in synonyms]
            if entity.name in entity_synonyms:
                entity_synonyms.remove(entity.name)

            entity.synonyms = entity_synonyms
            db.session.commit()
            # 获得es对应实体
            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            search_json = {
                "uuid": {"type": "term", "value": str(entity.uuid)}
            }
            es_id_para = {"search_index": "entity", "search_json": search_json}
            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)
            es_id = search_result.json()['data']['dataList'][0]
            # 更新ES实体
            key_value_json = {"synonyms": entity_synonyms}
            inesert_para = {"update_index": 'entity',
                            "data_update_json": [{es_id: key_value_json}]}
            search_result = requests.post(url + '/updatebyId', params=json.dumps(inesert_para), headers=header)

            # <editor-fold desc="sync yc del synonyms">
            sync_yc_del_synonyms(synonyms, entity.uuid, entity.get_yc_mark_category())
            # </editor-fold>
            res = success_res()
        else:
            res = fail_res(msg="该实体不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# <editor-fold desc="雨辰同步-实体增删改">
def sync_yc_add_name(name, entity_uuid, category_uuid, mark_category, longitude=None, latitude=None, sync=1):
    try:
        # 雨辰同步
        if sync and YC_ROOT_URL:
            header = {"Content-Type": "application/json; charset=UTF-8"}
            url = YC_ROOT_URL_PYTHON + "/api/redis/add"
            item = {
                "entity_id": entity_uuid,
                "name": name,
                "type": 1,  # 1主体；2别名
                "category_id": category_uuid
            }

            if longitude:
                item['lon'] = longitude
            if latitude:
                item['lat'] = latitude

            sync_yc_redis_data = {
                "entity_data": [item],
                "mark_category": mark_category
            }

            data = json.dumps(sync_yc_redis_data)
            yc_res = requests.post(url=url, data=data, headers=header)
    except Exception as e:
        print(str(e))


def sync_yc_add_synonyms(synonyms, entity_uuid, category_uuid, mark_category, longitude=None, latitude=None, sync=1):
    try:
        # 雨辰同步
        if sync and YC_ROOT_URL:
            header = {"Content-Type": "application/json; charset=UTF-8"}
            url = YC_ROOT_URL_PYTHON + "/api/redis/add"
            entity_data = []
            for synonym in synonyms:
                entity = Entity.query.filter(Entity.synonyms.has_key(synonym),
                                             Entity.category_uuid == category_uuid, Entity.valid == 1).first()
                item = {
                    "entity_id": str(entity_uuid),
                    "name": synonym,
                    "type": 2,  # 1主体；2别名
                    "category_id": str(category_uuid)
                }
                if longitude:
                    item['lon'] = longitude
                else:
                    item["lon"] = entity.longitude if entity else 0
                    print("lon", item["lon"])
                if latitude:
                    item['lat'] = latitude
                else:
                    item["lat"] = entity.latitude if entity else 0
                entity_data.append(item)

            sync_yc_redis_data = {
                "entity_data": entity_data,
                "mark_category": mark_category
            }
            data = json.dumps(sync_yc_redis_data)
            yc_res = requests.post(url=url, data=data, headers=header)
    except Exception as e:
        print(str(e))


def sync_yc_update_name(old_name, new_name, entity_uuid, mark_category, longitude=None, latitude=None,
                        sync=1):
    try:
        # 雨辰同步
        if sync and YC_ROOT_URL:
            yc_update_item = {
                "old_name": old_name,
                "new_name": new_name,
                "entity_id": str(entity_uuid),
                "type": 1  # 1主体；2别名
            }
            if longitude:
                yc_update_item['lon'] = longitude
            if latitude:
                yc_update_item['lat'] = latitude
            yc_update_data = {"entity_data": [yc_update_item],
                              "mark_category": mark_category}
            # 雨辰同步
            if sync and YC_ROOT_URL:
                header = {"Content-Type": "application/json; charset=UTF-8"}
                url = YC_ROOT_URL_PYTHON + "/api/redis/update"
                data = json.dumps(yc_update_data)
                yc_res = requests.post(url=url, data=data, headers=header)
    except Exception as e:
        print(str(e))


def sync_yc_update_category_id(entity_uuid, old_category_id, new_category_uuid, mark_category, longitude=None,
                               latitude=None,
                               sync=1):
    try:
        # 雨辰同步
        if sync and YC_ROOT_URL:
            for type in ["1", "2"]:
                yc_update_item = {"entity_id": str(entity_uuid),
                                  "category_id": str(new_category_uuid),
                                  "type": type}
                if longitude:
                    yc_update_item['lon'] = longitude
                if latitude:
                    yc_update_item['lat'] = latitude
                yc_update_data = {"entity_data": [yc_update_item],
                                  "mark_category": mark_category}
                # 雨辰同步
                if sync and YC_ROOT_URL:
                    header = {"Content-Type": "application/json; charset=UTF-8"}
                    url = YC_ROOT_URL_PYTHON + "/api/redis/update"
                    data = json.dumps(yc_update_data)
                    yc_res = requests.post(url=url, data=data, headers=header)
    except Exception as e:
        print(str(e))


def sync_yc_del_name(name, entity_uuid, mark_category, sync=1):
    try:
        if sync and YC_ROOT_URL:
            header = {"Content-Type": "application/json; charset=UTF-8"}
            url = YC_ROOT_URL_PYTHON + "/api/redis/del"
            data = {"entity_data": [{"name": name,
                                     "entity_id": str(entity_uuid)}],
                    "mark_category": mark_category}
            yc_res = requests.post(url=url, data=data, headers=header)
    except Exception as e:
        print(str(e))


def sync_yc_del_synonyms(del_synonyms, entity_uuid, mark_category, sync=1):
    try:
        # 雨辰同步
        if sync and YC_ROOT_URL:
            header = {"Content-Type": "application/json; charset=UTF-8"}
            url = YC_ROOT_URL_PYTHON + "/api/redis/del"
            sync_yc_redis_data = {"entity_data": [{"name": i,
                                                   "entity_id": str(entity_uuid)} for i in del_synonyms],
                                  "mark_category": mark_category}
            data = json.dumps(sync_yc_redis_data)
            yc_res = requests.post(url=url, data=data, headers=header)
    except Exception as e:
        print(str(e))


# </editor-fold>


# 获取某词语所指向实体（只返回id，name，category_id）
@blue_print.route('/get_linking_entity', methods=['GET'])
# @swag_from(get_linking_entity_dict)
def get_linking_entity():
    try:
        entity_name = request.args.get('search', '')
        category_uuid = request.args.get('category_uuid', None)
        entity = Entity.query.filter(
            and_(Entity.valid == 1, or_(Entity.name == entity_name, Entity.synonyms.has_key(entity_name))))

        if category_uuid:
            entity = entity.filter_by(category_uuid=category_uuid, valid=1)
        entity = entity.first()

        if entity:
            res = {'uuid': str(entity.uuid), 'name': entity.name, 'category': entity.category_name()}
        else:
            res = {'uuid': '-1', 'name': '', 'category': ''}
    except Exception as e:
        print(str(e))
        res = {'uuid': '-1', 'name': '', 'category': ''}
    return res


# 暂无使用，es数据库中模糊搜索
@blue_print.route('/get_top_list_es', methods=['GET'])
# @swag_from(get_top_list_es_dict)
def get_entity_list_es():
    try:
        entity_name = request.args.get('search', '')
        category_id = request.args.get('category_uuid', 0, type=int)
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        search_json = {"name": {"type": "text", "value": entity_name, "boost": 5},
                       'synonyms': {"type": "text", "value": entity_name, "boost": 5}}
        if category_id != 0:
            search_json['category_uuid'] = {"type": "term", "value": category_uuid}
        null = 'None'
        para = {"search_index": 'entity', "search_json": search_json}
        search_result = requests.get(url + '/searchCustom', params=para, headers={})
        res = [{'uuid': entity['_source']['uuid'],
                'name': entity['_source']['name'],
                'category': EntityCategory.get_category_name(entity['_source']['category_id'])
                } for entity in search_result.json()['data']['dataList']]
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res[:5])


# 模糊搜索实体分页展示
@blue_print.route('/get_search_panigation', methods=['GET'])
# @swag_from(get_search_panigation_dict)
def get_search_panigation():
    try:
        search = request.args.get('search', "")
        page_size = request.args.get('page_size', 10, type=int)
        cur_page = request.args.get('cur_page', 1, type=int)
        category_uuid = request.args.get('category_uuid', None)
        data, total_count = get_search_panigation_es(search=search, page_size=page_size, cur_page=cur_page,
                                                     category_uuid=category_uuid)
        res = {
            "data": data,
            "cur_page": cur_page,
            "page_size": page_size,
            "total_count": total_count
        }
    except Exception as e:
        print(str(e))
        res = {
            "data": [],
            "cur_page": 0,
            "page_size": 0,
            "total_count": 0
        }
    return jsonify(res)


def get_search_panigation_es(search='', page_size=10, cur_page=1, category_uuid=None):
    try:
        if category_uuid == EntityCategory.get_category_id(PLACE_BASE_NAME) and USE_PLACE_SERVER:
            data, total_count = get_place_from_base_server(page_size=page_size, cur_page=cur_page, search=search)
        else:
            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            if not search:
                search_json = {}
            else:
                search_json = {"name": {"type": "text", "value": search, "boost": 5},
                               "synonyms": {"type": "text", "value": search, "boost": 5}}

            if category_uuid:
                search_json['category_uuid'] = {"type": "term", "value": category_uuid}

            para = {"search_index": 'entity', "search_json": search_json, "pageSize": page_size,
                    "currentPage": cur_page}
            header = {"Content-Type": "application/json"}
            esurl = url + "/searchCustomPagination"
            search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
            # print(search_result.text)
            null = 'None'
            total_count = search_result.json()['data']['totalCount']
            data = [{'uuid': entity['_source'].get('uuid', None),
                     'name': entity['_source'].get('name', ""),
                     'props': entity['_source'].get('props', {}),
                     'synonyms': entity['_source'].get('synonyms', []),
                     'summary': entity['_source'].get('summary', ""),
                     'category': EntityCategory.get_category_name(entity['_source'].get('category_uuid', "")),
                     'category_uuid': entity['_source'].get('category_uuid', None),
                     "longitude": entity['_source'].get('longitude', []),
                     "latitude": entity['_source'].get('latitude', [])
                     } for entity in search_result.json()['data']['dataList']]
            # for entity in data:
            #     entity['props'] = {} if entity['props'] == "None" else eval(
            #         entity['props'])  # json.dumps(entity['props'].replace("\"",""),ensure_ascii= False)
            #     entity['synonyms'] = [] if entity['synonyms'] == "None" else eval(entity['synonyms'])

        res = data, total_count
    except Exception as e:
        print(str(e))
        res = [], 0
    return res


# 实体模糊搜索

@blue_print.route('/get_search_entity', methods=['GET'])
# @swag_from(get_search_dict)
def get_search_entity():
    try:
        search = request.args.get('search', "")
        # page_size = request.args.get('page_size', 10, type=int)
        # cur_page = request.args.get('cur_page', 1, type=int)
        category_uuid = request.args.get('category_uuid', None)
        data, total_count = get_search_es(search=search,
                                          category_uuid=category_uuid)
        res = {
            "data": data,
            "total_count": total_count
        }
    except Exception as e:
        print(str(e))
        res = {
            "data": [],
            "total_count": 0
        }
    return jsonify(res)


def get_search_es(search='', page_size=10, cur_page=1, category_id=0):
    try:
        if category_id == EntityCategory.get_category_id(PLACE_BASE_NAME) and USE_PLACE_SERVER:
            data, total_count = get_place_from_base_server(page_size=10000, cur_page=1, search=search)
        else:
            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            if not search:
                search_json = {}
            else:
                search_json = {"name": {"type": "text", "value": search, "boost": 5},
                               "synonyms": {"type": "text", "value": search, "boost": 5}}

            if category_id != 0:
                search_json['category_uuid'] = {"type": "term", "value": category_uuid}

            para = {"search_index": 'entity', "search_json": search_json, "pageSize": page_size,
                    "currentPage": cur_page}
            header = {"Content-Type": "application/json"}
            esurl = url + "/searchCustom"
            search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
            # print(search_result.text)
            null = 'None'
            total_count = search_result.json()['data']['totalCount']
            data = [{'uuid': entity['_source'].get('uuid', 0),
                     'name': entity['_source'].get('name', ""),
                     'props': entity['_source'].get('props', {}),
                     'synonyms': entity['_source'].get('synonyms', []),
                     'summary': entity['_source'].get('summary', ""),
                     'category': EntityCategory.get_category_name(entity['_source'].get('category_id', 0)),
                     "longitude": entity['_source'].get('longitude', []),
                     "latitude": entity['_source'].get('latitude', [])
                     } for entity in search_result.json()['data']['dataList']]
            # for entity in data:
            #     entity['props'] = {} if entity['props'] == "None" else eval(
            #         entity['props'])  # json.dumps(entity['props'].replace("\"",""),ensure_ascii= False)
            #     entity['synonyms'] = [] if entity['synonyms'] == "None" else eval(entity['synonyms'])

        res = data, total_count
    except Exception as e:
        print(str(e))
        res = [], 0
    return res


# 精准搜索
@blue_print.route('/get_entity_data_es', methods=['GET'])
# @swag_from(get_entity_data_es_dict)
def get_entity_data_es():
    # try:
    entity_name = request.args.get('search', '')
    url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
    search_json = {"name": {"type": "keyword", "value": [entity_name]}}
    para = {"search_index": 'entity', "search_json": search_json}
    search_result = requests.get(url + '/searchCustom', params=para, headers={})
    null = 'None'
    entity = search_result.json()['data']['dataList'][0]
    if entity:
        res = {'uuid': entity['_source']['uuid'], 'name': entity['_source']['name'],
               'synonyms': entity['_source']['synonyms'],
               'props': entity['_source']['props'],
               'summary': entity['_source']['summary'],
               'category': EntityCategory.get_category_name(entity['_source']['category_id'])}
    else:
        res = {'uuid': -1, 'name': '', 'synonyms': [], 'props': {}, 'summary': {},
               'category': ''}
    return jsonify(res)


# 获取实体信息
@blue_print.route('/get_entity_info', methods=['GET'])
# @swag_from(get_entity_info_dict)
def get_entity_info():
    try:
        uuid = request.args.get('uuid', None)
        entity = Entity.query.filter_by(uuid=uuid, valid=1).first()
        if entity:
            condition_object = []
            # 查询相关文档列表
            doc_mark_entities = DocMarkEntity.query.filter_by(entity_uuid=entity.uuid, valid=1).all()
            doc_uuids_by_entities = [i.doc_uuid for i in doc_mark_entities]
            doces = db.session.query(Document).filter(
                Document.uuid.in_(doc_uuids_by_entities), Document.valid == 1).order_by(
                Document.create_time.desc()).all()

            doc_list = [{
                "uuid": i.uuid,
                "name": i.name,
                "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S") if i.create_time else None,
                "create_username": Customer.get_username_by_id(i.create_by_uuid),
                "status": i.get_status_name()
            } for i in doces]

            # 查询相关事件列表
            conditions = [DocMarkEvent.valid == 1]
            doc_mark_entity_ids = [str(i.uuid) for i in doc_mark_entities]
            for doc_mark_entity_id in doc_mark_entity_ids:
                condition_object.append(or_(DocMarkEvent.event_subject.op('@>')([doc_mark_entity_id]),
                                            DocMarkEvent.event_object.op('@>')([doc_mark_entity_id])))

            condition_object = tuple(condition_object)
            doc_mark_events = []
            if condition_object:
                doc_mark_events = DocMarkEvent.query.filter(and_(*conditions), or_(*condition_object)).order_by(
                    DocMarkEvent.create_time.desc()).all()

            # 获取事件时间
            for doc_mark_event in doc_mark_events:
                event_datetime = []
                for event_time_uuid in doc_mark_event.event_time:
                    event_time_tag = DocMarkTimeTag.query.filter_by(uuid=event_time_uuid, valid=1).first()
                    if event_time_tag:
                        if event_time_tag.format_date:
                            event_datetime.append(event_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S'))

            doc_mark_event_list = [{
                "uuid": i.uuid,
                # "event_subject": i.event_subject,
                # "event_object": i.event_object,
                "datetime": event_datetime,
                "title": i.title
            } for i in doc_mark_events]

            res = {'uuid': str(entity.uuid), 'name': entity.name,
                   'synonyms': entity.synonyms if entity.synonyms else [],
                   'props': entity.props if entity.props else {},
                   'category_uuid': entity.category_uuid,
                   'category': entity.category_name(),
                   'summary': entity.summary if entity.summary else '',
                   'summary_phase': entity.summary.split('\n') if entity.summary else '',
                   'longitude': entity.longitude,
                   'latitude': entity.latitude,
                   "doc_list": doc_list,
                   "doc_mark_event_list": doc_mark_event_list
                   }
        else:
            res = {'uuid': '', 'name': '', 'synonyms': [], 'props': {}, 'category_uuid': "-1", 'category': '',
                   'longitude': None, 'latitude': None}

    except Exception as e:
        print(str(e))
        res = {'uuid': "-1", 'name': '', 'synonyms': [], 'props': {}, 'category_uuid': "-1", 'category': '',
               'longitude': None,
               'latitude': None}
    return jsonify(res)


# 获取实体信息  yc独用
@blue_print.route('/get_entities_info', methods=['POST'])
# @swag_from(get_entities_info)
def get_entities_info():
    try:
        uuids = request.json.get('uuids', [])
        entities = Entity.query.filter(Entity.uuid.in_(uuids)).all()
        res = success_res(data=[{'uuid': str(i.uuid),
                                 'name': i.name,
                                 'synonyms': i.synonyms if i.synonyms else [],
                                 'category_uuid': i.category_uuid,
                                 'category': i.category_name(),
                                 'longitude': i.longitude,
                                 'latitude': i.latitude} for i in entities])
    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


# 获取某词语所有信息
@blue_print.route('/get_entity_data', methods=['GET'])
# @swag_from(get_entity_data_dict)
def get_entity_data():
    try:
        search = request.args.get('search', '')
        entity = Entity.query.filter_by(name=search, valid=1).first()
        if entity:
            res = {'uuid': str(entity.uuid), 'name': entity.name, 'synonyms': entity.synonyms,
                   'props': entity.props, 'category': entity.category_name()}
        else:
            res = {'uuid': '-1', 'name': '', 'synonyms': [], 'props': {},
                   'category': ''}
    except Exception as e:
        print(str(e))
        res = {'uuid': -1, 'name': '', 'synonyms': [], 'props': {},
               'category': ''}
    return jsonify(res)


# 获取某词语的5个实体推荐
@blue_print.route('/get_top_list', methods=['GET'])
# @swag_from(get_top_list_dict)
def get_top_list():
    try:
        search = request.args.get('search', '')
        category_uuid = request.args.get('category_uuid', None)
        data, _ = get_search_panigation_es(search=search, category_uuid=category_uuid, page_size=5, cur_page=1)
        res = data
    except Exception as e:
        print(str(e))
        res = []

    return jsonify(res)


# 模糊搜索分页展示pg
@blue_print.route('/get_search_panigation_pg', methods=['GET'])
# @swag_from(get_search_panigation_pg_dict)
def get_search_panigation_pg():
    try:
        entity_name = request.args.get('search', '')
        page_size = request.args.get('page_size', 10, type=int)
        cur_page = request.args.get('cur_page', 1, type=int)

        entity_list = Entity.query.filter(and_(Entity.valid == 1, or_(Entity.name.like("%" + entity_name + "%"),
                                                                      Entity.synonyms.has_key(entity_name)))
                                          ).all()

        entity_uuids = [i.uuid for i in entity_list]

        search_cuts = analyse.extract_tags(entity_name, topK=5)
        conditions = [Entity.name.like("%" + i + "%") for i in search_cuts]
        conditions.extend([Entity.synonyms.has_key(i) for i in search_cuts])

        conditions = tuple(conditions)
        ex_list = Entity.query.filter(and_(or_(*conditions), Entity.valid == 1, ~Entity.uuid.in_(entity_uuids))).all()
        entity_list.extend(ex_list)

        total_like_list = [{'uuid': str(entity.uuid),
                            'name': entity.name,
                            'category': entity.category_name()
                            } for entity in entity_list]

        res = total_like_list[(cur_page - 1) * page_size:cur_page * page_size]
    except Exception as e:
        print(str(e))
        res = []

    return jsonify(res)


# 下载excel批量导入实体
@blue_print.route('download_entity_excel_example', methods=['GET'])
# @swag_from(download_entity_excel_example_dict)
def download_entity_excel_example():
    return '/static/{0}'.format("shitidaorumuban.xlsx")


# excel批量导入实体
@blue_print.route('import_entity_excel', methods=['POST'])
# @swag_from(import_entity_excel_dict)
def import_entity_excel():
    file_obj = request.files.get('file', None)
    try:
        filename = secure_filename(''.join(lazy_pinyin(file_obj.filename)))
        save_filename = "{0}{1}{2}".format(os.path.splitext(filename)[0],
                                           datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                                           os.path.splitext(filename)[1])
        file_savepath = os.path.join(os.getcwd(), 'static', save_filename)
        file_obj.save(file_savepath)

        data = xlrd.open_workbook(file_savepath)
        table = data.sheet_by_index(0)

        # 实体名称	实体类型    实体简介    实体别名    实体属性
        for row_index in range(1, table.nrows):
            try:
                row_value = table.row_values(row_index)
                ex_name = row_value[0].strip()
                category_uuid = EntityCategory.get_category_id(row_value[1].strip())

                # 地名数据不得导入
                if category_uuid != EntityCategory.get_category_id(PLACE_BASE_NAME):
                    ex_summary = row_value[2].strip()
                    # 解析别名
                    ex_synonyms = []
                    for synonym_str in row_value[3].strip().split('\n'):
                        if synonym_str:
                            ex_synonyms.append(synonym_str)
                    # 解析属性
                    ex_props = {}
                    for prop_str in row_value[4].strip().split('\n'):
                        if re.match('(.*)：(.*)', prop_str):
                            key, value = re.match('(.+?)：(.*)', prop_str).groups()
                            ex_props[key] = value

                    entity = Entity.query.filter(or_(Entity.name == ex_name,
                                                     Entity.synonyms.has_key(ex_name),
                                                     Entity.name.in_(ex_synonyms),
                                                     Entity.synonyms.contains(ex_props)
                                                     )).first()

                    if entity:
                        # <editor-fold desc="yc update name">
                        if entity.name != ex_name:
                            sync_yc_update_name(entity.name, ex_name, entity.uuid, entity.get_yc_mark_category())
                        # </editor-fold>

                        # <editor-fold desc="yc update category_id">
                        if category_uuid != entity.category_uuid:
                            sync_yc_update_category_id(entity.uuid, entity.category_uuid, category_uuid,
                                                       entity.get_yc_mark_category())
                        # </editor-fold>

                        # <editor-fold desc="yc add & del synonyms">
                        if isinstance(ex_synonyms, list):
                            add_synonyms = list(set(ex_synonyms).difference(set(entity.synonyms)))
                            remove_synonyms = list(set(entity.synonyms).difference(set(ex_synonyms)))

                            sync_yc_add_synonyms(add_synonyms, entity.uuid, entity.category_uuid,
                                                 entity.get_yc_mark_category())
                            if remove_synonyms:
                                # 删除别名
                                sync_yc_del_synonyms(remove_synonyms, entity.uuid, entity.get_yc_mark_category())
                        # </editor-fold>

                        entity.name = ex_name
                        entity.props = ex_props
                        entity.synonyms = ex_synonyms
                        entity.summary = ex_summary
                        entity.category_uuid = category_uuid
                        entity.valid = 1

                        # es 插入操作
                        data_insert_json = [{
                            "uuid": str(entity.uuid),
                            'name': ex_name,
                            'category_uuid': str(category_uuid),
                            'summary': ex_summary,
                            'props': ex_props,
                            'synonyms': ex_synonyms
                        }]
                        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'

                        header = {"Content-Type": "application/json; charset=UTF-8"}

                        # print(entity)
                        inesert_para = {"update_index": 'entity', "data_update_json": [{entity.uuid: data_insert_json}]}
                        search_result = requests.post(url + '/updatebyId', params=json.dumps(inesert_para),
                                                      headers=header)
                        # print(search_result.text, flush=True)

                    else:
                        entity = Entity(uuid=uuid.uuid1(), name=ex_name, props=ex_props, synonyms=ex_synonyms,
                                        category_uuid=category_uuid,
                                        valid=1)
                        db.session.add(entity)
                        # db.session.commit()

                        # es 插入操作
                        data_insert_json = [{
                            'name': ex_name,
                            'category_uuid': str(category_uuid),
                            'summary': ex_summary,
                            'props': ex_props,
                            'synonyms': ex_synonyms,
                            'uuid': str(entity.uuid)
                        }]
                        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'

                        header = {"Content-Type": "application/json; charset=UTF-8"}

                        # print(entity)
                        para = {"data_insert_index": "entity", "data_insert_json": data_insert_json}
                        search_result = requests.post(url + '/dataInsert', data=json.dumps(para), headers=header)
                        # print(search_result.text, flush=True)

                        # <editor-fold desc="yc insert name & synonyms">
                        sync_yc_add_name(ex_name, str(entity.uuid), str(entity.category_uuid),
                                         entity.get_yc_mark_category())
                        sync_yc_add_synonyms(ex_synonyms, str(entity.uuid), str(entity.category_uuid),
                                             entity.get_yc_mark_category())
                        # </editor-fold>

            except Exception as e:
                print(str(e))
                continue
        db.session.commit()

    except:
        db.session.rollback()

    res = success_res()
    return jsonify(res)


# 不做实体与数据库对齐和去重等操作，直接插入，excel批量导入实体
@blue_print.route('import_entity_excel_straightly', methods=['POST'])
# @swag_from(import_entity_excel_straightly_dict)
def import_entity_excel_straightly():
    file_obj = request.files.get('file', None)
    try:
        filename = secure_filename(''.join(lazy_pinyin(file_obj.filename)))
        save_filename = "{0}{1}{2}".format(os.path.splitext(filename)[0],
                                           datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                                           os.path.splitext(filename)[1])
        file_savepath = os.path.join(os.getcwd(), 'static', save_filename)
        file_obj.save(file_savepath)
        data = xlrd.open_workbook(file_savepath)
        table = data.sheet_by_index(0)

        entity_list = []
        # 实体名称	实体类型    实体简介    实体别名    实体属性
        for row_index in range(1, table.nrows):
            try:
                row_value = table.row_values(row_index)
                ex_name = row_value[0].strip()
                print("here is arrived", flush=True)
                category_uuid = str(EntityCategory.get_category_id(row_value[1].strip()))

                ex_summary = row_value[2].strip()
                # 解析别名
                ex_synonyms = []
                for synonym_str in row_value[3].strip().split('\n'):
                    if synonym_str:
                        ex_synonyms.append(synonym_str)
                # 解析属性
                ex_props = {}
                for prop_str in row_value[4].strip().split(','):
                    if re.match('(.*):(.*)', prop_str):
                        key, value = re.match('(.+?):(.*)', prop_str).groups()
                        ex_props[key] = value

                entity = {"name": ex_name, "props": ex_props, "synonyms": ex_synonyms,
                          "category_uuid": str(category_uuid),
                          "summary": ex_summary, "valid": 1}

                entity_list.append(entity)

            except Exception as e:
                print("excel error: ", str(e))
                continue

        w_dic = {"RECORDS": entity_list}
        with open("entity_xf.json", 'w', encoding="utf-8") as f:
            f.write(json.dumps(w_dic))

    except Exception as e:
        print(str(e))

    res = success_res()
    return jsonify(res)


def GetColumnTitle(sheet):
    col_dict = {}
    for i in range(sheet.ncols):
        col_dict[sheet.cell_value(0, i).strip()] = i
    return col_dict


def SaveOneFile(filepath, file_name):
    # print(filepath)
    # file_name = filepath.split("\\")[-1]
    workbook = xlrd.open_workbook(filepath)
    sheet = workbook.sheet_by_index(0)  # 只读第一个$sheet，没遍历所有！
    # 如第一行有列名，则按列名取数
    col_dict = GetColumnTitle(sheet)
    print("col_dict", col_dict)
    if bool(col_dict):
        number_of_rows = sheet.nrows
        if file_name == "国际和地区组织 — 中华人民共和国外交部.xlsx":
            try:
                category_uuid = EntityCategory.get_category_id('机构')
                name_summary_dict = {}
                for row in range(1, number_of_rows):
                    name, synonym, summary = sheet.cell(row, col_dict["名称"]).value, sheet.cell(row, col_dict[
                        "英文名称"]).value, sheet.cell(row, col_dict["概况"]).value
                    if name in name_summary_dict:
                        name_summary_dict[name]['summary'].append(summary)
                        name_summary_dict[name]['synonyms'].append(synonym)
                    else:
                        name_summary_dict[name] = {"summary": [summary], "synonyms": [synonym]}
                for name, info_dict in name_summary_dict.items():
                    insert_json = {
                        "name": name,
                        "category_uuid": str(category_uuid),
                        "summary": '\n'.join(info_dict['summary']),
                        "synonyms": list(set(info_dict['synonyms']))}

                    insert_entity_to_pg_and_es(insert_json.get("name", ""), insert_json.get("category_uuid", None),
                                               insert_json.get("summary", ""),
                                               insert_json.get("props", None), insert_json.get("synonyms", []))
            except Exception as e:
                print(str(e))

        elif file_name == "国家 — 中华人民共和国外交部.xlsx":
            try:
                category_uuid = EntityCategory.get_category_id(file_name.split(" — ")[0])
                name_summary_dict = {}
                for row in range(1, number_of_rows):
                    name, summary = sheet.cell(row, col_dict["国家"]).value, sheet.cell(row, col_dict["概况"]).value
                    if name in name_summary_dict:
                        name_summary_dict[name].append(summary)
                    else:
                        name_summary_dict[name] = [summary]
                for name, summary_list in name_summary_dict.items():
                    insert_json = {
                        "name": name,
                        "category_uuid": str(category_uuid),
                        "summary": '\n'.join(summary_list)}

                    insert_entity_to_pg_and_es(insert_json.get("name", ""), insert_json.get("category_uuid", None),
                                               insert_json.get("summary", ""),
                                               insert_json.get("props", None), insert_json.get("synonyms", []))
            except Exception as e:
                print(str(e))

        elif file_name == "机构-台外军机构.xlsx":
            try:
                category_uuid = EntityCategory.get_category_id(file_name.split("-")[0])
                for row in range(1, number_of_rows):
                    print("{}/{}".format(row, number_of_rows))
                    insert_json = {
                        "name": sheet.cell(row, col_dict["名称"]).value,
                        "category_uuid": str(category_uuid),
                        "summary": sheet.cell(row, col_dict["属性"]).value}
                    # print(insert_json)
                    insert_entity_to_pg_and_es(insert_json.get("name", ""), insert_json.get("category_uuid", None),
                                               insert_json.get("summary", ""),
                                               insert_json.get("props", None), insert_json.get("synonyms", []))
            except Exception as e:
                print(str(e))

        elif file_name == "人员-关岗.xlsx":
            try:
                category_uuid = EntityCategory.get_category_id(file_name.split("-")[0])
                for row in range(1, number_of_rows):
                    props_json = {"身份证号码": sheet.cell(row, col_dict["身份证号码"]).value,
                                  "性别": sheet.cell(row, col_dict["性别"]).value,
                                  "政治面貌": sheet.cell(row, col_dict["政治面貌"]).value,
                                  "军衔": sheet.cell(row, col_dict["军衔"]).value,
                                  "文化程度": sheet.cell(row, col_dict["文化程度"]).value,
                                  "职务级别": sheet.cell(row, col_dict["职务级别"]).value,
                                  "第一学历": sheet.cell(row, col_dict["第一学历"]).value,
                                  "籍贯": sheet.cell(row, col_dict["籍贯"]).value,
                                  "入伍时间": sheet.cell(row, col_dict["入伍时间"]).value,
                                  "部队内码": sheet.cell(row, col_dict["部队内码"]).value,
                                  "院校培训": sheet.cell(row, col_dict["院校培训"]).value,
                                  "简述": sheet.cell(row, col_dict["简述"]).value,
                                  "职务": sheet.cell(row, col_dict["职务"]).value,
                                  "任现职时间": sheet.cell(row, col_dict["任现职时间"]).value,
                                  "现岗时间": sheet.cell(row, col_dict["现岗时间"]).value,
                                  "任职经历": sheet.cell(row, col_dict["任职经历"]).value}

                    insert_json = {
                        "name": sheet.cell(row, col_dict["姓名"]).value,
                        "category_uuid": category_uuid,
                        "props": props_json
                    }
                    # print(insert_json)
                    insert_entity_to_pg_and_es(insert_json.get("name", ""), insert_json.get("category_uuid", None),
                                               insert_json.get("summary", ""),
                                               insert_json.get("props", None), insert_json.get("synonyms", []))

            except Exception as e:
                print(str(e))

        elif file_name == "设施-仓库工程.xlsx":
            try:
                category_uuid = EntityCategory.get_category_id("工程")
                for row in range(1, number_of_rows):
                    print("设施-仓库工程: {}/{}".format(row, number_of_rows))
                    props_json = {"扩展地名": sheet.cell(row, col_dict["扩展地名"]).value,
                                  "仓库级别": sheet.cell(row, col_dict["仓库级别"]).value,
                                  "储存性质": sheet.cell(row, col_dict["储存性质"]).value,
                                  "启用时间": sheet.cell(row, col_dict["启用时间"]).value,
                                  "容量": sheet.cell(row, col_dict["容量"]).value,
                                  "占地面积": sheet.cell(row, col_dict["占地面积"]).value,
                                  "占用率": sheet.cell(row, col_dict["占用率"]).value}

                    insert_json = {
                        "name": sheet.cell(row, col_dict["工程名称"]).value,
                        "category_uuid": str(category_uuid),
                        "props": props_json
                    }
                    insert_entity_to_pg_and_es(insert_json.get("name", ""), insert_json.get("category_uuid", None),
                                               insert_json.get("summary", ""),
                                               insert_json.get("props", None), insert_json.get("synonyms", []))
            except Exception as e:
                print(str(e))

        elif file_name == "设施-机场.xlsx":
            try:
                category_uuid = EntityCategory.get_category_id("工程")
                for row in range(1, number_of_rows):
                    print("设施-机场: {}/{}".format(row, number_of_rows))
                    props_json = {
                        "地名": sheet.cell(row, col_dict["地名"]).value,
                        "纬度": sheet.cell(row, col_dict["纬度"]).value,
                        "经度": sheet.cell(row, col_dict["经度"]).value,
                        "机场类别": sheet.cell(row, col_dict["机场类别"]).value,
                        "机场等级": sheet.cell(row, col_dict["机场等级"]).value,
                        "导航方式": sheet.cell(row, col_dict["导航方式"]).value,
                        "军事设施使用性质": sheet.cell(row, col_dict["军事设施使用性质"]).value,
                        "道面结构材料": sheet.cell(row, col_dict["道面结构材料"]).value,
                        "场站级别": sheet.cell(row, col_dict["场站级别"]).value,
                        "夜航灯光方式": sheet.cell(row, col_dict["夜航灯光方式"]).value,
                        "主跑道长": sheet.cell(row, col_dict["主跑道长"]).value,
                        "跑道方向": sheet.cell(row, col_dict["跑道方向"]).value,
                        "标高": sheet.cell(row, col_dict["标高"]).value,
                        "配套情况": sheet.cell(row, col_dict["配套情况"]).value,
                        "单机掩蔽库数量": sheet.cell(row, col_dict["单机掩蔽库数量"]).value,
                        "油库容量": sheet.cell(row, col_dict["油库容量"]).value,
                        "营房总面积": sheet.cell(row, col_dict["营房总面积"]).value,
                        "占地面积": sheet.cell(row, col_dict["占地面积"]).value
                    }

                    insert_json = {
                        "name": sheet.cell(row, col_dict["工程名称"]).value,
                        "category_uuid": str(category_uuid),
                        "props": props_json,
                        "summary": sheet.cell(row, col_dict["简述"]).value
                    }
                    insert_entity_to_pg_and_es(insert_json.get("name", ""), insert_json.get("category_uuid", None),
                                               insert_json.get("summary", ""),
                                               insert_json.get("props", None), insert_json.get("synonyms", []))
            except Exception as e:
                print(str(e))

        elif file_name == "设施-战备工程.xlsx":
            try:
                category_uuid = EntityCategory.get_category_id("工程")
                for row in range(1, number_of_rows):
                    print("设施-战备工程: {}/{}".format(row, number_of_rows))
                    props_json = {
                        "工程分类": sheet.cell(row, col_dict["工程分类"]).value,
                        "所在位置": sheet.cell(row, col_dict["所在位置"]).value,
                        "军标库号": sheet.cell(row, col_dict["军标库号"]).value,
                        "质量描述": sheet.cell(row, col_dict["质量描述"]).value,
                        "竣工时间": sheet.cell(row, col_dict["竣工时间"]).value,
                        "保护区类型": sheet.cell(row, col_dict["保护区类型"]).value,
                        "所在防护责任区": sheet.cell(row, col_dict["所在防护责任区"]).value,
                        "数据来源": sheet.cell(row, col_dict["数据来源"]).value,
                        "数据时间": sheet.cell(row, col_dict["数据时间"]).value
                    }

                    insert_json = {
                        "name": sheet.cell(row, col_dict["工程名称"]).value,
                        "category_uuid": str(category_uuid),
                        "props": props_json,
                        "summary": ""
                    }
                    insert_entity_to_pg_and_es(insert_json.get("name", ""), insert_json.get("category_uuid", None),
                                               insert_json.get("summary", ""),
                                               insert_json.get("props", None), insert_json.get("synonyms", []))
            except Exception as e:
                print(str(e))

        elif file_name == "装备-台外军装备.xlsx":
            try:
                category_uuid = EntityCategory.get_category_id(file_name.split("-")[0])
                for row in range(1, number_of_rows):
                    print("装备-台外军装备: {}/{}".format(row, number_of_rows))
                    props_json = {
                        "装备分类": sheet.cell(row, col_dict["装备分类"]).value,
                        "国家": sheet.cell(row, col_dict["国家"]).value}
                    insert_json = {
                        "name": sheet.cell(row, col_dict["装备名称"]).value,
                        "category_uuid": str(category_uuid),
                        "props": props_json
                    }
                    insert_entity_to_pg_and_es(insert_json.get("name", ""), insert_json.get("category_uuid", None),
                                               insert_json.get("summary", ""),
                                               insert_json.get("props", None), insert_json.get("synonyms", []))
            except Exception as e:
                print(str(e))

        # 横表
        elif file_name == "装备-我军装备.xlsx":
            insert_json = {}
            props_json = {}
            mc_value = sheet.cell(1, 1).value
            try:
                category_uuid = EntityCategory.get_category_id(file_name.split("-")[0])
                insert_json["category_uuid"] = str(category_uuid)
                for row in range(1, number_of_rows):
                    print("装备-我军装备: {}/{}".format(row, number_of_rows))
                    if sheet.cell(row, 1).value == mc_value:
                        if sheet.cell(row, 2).value == "装备名称":
                            insert_json["name"] = sheet.cell(row, 3).value
                        elif sheet.cell(row, 2).value == "装备别名":
                            insert_json["synonyms"] = [sheet.cell(row, 3).value]
                        else:
                            props_json[str(sheet.cell(row, 2).value)] = sheet.cell(row, 3).value
                            insert_json["props"] = json.dumps(props_json, ensure_ascii=False)
                        if row == number_of_rows - 1 or sheet.cell(row + 1, 1).value != mc_value:
                            insert_entity_to_pg_and_es(insert_json.get("name", ""),
                                                       insert_json.get("category_uuid", None),
                                                       insert_json.get("summary", ""),
                                                       insert_json.get("props", None), insert_json.get("synonyms", []))

                    else:
                        mc_value = sheet.cell(row, 1).value
                        if sheet.cell(row, 2).value == "装备名称":
                            insert_json["name"] = sheet.cell(row, 3).value

            except Exception as e:
                print(str(e))

        elif file_name == "组织-部队.xlsx":
            try:
                category_uuid = EntityCategory.get_category_id('部队')
                for row in range(1, number_of_rows):
                    print("组织-部队: {}/{}".format(row, number_of_rows))
                    props_json = {
                        "部队内码": sheet.cell(row, col_dict["部队内码"]).value,
                        "代号": sheet.cell(row, col_dict["代号"]).value,
                        "驻地": sheet.cell(row, col_dict["部队内码"]).value,
                        "经度": sheet.cell(row, col_dict["部队内码"]).value,
                        "纬度": sheet.cell(row, col_dict["代号"]).value,
                        "高程": sheet.cell(row, col_dict["高程"]).value,
                        "类别": sheet.cell(row, col_dict["类别"]).value,
                        "级别": sheet.cell(row, col_dict["级别"]).value,
                        "建制": sheet.cell(row, col_dict["建制"]).value
                    }
                    insert_json = {
                        "name": sheet.cell(row, col_dict["部队番号"]).value,
                        "category_uuid": str(category_uuid),
                        "props": props_json,
                        "synonyms": [sheet.cell(row, col_dict["部队简称"]).value]
                    }
                    insert_entity_to_pg_and_es(insert_json.get("name", ""),
                                               insert_json.get("category_uuid", None),
                                               insert_json.get("summary", ""),
                                               insert_json.get("props", None), insert_json.get("synonyms", []))
            except Exception as e:
                print(str(e))

        elif file_name == "组织-台外军部队.xlsx":
            try:
                category_uuid = EntityCategory.get_category_id('部队')
                for row in range(1, number_of_rows):
                    print("组织-台外军部队: {}/{}".format(row, number_of_rows))
                    insert_json = {
                        "name": sheet.cell(row, col_dict["名称"]).value,
                        "category_uuid": str(category_uuid),
                        "summary": sheet.cell(row, col_dict["简述"]).value
                    }
                    insert_entity_to_pg_and_es(insert_json.get("name", ""),
                                               insert_json.get("category_uuid", None),
                                               insert_json.get("summary", ""),
                                               insert_json.get("props", None), insert_json.get("synonyms", []))
            except Exception as e:
                print(str(e))

        else:
            print("没有匹配文件模板:", file_name)

    else:
        pass


@blue_print.route('import_excel_to_pg', methods=['POST'])
def import_excel_to_pg():
    try:
        file_list = request.files.getlist('file', None)
        for file_obj in file_list:
            # print('中国')
            # print('file_obj.__dict__', file_obj.__dict__)
            # zip_file = zipfile.ZipFile(file_obj)
            # print('zip_file.namelist()', zip_file.namelist())
            # import chardet
            # for i in zip_file.namelist():
            #     print(type(i))
            #     print(type(i.encode()))
            #     print(chardet.detect(i.encode()))
            #     print(type(i.encode().decode('gb2312')))
            # file_obj_files = file_obj.filename+"_files/"
            # if os.path.isdir(file_obj_files):
            #     pass
            # else:
            #     os.mkdir(file_obj_files)
            # for names in zip_file.namelist():
            #     zip_file.extract(names, file_obj_files)
            # zip_file.close()

            path_filename = file_obj.filename
            print(path_filename)
            path = path_filename.split("/")
            # filename = secure_filename(''.join(lazy_pinyin(path[-1])))
            # save_filename = "{0}{1}{2}".format(os.path.splitext(filename)[0],
            #                                    datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
            #                                    os.path.splitext(filename)[1]).lower()
            path_filename = secure_filename(''.join(lazy_pinyin(path_filename)))
            file_savepath = os.path.join(os.getcwd(), 'static', path_filename)
            print(file_savepath)
            file_obj.save(file_savepath)
            SaveOneFile(file_savepath, file_obj.filename)
        res = success_res()
    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


@blue_print.route('post_json_data_path_to_yc', methods=['GET', 'POST'])
def post_json_data_path_to_yc():
    try:
        entity_category_1 = EntityCategory.query.filter_by(valid=1, type=1).all()
        entity_category_2 = EntityCategory.query.filter_by(valid=1, type=2).all()
        entity_category1_ids = [str(i.uuid) for i in entity_category_1]
        entity_category2_ids = [str(i.uuid) for i in entity_category_2]
        category_uuid_of_place = EntityCategory.query.filter_by(name=PLACE_BASE_NAME, valid=1).first()
        if category_uuid_of_place:
            category_uuid_of_place = category_uuid_of_place.uuid
            if entity_category1_ids:
                entity_list = Entity.query.filter(Entity.valid == 1, Entity.category_uuid != category_uuid_of_place,
                                                  Entity.category_uuid.in_(entity_category1_ids)).all()
            place_list = Entity.query.filter_by(valid=1, category_uuid=category_uuid_of_place).all()
            if entity_category2_ids:
                concept_list = Entity.query.filter(Entity.valid == 1,
                                                   Entity.category_uuid.in_(entity_category2_ids)).all()

        root_path = os.getcwd()
        yc_entity_path = os.path.join("/static", "entity.json")
        entity_json_save_path = os.path.join(root_path, "static", "entity.json")
        with open(entity_json_save_path, 'w', encoding='utf-8') as f:
            entity_records = [{
                "uuid": str(entity.uuid),
                "name": entity.name,
                "synonyms": entity.synonyms,
                "category_uuid": str(entity.category_uuid)} for entity in entity_list]
            dict_entity = {"RECORDS": entity_records}
            f.write(json.dumps(dict_entity))

        yc_place_path = os.path.join("/static", "place.json")
        place_json_save_path = os.path.join(root_path, "static", "place.json")
        with open(place_json_save_path, 'w', encoding='utf-8') as f:
            place_records = [{
                "uuid": str(place.uuid),
                "name": place.name,
                "synonyms": place.synonyms,
                "props": place.props,
                "category_uuid": str(place.category_uuid),
                "summary": place.summary,
                "valid": place.valid,
                "longitude": place.longitude,
                "latitude": place.latitude} for place in place_list]
            dict_place = {"RECORDS": place_records}
            f.write(json.dumps(dict_place))

        yc_concept_path = os.path.join("/static", "concept.json")
        concept_json_save_path = os.path.join(root_path, "static", "concept.json")
        with open(concept_json_save_path, 'w', encoding='utf-8') as f:
            concept_records = [{
                "uuid": str(concept.uuid),
                "name": concept.name,
                "synonyms": concept.synonyms,
                "category_uuid": str(concept.category_uuid)} for concept in concept_list]
            dict_concept = {"RECORDS": concept_records}
            f.write(json.dumps(dict_concept))

        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = YC_ROOT_URL + '/entity/init'
        body = {
            "entityPath": yc_entity_path,
            "placePath": yc_place_path,
            "conceptPath": yc_concept_path
        }
        data = json.dumps(body)
        print(data)
        yc_res = requests.post(url=url, data=data, headers=header)
        print("yc_res.status_code", yc_res.status_code)
        res = success_res()

    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


def insert_entity_to_pg_and_es(name, category_uuid, summary, props={}, synonyms=[]):
    try:

        category = EntityCategory.query.filter_by(uuid=category_uuid, valid=1).first()
        if not category:
            res = fail_res(msg="实体类型不存在，添加失败！")
            return jsonify(res)

        # if category.name == PLACE_BASE_NAME:
        #     res = fail_res(msg="地名库由专业团队维护,不能添加！")
        #     return jsonify(res)
        if not name:
            res = fail_res(msg="实体名称不能为空，添加失败！")
            return jsonify(res)

        entity = Entity.query.filter(Entity.name == name, Entity.valid == 1,
                                     Entity.category_uuid == category_uuid).first()

        if name in synonyms:
            synonyms.remove(name)

        if entity:
            entity.summary = summary
            entity.props = props
            entity.synonyms = synonyms
            db.session.commit()

            key_value_json = {"uuid": str(entity.uuid)}

            # es 更新操作
            if category_uuid:
                key_value_json["category_uuid"] = category_uuid
            if summary:
                key_value_json["summary"] = summary

            key_value_json["props"] = props if props else {}
            if synonyms:
                key_value_json["synonyms"] = synonyms

            # 获得es对应实体
            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            search_json = {
                "uuid": {"type": "term", "value": str(entity.uuid)}
            }
            es_id_para = {"search_index": "entity", "search_json": search_json}
            '''
            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)

            if search_result.json()['data']['dataList']:
                es_id = search_result.json()['data']['dataList'][0]
                # 更新ES实体
                update_para = {"update_index": 'entity',
                            "data_update_json": [{es_id: key_value_json}]}
                # print("key_value_json", key_value_json, flush=True)
                update_result = requests.post(url + '/updatebyId', data=json.dumps(update_para), headers=header)
            else:
                print("es中丢失pg目标")
                # data_insert_json = [key_value_json]
                # url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'

                # header = {"Content-Type": "application/json; charset=UTF-8"}

                # para = {"data_insert_index": "entity", "data_insert_json": data_insert_json}
                # search_result = requests.post(url + '/dataInsert', data=json.dumps(para), headers=header)
            '''
        else:
            props = props if props else {}
            if name in synonyms:
                synonyms.remove(name)
            entity = Entity(uuid=uuid.uuid1(), name=name, category_uuid=category_uuid, props=props, synonyms=synonyms,
                            summary=summary,
                            valid=1)

            db.session.add(entity)
            db.session.commit()
            es_insert_item = {}

            if entity.uuid:
                es_insert_item = {"uuid": str(entity.uuid)}
            # es 插入操作
            if name:
                es_insert_item["name"] = name
            if category_uuid:
                es_insert_item["category_uuid"] = category_uuid
            if summary:
                es_insert_item["summary"] = summary

            es_insert_item["props"] = props if props else {}
            if synonyms:
                es_insert_item["synonyms"] = synonyms

            data_insert_json = [es_insert_item]
            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'

            header = {"Content-Type": "application/json; charset=UTF-8"}

            para = {"data_insert_index": "entity", "data_insert_json": data_insert_json}
            # search_result = requests.post(url + '/dataInsert', data=json.dumps(para), headers=header)
    except Exception as e:
        db.session.rollback()
        print(str(e))


@blue_print.route('sync_entity_doc_place_doc_entity', methods=['POST'])
def sync_entity_doc_place_doc_entity():
    try:
        entity_sqls = request.files.getlist('entity_sql', None)
        doc_mark_place_sqls = request.files.getlist('doc_mark_place_sql', None)
        doc_mark_entity_sqls = request.files.getlist('doc_mark_entity_sql', None)
        place_save_path = ''
        entity_save_path = ''
        for doc_mark_place_sql in doc_mark_place_sqls:
            path_filename = doc_mark_place_sql.filename
            path = path_filename.split("/")
            if path:
                filename = secure_filename(''.join(lazy_pinyin(path[-1])))
                save_filename = "{0}{1}{2}".format(os.path.splitext(filename)[0],
                                                   datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                                                   os.path.splitext(filename)[1]).lower()
                place_save_path = os.path.join(os.getcwd(), 'static', save_filename)
                doc_mark_place_sql.save(place_save_path)

        for doc_mark_entity_sql in doc_mark_entity_sqls:
            path_filename = doc_mark_entity_sql.filename
            path = path_filename.split("/")
            if path:
                filename = secure_filename(''.join(lazy_pinyin(path[-1])))
                save_filename = "{0}{1}{2}".format(os.path.splitext(filename)[0],
                                                   datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                                                   os.path.splitext(filename)[1]).lower()
                entity_save_path = os.path.join(os.getcwd(), 'static', save_filename)
                doc_mark_entity_sql.save(entity_save_path)

        dict = get_doc_mark_entity_place_dict(place_save_path, entity_save_path)
        dict_trans_entity = {}
        dict_trans_place = {}
        for entity_sql in entity_sqls:
            path_filename = entity_sql.filename
            path = path_filename.split("/")
            if path:
                filename = secure_filename(''.join(lazy_pinyin(path[-1])))
                save_filename = "{0}{1}{2}".format(os.path.splitext(filename)[0],
                                                   datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                                                   os.path.splitext(filename)[1]).lower()
                file_savepath = os.path.join(os.getcwd(), 'static', save_filename)
                entity_sql.save(file_savepath)
                with open(file_savepath, mode='r', encoding='utf-8') as file:
                    lines = file.readlines()
                    for line in lines:
                        tmp = line.split("VALUES ")
                        if len(tmp) >= 2:
                            tmp = tmp[1][1:-1]
                            str_list = tmp.split(",")
                            if len(str_list) == 14:
                                entity = db.session.query(Entity).filter(Entity.name == str_list[0][1:-1],
                                                                         Entity.valid == 1).first()
                                if entity:
                                    e_uuid = str_list[7].strip(" ").strip("'")
                                    if e_uuid in dict.get("entity_uuid") and e_uuid != str(entity.uuid):
                                        dict_trans_entity[e_uuid] = entity.uuid
                                    if e_uuid in dict.get("place_uuid") and e_uuid != str(entity.uuid):
                                        dict_trans_place[e_uuid] = entity.uuid
                                else:
                                    if int(str_list[12]):
                                        with open('entity.txt', mode='w', encoding='utf-8') as f:
                                            f.write(line)

        with open('doc_mark_place_insert.txt', mode='w', encoding='utf-8') as file:
            for key, value in dict_trans_place.items():
                tmp_str = "UPDATE doc_mark_place SET place_uuid='{0}' WHERE place_uuid='{1}';".format(value, key)
                file.write(tmp_str + '\n')

        with open('doc_mark_entity_insert.txt', mode='w', encoding='utf-8') as file:
            for key, value in dict_trans_entity.items():
                tmp_str = "UPDATE doc_mark_entity SET entity_uuid='{0}' WHERE entity_uuid='{1}';".format(value, key)
                file.write(tmp_str + '\n')
        res = success_res()
    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


def get_doc_mark_entity_place_dict(place_save_path, entity_save_path):
    dict = {}
    with open(place_save_path, mode='r', encoding='utf-8') as file:
        lines = file.readlines()
        place_uuid = []
        for line in lines:
            tmp = line.split("]',")
            if len(tmp) >= 2:
                str_list = tmp[1].split(",")
                if len(str_list) >= 4:
                    if str_list[3].strip(" ").strip("'") not in place_uuid:
                        place_uuid.append(str_list[3].strip(" ").strip("'"))
        dict["place_uuid"] = place_uuid
    with open(entity_save_path, mode='r', encoding='utf-8') as file:
        lines = file.readlines()
        entity_uuid = []
        for line in lines:
            tmp = line.split("]',")
            if len(tmp) >= 2:
                str_list = tmp[1].split(",")
                if len(str_list) >= 4:
                    if str_list[3].strip(" ").strip("'") not in entity_uuid:
                        entity_uuid.append(str_list[3].strip(" ").strip("'"))
        dict["entity_uuid"] = entity_uuid
    return dict
