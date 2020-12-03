# from flasgger import swag_from
from flask import jsonify, request
import json
from . import api_initial as blue_print
from ..models import Customer, EntityCategory, Document, Catalog, Entity, DocMarkEvent, DocMarkTimeTag, DocMarkRelationProperty
from .. import db
from ..conf import ADMIN_NAME, ADMIN_PWD, ASSIS_NAME, ASSIS_PWD, TAG_TABS, PLACE_BASE_NAME, ES_SERVER_IP, \
    ES_SERVER_PORT, NEO4J_SERVER_IP, NEO4J_SERVER_PORT
from .utils import success_res, fail_res
import requests
import math
import datetime


# from ..swagger.initial_dict import *

@blue_print.route("/init", methods=['GET'])
def init():
    # 初始化系统管理员和系统维护人员账号
    try:
        customer = Customer.query.filter_by(username=ADMIN_NAME).first()
        if not customer:
            c = Customer(username=ADMIN_NAME, pwd=ADMIN_PWD)
            db.session.add(c)
            db.session.commit()

        customer = Customer.query.filter_by(username=ASSIS_NAME).first()
        if not customer:
            c = Customer(username=ASSIS_NAME, pwd=ASSIS_PWD)
            db.session.add(c)
            db.session.commit()

        print("{0}\n{1}".format("—" * 100, "管理员&系统维护员初始化成功~"), flush=True)
    except:
        db.session.rollback()
        print("管理员&系统维护员初始化异常！", flush=True)

    # 检查标注页面的标注标签
    try:
        tts = json.loads(TAG_TABS)
        print(tts, flush=True)
        print("{0}\n{1}".format("—" * 100, "标注页面的标注标签正常~"), flush=True)
    except Exception as e:
        print(str(e), flush=True)
        print("标注页面的标注标签异常！", flush=True)

    try:
        category = EntityCategory.query.filter_by(username=PLACE_BASE_NAME).first()
        if not category:
            data = [EntityCategory(name="PLACE_BASE_NAME", valid=1)]
            db.session.add_all(data)
            db.session.commit()
        res = success_res()

        print("{0}\n{1}".format("—" * 100, "地名库类型初始化成功~"), flush=True)
    except Exception as e:
        print(str(e), flush=True)
        print("地名库类型初始化异常！", flush=True)
        res = fail_res()

    return jsonify(res)


@blue_print.route('/pg_insert_es', methods=['GET','POST'])
# @swag_from(pg_insert_es_dict)
def pg_insert_es():
    try:
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        header = {"Content-Type": "application/json"}
        esurl = url + "/pg_insert_es"

        pg_table = 'entity'
        es_mapping_dict = {
            "name": "ik_keyword",
            "summary": "ik",
            "latitude": "id",
            "longitude": "id",
            "location": "location"
        }

        para = {"create_index": pg_table, "mapping_json": es_mapping_dict}
        search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)

        pg_table_doc = 'document'
        es_mapping_dict_doc = {
            #"id": "id",
            "name": "ik_keyword",
            "content": "ik"
            # "keywords": "ik",
            # "create_time": "time",
            # "dates": "ik",  # 多个时间，
            # "places": "ik",  # 多个地点
            # "entities": "ik",  # [{name: category_id}, …]  # 多个实体，含名称和类型id
            # "event_categories": "ik",  # [{event_class: event_category}, …]
            #"doc_type": "ik_keyword",
            # "notes": "ik"
        }
        pg_dict_doc = {"uuid": {"col_type": "align", "document": "uuid"},
                   "name": {"col_type": "", "document": "name"},
                   "content": {"col_type": "", "document": "content"},
                   "keywords": {"col_type": "", "document": "keywords"},
                   "create_time": {"col_type": "", "document": "create_time"},
                   "doc_type": {"col_type": "", "document": "catalog_uuid"}
                   }

        para = {"pg_dict": pg_dict_doc, "es_index_name": pg_table_doc, "es_mapping_dict": es_mapping_dict_doc}
        search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
        print(search_result, flush=True)
        res = success_res()
    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


@blue_print.route('/delete_all_in_es', methods=['GET', 'POST'])
# @swag_from(delete_index_dict)
def delete_all_in_es():
    try:
        para = {"delete_index": 'entity'}
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        esurl = url + "/deleteIndex"
        delete_result = requests.get(url=esurl, params=para, headers={})

        para1 = {"delete_index": 'document'}
        delete_result1 = requests.get(url=esurl, params=para1, headers={})
        res = success_res(msg = f"{str(delete_result)},{str(delete_result1)}")
    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


@blue_print.route('/pg_insert_arango', methods=['GET','POST'])
def pg_insert_arango():
    try:
        root_url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        header = {"Content-Type": "application/json"}
        serve_url = root_url + "/arango/insert_data"
        # 插入实体
        entities = Entity.query.with_entities(Entity.uuid, Entity.name, Entity.category_uuid).filter_by(
            valid=1).all()
        print("entities[0].uuid: ", entities[0].uuid)
        batch_size = 20000
        for i in range(math.ceil(len(entities) / batch_size)):
            nodes = [{
                "_key": str(entity.uuid),
                "uuid": str(entity.uuid),
                "name": entity.name,
                "category_uuid": str(entity.category_uuid)
            } for entity in entities if entity.uuid and entity.name and entity.category_uuid][
                    i * batch_size:(i + 1) * batch_size]
            para = {"collection": "entity", "data": nodes}
            search_result = requests.post(url=serve_url, data=json.dumps(para), headers=header)
            # print(search_result.status_code, flush=True)
            # print(search_result.text, flush=True)
            if search_result.status_code != 200 or not json.loads(search_result.text).get("code", 0):
                return fail_res(msg="arango serve error: {}".format(json.loads(search_result.text).get("msg", "")))

        # 插入事件
        serve_url = root_url + "/arango/insert_data"
        events = DocMarkEvent.query.filter_by(valid=1).all()
        insert_nodes = []
        for doc_mark_event in events:
            event_time = []
            for event_time_uuid in doc_mark_event.event_time:
                event_time_tag = DocMarkTimeTag.query.filter_by(uuid=event_time_uuid, valid=1).first()
                if event_time_tag:
                    if event_time_tag.format_date:
                        event_time.append(event_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S'))
            nodes = {
                "_key": str(doc_mark_event.uuid),
                "event_uuid": str(doc_mark_event.uuid),
                "event_subject": doc_mark_event.event_subject,
                "event_object": doc_mark_event.event_object,
                "event_time": event_time
            }
            insert_nodes.append(nodes)

        para = {"collection": "event", "data": insert_nodes}
        result = requests.post(url=serve_url, data=json.dumps(para), headers=header)
        # print(result.status_code, flush=True)
        # print(result.text, flush=True)
        if result.status_code != 200 or not json.loads(result.text).get("code", 0):
            return fail_res(
                msg="arango serve error: {}".format(json.loads(result.text).get("msg", "")))

        # 插入实体关系
        serve_url = root_url + "/arango/insert_edge_data"
        entity_relations = DocMarkRelationProperty.query.filter_by(start_type='1', end_type='1', valid=1).all()
        nodes = [{
            "_key": str(item.uuid),
            "_from": 'entity/' + str(item.source_entity_uuid),
            "_to": 'entity/' + str(item.target_entity_uuid),
            "relation_uuid": str(item.relation_uuid),
            "relation_name": item.relation_name,
            "start_time": item.start_time.strftime('%Y-%m-%d %H:%M:%S') if item.start_time else None,
            "end_time": item.end_time.strftime('%Y-%m-%d %H:%M:%S') if item.end_time else None,
            "doc_uuid": str(item.doc_uuid)
        } for item in entity_relations]

        para = {"collection": "entity_relation", "data": nodes}
        result = requests.post(url=serve_url, data=json.dumps(para), headers=header)
        # print(result.status_code, flush=True)
        # print(result.text, flush=True)
        if result.status_code != 200 or not json.loads(result.text).get("code", 0):
            return fail_res(
                msg="arango serve error: {}".format(json.loads(result.text).get("msg", "")))

        # 插入事件关系
        serve_url = root_url + "/arango/insert_edge_data"
        event_relations = DocMarkRelationProperty.query.filter_by(start_type='2', end_type='2', valid=1).all()
        # print(event_relations[0].uuid)
        nodes = [{
            "_key": str(item.uuid),
            "_from": 'event/' + str(item.source_entity_uuid),
            "_to": 'event/' + str(item.target_entity_uuid),
            "relation_uuid": str(item.relation_uuid),
            "relation_name": item.relation_name,
            "start_time": item.start_time.strftime("%Y-%m-%d %H:%M:%S") if item.start_time else None,
            "end_time": item.end_time.strftime('%Y-%m-%d %H:%M:%S') if item.end_time else None,
            "doc_uuid": str(item.doc_uuid)
        } for item in event_relations]

        para = {"collection": "event_relation", "data": nodes}
        result = requests.post(url=serve_url, data=json.dumps(para), headers=header)
        # print(result.status_code, flush=True)
        # print(result.text, flush=True)
        if result.status_code != 200 or not json.loads(result.text).get("code", 0):
            return fail_res(
                msg="arango serve error: {}".format(json.loads(result.text).get("msg", "")))

        res = success_res()

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/delete_all_in_arango', methods=['GET','POST'])
def delete_all_in_arango():
    try:
        collection_list = ['entity', 'entity_relation', 'event', 'event_relation']
        for collection in collection_list:
            para = {
                "collection": collection,
                "key": "all"
            }
            header = {"Content-Type": "application/json; charset=UTF-8"}
            url = "http://{}:{}".format(ES_SERVER_IP, ES_SERVER_PORT) + '/arango/delete_data'
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


@blue_print.route('/pg_insert_elastic', methods=['GET','POST'])
def pg_insert_elastic():
    try:
        root_url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        header = {"Content-Type": "application/json; charset=UTF-8"}
        serve_url = root_url + "/dataInsert"
        # 插入实体
        entities = Entity.query.with_entities(Entity.uuid, Entity.name, Entity.category_uuid, Entity.summary, Entity.props,
        Entity.synonyms, Entity.longitude, Entity.latitude).filter_by(
            valid=1).all()
        creat_url = root_url + "/createIndex"
        pg_table = 'entity'
        es_mapping_dict = {
            "name": "ik_keyword",
            "summary": "ik",
            "latitude": "id",
            "longitude": "id",
            "location": "location"
        }
        para = {"create_index": pg_table, "mapping_json": es_mapping_dict}
        search_result = requests.post(creat_url, data=json.dumps(para), headers=header)

        #print("entities[0].uuid: ", entities[0].uuid)

        batch_size = 20000
        for i in range(math.ceil(len(entities) / batch_size)):
            nodes = [{
                "uuid": str(entity.uuid),
                "name": entity.name,
                "category_uuid": str(entity.category_uuid),
                "summary": entity.summary,
                "props": entity.props,
                "synonyms": entity.synonyms,
                "latitude": entity.latitude,
                "longitude": entity.longitude
            } for entity in entities if entity.uuid and entity.name and entity.category_uuid][
                    i * batch_size:(i + 1) * batch_size]
            # print(data_insert_json)
            para = {"data_insert_index": "entity", "data_insert_json": nodes}
            search_result = requests.post(serve_url + '/dataInsert', data=json.dumps(para), headers=header)

            if search_result.status_code != 200 or not json.loads(search_result.text).get("code", 0):
                return fail_res(msg="elastic serve error: {}".format(json.loads(search_result.text).get("msg", "")))

        # 插入事件
        # document = Document.query.filter_by(valid=1).all()
        # insert_nodes = []
        # for doc in document:
        #     event_time = []
        #     for event_time_uuid in doc.event_time:
        #         event_time_tag = DocMarkTimeTag.query.filter_by(uuid=event_time_uuid, valid=1).first()
        #         if event_time_tag:
        #             if event_time_tag.format_date:
        #                 event_time.append(event_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S'))
        #     nodes = {
        #         "_key": str(doc.uuid),
        #         "event_uuid": str(doc.uuid),
        #         "event_subject": doc.event_subject,
        #         "event_object": doc.event_object,
        #         "event_time": event_time
        #     }
        #     insert_nodes.append(nodes)
    except Exception as e:
        print(str(e),flush=True
)
    return jsonify(success_res())


# @blue_print.route('/pg_insert_neo4j', methods=['GET'])
# # @swag_from(pg_insert_es_dict)
# def pg_insert_neo4j():
#     try:
#         root_url = f'http://{NEO4J_SERVER_IP}:{NEO4J_SERVER_PORT}'
#         header = {"Content-Type": "application/json"}
#         serve_url = root_url + "/create_node/init_nodes"
#         entities = Entity.query.with_entities(Entity.id, Entity.name, Entity.category_id).filter_by(valid=1).all()
#         batch_size = 20000
#         for i in range(math.ceil(len(entities) / batch_size)):
#             nodes = [{
#                 "id": str(i.id),
#                 "name": i.name,
#                 "category_id": str(i.category_id)
#             } for i in entities if i.id and i.name and i.category_id][i * batch_size:(i + 1) * batch_size]
#             para = {"label": "Entity", "nodes": nodes}
#             search_result = requests.post(url=serve_url, data=json.dumps(para), headers=header)
#             print(search_result.status_code, flush=True)
#             print(search_result.text, flush=True)
#             if search_result.status_code != 200 or not json.loads(search_result.text).get("code", 0):
#                 return fail_res(msg="neo4j serve error: {}".format(json.loads(search_result.text).get("msg", "")))
#         res = success_res()
#     except Exception as e:
#         print(str(e))
#         db.session.rollback()
#         res = fail_res()
#     return jsonify(res)



#__________________________________ 暂时不用的接口

@blue_print.route('/update_es_doc', methods=['GET'])
# @swag_from(update_es_doc_dict)
def update_es_doc():
    try:
        docs = Document.query.all()
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        header = {"Content-Type": "application/json; charset=UTF-8"}
        for doc in docs:
            doc_uuid = doc.uuid
            an_catalog = Catalog.get_ancestorn_catalog(doc.catalog_uuid)
            doc_type = an_catalog.uuid if an_catalog else ""

            # 获得es对应doc
            search_json = {
                "uuid": {"type": "term", "value": str(doc_uuid)}
            }

            es_id_para = {"search_index": "document", "search_json": search_json}

            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)
            try:
                es_id = search_result.json()['data']['dataList'][0]
            except:
                es_id = ''
            # 替换name 修改es已有do
            key_value_json = {'doc_type': str(doc_type)}
            inesert_para = {"update_index": 'document',
                            "data_update_json": [{es_id: key_value_json}]}
            requests.post(url + '/updatebyId', data=json.dumps(inesert_para), headers=header)
            res = success_res()
    except Exception as e:
        print(str(e))
        res = fail_res()
    return res


@blue_print.route('/entity_update_loaction', methods=['GET'])
def entity_update_loaction():
    try:
        entities = Entity.query.all()
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        header = {"Content-Type": "application/json; charset=UTF-8"}
        for entity in entities:
            ent_id = entity.id
            ent_location = Entity.get_location_of_entity(ent_id)
            # 获得es对应entity
            search_json = {
                "id": {"type": "id", "value": ent_id}
            }
            es_id_para = {"search_index": "entity", "search_json": search_json}

            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)
            try:
                es_id = search_result.json()['data']['dataList'][0]
            except:
                es_id = ''
            # 替换name 修改es已有entity
            key_value_json = {'location': ent_location}
            inesert_para = {"update_index": 'entity',
                            "data_update_json": [{es_id: key_value_json}]}
            requests.post(url + '/updatebyId', data=json.dumps(inesert_para), headers=header)
            res = success_res()
    except Exception as e:
        print(str(e))
        res = fail_res(str(e))
    return res
