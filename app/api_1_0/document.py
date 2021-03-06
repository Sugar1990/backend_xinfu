# -*- coding: utf-8 -*-
import datetime
import hashlib
import json
import math
import os
import re
import time
import uuid

import requests
# from flasgger import swag_from
from flask import jsonify, request
from pypinyin import lazy_pinyin
from sqlalchemy import or_, and_
from werkzeug.utils import secure_filename

# from app.swagger.document_dict import *
from . import api_document as blue_print
from .get_leader_ids import get_leader_ids
from .utils import success_res, fail_res, devide_str, dfm_format
from .. import db, lock
from ..conf import LEXICON_IP, LEXICON_PORT, SUMMARY_IP, SUMMARY_PORT, YC_ROOT_URL, ES_SERVER_IP, ES_SERVER_PORT, \
    YC_TAGGING_PAGE_URL, YC_ROOT_URL_PYTHON, EVENT_EXTRACTION_URL, PLACE_BASE_NAME
from ..models import Document, Entity, Customer, Permission, Catalog, DocMarkEntity, DocMarkPlace, DocMarkTimeTag, \
    DocMarkEvent, DocMarkComment, EntityCategory, DocMarkAdvise, DocMarkMind, DocMarkRelationProperty
from ..serve.word_parse import extract_word_content


# 上传文档
@blue_print.route("/upload_doc", methods=['POST'])
# @swag_from(upload_doc_dict)
def upload_doc():
    try:
        catalog_uuid = request.form.get('catalog_uuid', "")
        uid = request.form.get('uid', "")
        file_list = request.files.getlist('file', None)
        # catalog_id = int(catalog_id)

        for file_obj in file_list:
            path_filename = file_obj.filename
            path = path_filename.split("/")
            if path:
                path_catalog_name_list = [i.strip() for i in path[:-1]]
                if path_catalog_name_list:
                    with lock:
                        catalog_uuid = find_leaf_catalog_id(catalog_uuid, path_catalog_name_list, uid)

                if catalog_uuid:
                    filename = secure_filename(''.join(lazy_pinyin(path[-1])))
                    save_filename = "{0}{1}{2}".format(os.path.splitext(filename)[0],
                                                       datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                                                       os.path.splitext(filename)[1]).lower()
                    file_savepath = os.path.join(os.getcwd(), 'static', save_filename)
                    file_obj.save(file_savepath)

                    doc_extension = os.path.splitext(filename)[1]
                    content_list, keywords = [], []
                    if doc_extension in ['.docx', '.doc']:
                        content_list = extract_word_content(file_savepath)
                        keywords = get_keywords(content_list)

                    permission_id = 0
                    customer = Customer.query.filter_by(uuid=uid).first()
                    if customer:
                        permission = Permission.query.filter_by(id=customer.permission_id).first()
                        if permission:
                            permission_id = permission.id

                        with open(file_savepath, 'rb') as f:
                            md5_hash = hashlib.md5(f.read())
                            file_md5 = md5_hash.hexdigest()

                        if file_md5:
                            doc = Document.query.filter_by(md5=file_md5, catalog_uuid=catalog_uuid, valid=1).first()
                            if doc:
                                url = YC_TAGGING_PAGE_URL + "?doc_id={0}&uid={1}".format(doc.uuid, uid)
                                doc_power = doc.get_power() if doc else 0
                                cus_power = customer.get_power() if customer else 0
                                if cus_power:
                                    if doc_power <= cus_power:
                                        url += "&edit=1"
                                res = fail_res(data=url, msg="{0}文档已存在\n".format(path[-1]))
                            else:
                                datetime_now = datetime.datetime.now()
                                doc = Document(uuid=uuid.uuid1(), name=path[-1],
                                               category=os.path.splitext(filename)[1],
                                               savepath='/static/{0}'.format(save_filename),
                                               catalog_uuid=catalog_uuid,
                                               content=content_list,
                                               create_by_uuid=uid,
                                               create_time=datetime_now,
                                               permission_id=permission_id,
                                               status=0,
                                               keywords=keywords,
                                               md5=file_md5,
                                               valid=1
                                               )

                                db.session.add(doc)
                                db.session.commit()

                                print("------------preprocess start--------------")

                                if YC_ROOT_URL_PYTHON:

                                    header = {"Content-Type": "application/json; charset=UTF-8"}
                                    url = YC_ROOT_URL_PYTHON + '/api/mark/result'
                                    new_str = '\r\n'.join(doc.content)
                                    body = {"content": new_str}

                                    data = json.dumps(body)
                                    yc_res = requests.post(url=url, data=data, headers=header)
                                    print("yc_res.status_code", yc_res.status_code)
                                    # print("yc_res.content:", yc_res.content)
                                    if yc_res.status_code in (200, 201):
                                        yc_res = yc_res.json()['data']
                                        res_entity = yc_res["entity"]
                                        res_place = yc_res["place"]
                                        res_time = yc_res["time"]
                                        res_concept = yc_res["concept"]
                                        print("res_entity: ", res_entity)
                                        print("res_place: ", res_place)
                                        print("res_concept: ", res_concept)
                                        print("res_time: ", res_time)
                                        data_insert_entity = []
                                        for index, item_entity in enumerate(res_entity):
                                            entity_json = {}
                                            doc_mark_entity = DocMarkEntity(uuid=uuid.uuid1(), doc_uuid=doc.uuid,
                                                                            valid=1)
                                            if item_entity.get("word", ""):
                                                doc_mark_entity.word = item_entity["word"]
                                                entity_json["name"] = item_entity["word"]
                                            if item_entity.get("entity_id", ""):
                                                doc_mark_entity.entity_uuid = str(item_entity["entity_id"])
                                            if item_entity.get("entity_type_id", ""):
                                                entity_json["category_id"] = str(item_entity["entity_type_id"])
                                            if item_entity.get("word_count", ""):
                                                word_count_list = list(item_entity["word_count"].split(','))
                                                doc_mark_entity.appear_index_in_text = word_count_list

                                            # 插入position
                                            if item_entity.get("position", []):
                                                doc_mark_entity.position = item_entity["position"]

                                            db.session.add(doc_mark_entity)
                                            db.session.commit()
                                            item_entity["doc_mark_id"] = str(doc_mark_entity.uuid)
                                            data_insert_entity.append(entity_json)
                                        # print("doc_mark_entity数据插入成功")

                                        for index, item_entity in enumerate(res_concept):
                                            entity_json = {}
                                            doc_mark_entity = DocMarkEntity(uuid=uuid.uuid1(), doc_uuid=doc.uuid,
                                                                            valid=1)
                                            if item_entity.get("word", ""):
                                                doc_mark_entity.word = item_entity["word"]
                                                entity_json["name"] = item_entity["word"]
                                            if item_entity.get("concept_id", ""):
                                                doc_mark_entity.entity_uuid = str(item_entity["concept_id"])
                                            if item_entity.get("concept_type_id", ""):
                                                entity_json["category_id"] = str(item_entity["concept_type_id"])
                                            if item_entity.get("word_count", ""):
                                                word_count_list = list(item_entity["word_count"].split(','))
                                                doc_mark_entity.appear_index_in_text = word_count_list

                                            # 插入position
                                            if item_entity.get("position", []):
                                                doc_mark_entity.position = item_entity["position"]

                                            db.session.add(doc_mark_entity)
                                            db.session.commit()
                                            item_entity["doc_mark_id"] = str(doc_mark_entity.uuid)
                                            data_insert_entity.append(entity_json)

                                        data_insert_place = []
                                        # data_insert_location = []
                                        for index, item_place in enumerate(res_place):
                                            # location_json = {}
                                            doc_mark_place = DocMarkPlace(uuid=uuid.uuid1(), doc_uuid=doc.uuid, valid=1)
                                            if item_place.get("word", ""):
                                                doc_mark_place.word = item_place["word"]
                                                # data_insert_place.append(item_place["word"])
                                            if item_place.get("type", 0):
                                                doc_mark_place.type = item_place["type"]
                                            if item_place.get("place_id", 0):
                                                doc_mark_place.place_uuid = str(item_place["place_id"])

                                            # 插入position
                                            if item_place.get("position", []):
                                                doc_mark_place.position = item_place["position"]
                                            # 插入direction
                                            if item_place.get("direction", ""):
                                                doc_mark_place.direction = item_place["direction"]
                                            # 插入distance
                                            if item_place.get("distance", 0.0):
                                                doc_mark_place.distance = item_place["distance"]
                                            # 插入unit
                                            if item_place.get("unit", ""):
                                                doc_mark_place.unit = item_place["unit"]
                                            # 插入source_type
                                            if item_place.get("source_type", 0):
                                                doc_mark_place.source_type = item_place["source_type"]
                                            # 插入dms
                                            if item_place.get("dms", []):
                                                doc_mark_place.dms = item_place["dms"]
                                            # 插入relation
                                            if item_place.get("relation", ""):
                                                doc_mark_place.relation = item_place["relation"]
                                            # 插入height
                                            if item_place.get("height", ""):
                                                doc_mark_place.height = item_place["height"]
                                            # 插入entity_or_sys
                                            if item_place.get("entity_or_sys", 0):
                                                doc_mark_place.entity_or_sys = item_place["entity_or_sys"]

                                            # doc_mark_place是经纬度时必须含有lon和lat
                                            if doc_mark_place.type == 2:
                                                if item_place.get("place_lon", "") and item_place.get("place_lat", ""):
                                                    if "°" in item_place["place_lon"]:
                                                        place_lon = find_dfm(item_place["place_lon"])
                                                    else:
                                                        place_lon = find_int_in_str(item_place["place_lon"])
                                                    doc_mark_place.place_lon = place_lon

                                                    if "°" in item_place["place_lat"]:
                                                        place_lat = find_dfm(item_place["place_lat"])
                                                    else:
                                                        place_lat = find_int_in_str(item_place["place_lat"])
                                                    doc_mark_place.place_lat = place_lat
                                            # 其他类型的doc_mark_place
                                            else:
                                                # if item_place.get("place_lon", ""):
                                                #     doc_mark_place.place_lon = item_place["place_lon"]
                                                #
                                                # # location_json["lon"] = item_place["place_lon"]
                                                # if item_place.get("place_lat", ""):
                                                #     doc_mark_place.place_lat = item_place["place_lat"]

                                                if item_place.get("place_lon", ""):
                                                    try:
                                                        place_lon = float(item_place.get("place_lon"))
                                                        doc_mark_place.place_lon = str(place_lon)
                                                    except:
                                                        pass

                                                if item_place.get("place_lat", ""):
                                                    try:
                                                        place_lat = float(item_place.get("place_lat"))
                                                        doc_mark_place.place_lat = str(place_lat)
                                                    except:
                                                        pass

                                                    # location_json["lat"] = item_place["place_lat"]
                                            if item_place.get("word_count", ""):
                                                word_count_list = list(item_place["word_count"].split(','))
                                                doc_mark_place.appear_index_in_text = word_count_list

                                            # 经纬度都有值时添加到数据库中
                                            if doc_mark_place.type == 2:
                                                if doc_mark_place.place_lon and doc_mark_place.place_lat:
                                                    db.session.add(doc_mark_place)
                                                    db.session.commit()
                                                    item_place["doc_mark_id"] = str(doc_mark_place.uuid)
                                                    # 合格的地名才同步es
                                                    data_insert_place.append(doc_mark_place.word)
                                            else:
                                                db.session.add(doc_mark_place)
                                                db.session.commit()
                                                item_place["doc_mark_id"] = str(doc_mark_place.uuid)

                                                data_insert_place.append(doc_mark_place.word)

                                                # data_insert_location.append(location_json)
                                        print("doc_mark_place数据插入成功")

                                        data_insert_date = []
                                        data_insert_time_range = []
                                        data_insert_time_period = []
                                        for index, item_time in enumerate(res_time):
                                            time_range_json = {}
                                            doc_mark_time_tag = DocMarkTimeTag(uuid=uuid.uuid1(), doc_uuid=doc.uuid,
                                                                               valid=1)
                                            if item_time.get("time_type", 0):
                                                doc_mark_time_tag.time_type = item_time["time_type"]
                                            if item_time.get("word", ""):
                                                doc_mark_time_tag.word = item_time["word"]

                                            # 插入position
                                            if item_time.get("position", []):
                                                doc_mark_time_tag.position = item_time["position"]
                                            if item_time.get("format_date", ""):
                                                doc_mark_time_tag.format_date = item_time["format_date"]
                                            if item_time.get("format_date_end", ""):
                                                doc_mark_time_tag.format_date_end = item_time["format_date_end"]
                                            if item_time.get("arab_time", ""):
                                                doc_mark_time_tag.arab_time = item_time["arab_time"]
                                                data_insert_time_period.append(item_time["arab_time"])
                                            if item_time.get("word_count", ""):
                                                word_count_list = list(item_time["word_count"].split(','))
                                                doc_mark_time_tag.appear_index_in_text = word_count_list
                                            if item_time.get("format_date", "") and item_time.get("format_date_end",
                                                                                                  ""):
                                                start_time = time.strptime(item_time["format_date"],
                                                                           "%Y-%m-%d %H:%M:%S")
                                                start_time = int(time.mktime(start_time))
                                                end_time = time.strptime(item_time["format_date_end"],
                                                                         "%Y-%m-%d %H:%M:%S")
                                                end_time = int(time.mktime(end_time))
                                                time_range_json["start_time"] = start_time
                                                time_range_json["end_time"] = end_time
                                                data_insert_time_range.append(time_range_json)
                                            if not item_time.get("format_date_end", "") and item_time.get("format_date",
                                                                                                          ""):
                                                start_time = time.strptime(item_time["format_date"],
                                                                           "%Y-%m-%d %H:%M:%S")
                                                start_time = int(time.mktime(start_time))
                                                data_insert_date.append(start_time)

                                            db.session.add(doc_mark_time_tag)
                                            db.session.commit()
                                            item_time["doc_mark_id"] = str(doc_mark_time_tag.uuid)
                                        # print("doc_mark_time_tag插入成功")

                                        doc.status = 2
                                        db.session.commit()

                                        print("yc_res_1: ", yc_res)

                                        # <editor-fold desc="返回event带解析封装接口">
                                        event_id_list = []
                                        event_res = {}
                                        event_res['content'] = doc.content
                                        event_res['result'] = yc_res
                                        header = {"Content-Type": "application/json; charset=UTF-8"}
                                        url = EVENT_EXTRACTION_URL + '/event_extraction'

                                        data = json.dumps(event_res)
                                        # print("jw接口传参：", event_res)
                                        event_extraction_res = requests.post(url=url, data=data, headers=header)

                                        print("event_extraction_res.status_code", event_extraction_res.status_code)

                                        if event_extraction_res.status_code in (200, 201):
                                            print("jw接口结果", event_extraction_res.json()["result"])
                                            data_insert_event = []

                                            for item in event_extraction_res.json()["result"]:
                                                # print("a")
                                                event_json = {}
                                                doc_mark_event = DocMarkEvent(uuid=uuid.uuid1(), doc_uuid=doc.uuid,
                                                                              valid=1)
                                                if not item.get("event_address", []) or not item.get("event_time",
                                                                                                     []) or not (
                                                        item.get("event_subject", []) or item.get("event_object", [])):
                                                    continue
                                                if item.get("event_address", []):
                                                    # print("b")
                                                    doc_mark_event.event_address = item["event_address"]
                                                if item.get("event_class_id", None):
                                                    doc_mark_event.event_class_uuid = item["event_class_id"]
                                                    event_json["event_class_id"] = item["event_class_id"]
                                                if item.get("event_category_id", None):
                                                    doc_mark_event.event_type_uuid = item["event_category_id"]
                                                    event_json["category_id"] = item["event_category_id"]
                                                if item.get("event_desc", ""):
                                                    doc_mark_event.event_desc = item["event_desc"]
                                                if item.get("event_object", []):
                                                    doc_mark_event.event_object = item["event_object"]
                                                if item.get("event_predicate", ""):
                                                    doc_mark_event.event_predicate = item["event_predicate"]
                                                if item.get("event_subject", []):
                                                    doc_mark_event.event_subject = item["event_subject"]
                                                if item.get("event_time", []):
                                                    doc_mark_event.event_time = item["event_time"]
                                                if item.get("title", ""):
                                                    doc_mark_event.title = item["title"]
                                                db.session.add(doc_mark_event)
                                                db.session.commit()
                                                print(doc_mark_event.uuid)

                                                event_id_list.append(str(doc_mark_event.uuid))
                                                data_insert_event.append(event_json)
                                        else:
                                            res = fail_res(msg="调用event_extraction接口失败")
                                            return res
                                        # </editor-fold>

                                        # <editor-fold desc="调用yc文档预处理接口,eventIds暂时为空列表">
                                        eventIds = event_id_list
                                        header = {"Content-Type": "application/json; charset=UTF-8"}
                                        url = YC_ROOT_URL + '/doc/preprocess'
                                        # print(doc.uuid)
                                        body = {"docId": str(doc.uuid), "eventIds": eventIds}
                                        data = json.dumps(body)
                                        yc_res_event = requests.post(url=url, data=data, headers=header)
                                        print("yc_res_event.status_code", yc_res_event.status_code)
                                        if yc_res_event.status_code in (200, 201):
                                            print(json.loads(yc_res_event.text))
                                            res_html_path = yc_res_event.json()["data"]
                                            # res_html_path = json.loads(yc_res_event.text)
                                            print("路径结果", res_html_path)
                                            doc_html = Document.query.filter_by(uuid=doc.uuid,
                                                                                catalog_uuid=catalog_uuid,
                                                                                valid=1).first()
                                            doc_html.html_path = res_html_path
                                            print("res_html_path", doc_html.html_path)
                                            db.session.commit()
                                        else:
                                            res = fail_res(msg="调用doc_preprocess接口失败")
                                            return res
                                            # </editor-fold>
                                    else:
                                        res = fail_res(msg="上传成功，但预处理失败")
                                        return res

                                # 抽取id、name、content插入es数据库中
                                data_insert_json = [{
                                    "uuid": str(doc.uuid),
                                    "name": doc.name,
                                    "content": doc.content,
                                    "create_time": datetime_now.isoformat(),
                                    "keywords": doc.keywords,
                                    "date": data_insert_date,
                                    "time_range": data_insert_time_range,
                                    "time_period": data_insert_time_period,
                                    "place": data_insert_place,
                                    # "location": data_insert_location,
                                    "entities": data_insert_entity,
                                    "event_categories": data_insert_event,
                                    "doc_type": str(doc.catalog_uuid)
                                }]
                                # an_catalog = Catalog.get_ancestorn_catalog(catalog_uuid)
                                # doc_type_id = str(an_catalog.uuid) if an_catalog else ""
                                # if doc_type_id:
                                #     data_insert_json[0]["doc_type"] = doc_type_id

                                url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
                                header = {"Content-Type": "application/json; charset=UTF-8"}
                                para = {"data_insert_index": "document",
                                        "data_insert_json": data_insert_json}

                                insert_result = requests.post(url + '/dataInsert', data=json.dumps(para),
                                                              headers=header)

                                url = YC_TAGGING_PAGE_URL + "?doc_id={0}&uid={1}".format(doc.uuid, uid)
                                doc_power = doc.get_power() if doc else 0
                                cus_power = customer.get_power() if customer else 0
                                if cus_power:
                                    if doc_power <= cus_power:
                                        url += "&edit=1"
                                res = success_res(data=url)
                        else:
                            res = fail_res(msg="计算文件md5异常，上传失败")
                    else:
                        res = fail_res(msg="无效用户，操作失败")
                else:
                    res = fail_res(msg="文档不能上传至根目录")
            else:
                res = fail_res(msg="upload path is empty")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(str(e))
    return jsonify(res)


def find_leaf_catalog_id(parent_catalog_id, path_catalog_name_list, uid):
    if len(path_catalog_name_list) == 1:
        path_name = path_catalog_name_list[0]
        catalog = Catalog.query.filter_by(name=path_name).filter_by(parent_uuid=parent_catalog_id).first()
        if catalog:
            return catalog.uuid
        else:
            catalog = Catalog(name=path_name, parent_uuid=parent_catalog_id, create_by_uuid=uid,
                              create_time=datetime.datetime.now())
            db.session.add(catalog)
            db.session.commit()
            return catalog.uuid
    else:
        path_name = path_catalog_name_list.pop(0)
        catalog = Catalog.query.filter_by(name=path_name).filter_by(parent_uuid=parent_catalog_id).first()
        if catalog:
            return find_leaf_catalog_id(catalog.uuid, path_catalog_name_list, uid)
        else:
            catalog = Catalog(name=path_name, parent_uuid=parent_catalog_id, create_by_uuid=uid,
                              create_time=datetime.datetime.now())
            db.session.add(catalog)
            db.session.commit()
            return find_leaf_catalog_id(catalog.uuid, path_catalog_name_list, uid)


# 获得文档路径
@blue_print.route("/get_doc_realpath", methods=['GET'])
# @swag_from(get_doc_realpath_dict)
def get_doc_realpath():
    try:
        doc_uuid = request.args.get('doc_uuid', "")
        doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()

        res = doc.savepath.replace('\n\"', '') if doc else ""
    except Exception as e:
        print(str(e))
        res = ""
    return jsonify(res)


# 修改doc在es中的doc_type（文档的祖目录id）
@blue_print.route("/update_es_doc_type", methods=['GET'])
# @swag_from(update_es_doc_type_dict)
def update_es_doc_type():
    try:
        docs = Document.query.filter_by(valid=1).all()
        doc_ids = [str(i.uuid) for i in docs]
        res = modify_doc_es_doc_type(doc_ids)
    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


# 修改doc在es中的doc_type（文档的祖目录id）
def modify_doc_es_doc_type(doc_ids):
    try:
        if isinstance(doc_ids, list):
            doc_list = Document.query.filter(Document.uuid.in_(doc_ids), Document.valid == 1).all()
            for doc in doc_list:
                # 获得es对应doc
                url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
                header = {"Content-Type": "application/json; charset=UTF-8"}
                search_json = {
                    "uuid": {"type": "term", "value": str(doc.uuid)}
                }

                es_id_para = {"search_index": "document", "search_json": search_json}

                search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)
                try:
                    es_id = search_result.json()['data']['dataList'][0]
                except:
                    es_id = ''

                # 替换doc_type 修改es已有doc
                an_catalog = Catalog.get_ancestorn_catalog(doc.catalog_uuid)
                doc_type = an_catalog.uuid if an_catalog else ""
                key_value_json = {'doc_type': doc_type}
                inesert_para = {"update_index": 'document',
                                "data_update_json": [{es_id: key_value_json}]}

                requests.post(url + '/updatebyId', data=json.dumps(inesert_para), headers=header)
            res = success_res()
        else:
            res = fail_res("paramter \"ids\" is not list type")
    except Exception as e:
        print(str(e))
        res = fail_res()
    return res


# 移动文件到指定目录
@blue_print.route('/move_doc_to_catalog', methods=['POST'])
def move_doc_to_catalog():
    catalog_uuid = request.json.get('catalog_uuid', '')
    doc_uuids = request.json.get('doc_uuids', [])

    try:

        catalog = Catalog.query.filter_by(uuid=catalog_uuid).first()
        if not catalog:
            res = fail_res(msg="目标目录不存在")
        else:
            docs = Document.query.filter(Document.uuid.in_(doc_uuids), Document.valid == 1).all()
            if docs:
                for doc in docs:
                    document_same = Document.query.filter(Document.md5 == doc.md5, Document.uuid != doc.uuid,
                                                          Document.valid == 1).first()
                    move_source_docs_to_target_catalog([doc], catalog_uuid)
                    res = success_res()
            else:
                res = fail_res(msg="移动文档不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 移动文件到指定目录
def move_source_docs_to_target_catalog(source_docs=[], target_catalog_id=""):
    target_docs = Document.query.filter_by(catalog_uuid=target_catalog_id, valid=1).all()

    # 重名：判断和处理重名文件；否则直接移动
    del_doc_id = []
    save_target_docs_dict = {i.md5: i for i in target_docs if i.md5 and i.uuid}
    for source_doc_item in source_docs:
        if source_doc_item.md5 in save_target_docs_dict:
            target_doc_item = save_target_docs_dict[source_doc_item.md5]
            if target_doc_item.status < 2 and source_doc_item.status > 1:
                # 目标文件未标注，移动文件已标注，删除目标文件
                del_doc_id.append(target_doc_item.uuid)
                source_doc_item.catalog_uuid = target_catalog_id
                modify_doc_es_doc_type([str(source_doc_item.uuid)])
                db.session.commit()
            else:
                # 目标文件已标注，删除移动文件
                del_doc_id.append(str(source_doc_item.uuid))
        else:
            source_doc_item.catalog_uuid = target_catalog_id
            modify_doc_es_doc_type([str(source_doc_item.uuid)])
            db.session.commit()
    delete_doc_in_pg_es(del_doc_id)


# 获取文档内容
@blue_print.route('/get_content', methods=['GET'])
# @swag_from(get_content_dict)
def get_content():
    try:
        doc_uuid = request.args.get('doc_uuid')
        doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()
        res = doc.content if doc else []
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


# 获取文档内容
@blue_print.route('/modify_keywords', methods=['POST'])
# @swag_from(modify_keywords)
def modify_keywords():
    try:
        doc_uuid = request.json.get('doc_uuid', '')
        keywords = request.json.get('keywords', [])
        doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()
        if doc:
            doc.keywords = keywords
            db.session.commit()
            res = success_res()
        else:
            res = fail_res(msg="该文档不存在")
    except Exception as e:
        print(str(e))
        res = fail_res(msg="更新异常")
    return jsonify(res)


# 获取文档内容
@blue_print.route('/get_keywords', methods=['GET'])
# @swag_from(get_keywords)
def get_keywords():
    try:
        doc_uuid = request.args.get('doc_uuid')
        doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()
        if doc:
            res = success_res(data=doc.keywords)
        else:
            res = fail_res(data=[], msg="该文档不存在")
    except Exception as e:
        print(str(e))
        res = fail_res(data=[])
    return jsonify(res)


# 更新文档信息
@blue_print.route('/modify_doc_info', methods=['PUT'])
# @swag_from(modify_doc_info_dict)
def modify_doc_info():
    try:
        doc_uuid = request.json.get('doc_uuid', "")
        name = request.json.get('name', '')
        status = request.json.get('status', 0)

        doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()
        if not doc:
            res = fail_res()
        else:
            if name:
                doc.name = name
            if status:
                doc.status = status
            db.session.commit()

            # 获得es对应doc
            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            search_json = {
                "uuid": {"type": "term", "value": str(doc_uuid)}
            }

            es_id_para = {"search_index": "document", "search_json": search_json}

            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)
            try:
                es_id = search_result.json()['data']['dataList'][0]
            except:
                es_id = ''

            # 替换name 修改es已有doc
            if name:
                key_value_json = {'name': name}
                inesert_para = {"update_index": 'document',
                                "data_update_json": [{es_id: key_value_json}]}

                requests.post(url + '/updatebyId', data=json.dumps(inesert_para), headers=header)

            res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 删除文档
@blue_print.route('/del_doc', methods=['POST'])
# @swag_from(del_doc_dict)
def del_doc():
    doc_uuids = request.json.get('doc_uuids', [])
    customer_uuid = request.json.get('customer_uuid', "")
    permission_flag = False
    status_flag = False
    try:
        customer = Customer.query.filter_by(uuid=customer_uuid, valid=1).first()
        print(customer.uuid)
        if customer:
            del_doc_ids = []
            for doc_uuid in doc_uuids:
                doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()
                if doc:
                    if doc.get_power() > customer.get_power():
                        permission_flag = True
                    else:
                        if doc.status < 2:
                            del_doc_ids.append(str(doc.uuid))
                        else:
                            status_flag = True

            # delete_doc_mark_result(del_doc_ids)
            if del_doc_ids:
                delete_doc_mark_result(del_doc_ids)
                success_msg = ['操作成功']  # 删除消息
            else:
                success_msg = []
            if permission_flag or status_flag:
                if del_doc_ids:
                    success_msg.append("。其中部分文档")
                flag_msg = []  # 删除原因
                if permission_flag:
                    flag_msg.append('权限不够')
                if status_flag:
                    flag_msg.append('已标注文档')
                success_msg.append("、".join(flag_msg))
                success_msg.append("，无法删除")

            msg = ''.join(success_msg)

            res = success_res(msg=msg)
        else:
            res = fail_res(msg='无效用户，操作失败')
    except Exception as e:
        print(str(e))
        # db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 删除doc操作
def delete_doc_in_pg_es(doc_ids):
    try:
        for doc_uuid in doc_ids:
            doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()
            if doc:
                doc.valid = 0
                # db.session.delete(doc)
                # db.session.commit()

        es_id_list = []  # 删除doc 对应esdoc的列表
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        for doc_uuid in doc_ids:
            header = {"Content-Type": "application/json; charset=UTF-8"}
            search_json = {
                'uuid': {'type': 'term', 'value': str(doc_uuid)}
            }
            es_id_para = {"search_index": "document", "search_json": search_json}

            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)

            list_out = search_result.json()['data']['dataList']

            if list_out:
                es_id_list.append(list_out[0])

        if es_id_list:
            delete_para = {"delete_index": "document", "id_json": es_id_list}
            search_result = requests.post(url + '/deletebyId', data=json.dumps(delete_para), headers=header)
        else:
            print('No_delete')
    except Exception as e:
        print(str(e))
        pass


def delete_doc_mark_result(doc_ids):
    try:
        doces = Document.query.filter(Document.uuid.in_(doc_ids), Document.valid == 1).all()
        for doc in doces:
            doc.valid = 0

        doc_mark_times = DocMarkTimeTag.query.filter(DocMarkTimeTag.doc_uuid.in_(doc_ids),
                                                     DocMarkTimeTag.valid == 1).all()
        for doc_mark_time in doc_mark_times:
            doc_mark_time.valid = 0

        doc_mark_entities = DocMarkEntity.query.filter(DocMarkEntity.doc_uuid.in_(doc_ids),
                                                       DocMarkEntity.valid == 1).all()
        for doc_mark_entity in doc_mark_entities:
            doc_mark_entity.valid = 0

        doc_mark_plcaces = DocMarkPlace.query.filter(DocMarkPlace.doc_uuid.in_(doc_ids), DocMarkPlace.valid == 1).all()
        for doc_mark_plcace in doc_mark_plcaces:
            doc_mark_plcace.valid = 0

        doc_mark_comments = DocMarkComment.query.filter(DocMarkComment.doc_uuid.in_(doc_ids),
                                                        DocMarkComment.valid == 1).all()
        for doc_mark_comment in doc_mark_comments:
            doc_mark_comment.valid = 0

        doc_mark_minds = DocMarkMind.query.filter(DocMarkMind.doc_uuid.in_(doc_ids), DocMarkMind.valid == 1).all()
        for doc_mark_mind in doc_mark_minds:
            doc_mark_mind.valid = 0

        doc_mark_relationproperties = DocMarkRelationProperty.query.filter(
            DocMarkRelationProperty.doc_uuid.in_(doc_ids), DocMarkRelationProperty.valid == 1).all()
        for doc_mark_relationproperty in doc_mark_relationproperties:
            doc_mark_relationproperty.valid = 0

        doc_mark_advises = DocMarkAdvise.query.filter(DocMarkAdvise.doc_uuid.in_(doc_ids),
                                                      DocMarkAdvise.valid == 1).all()
        for doc_mark_advise in doc_mark_advises:
            doc_mark_advise.valid = 0

        doc_mark_events = DocMarkEvent.query.filter(DocMarkEvent.doc_uuid.in_(doc_ids), DocMarkEvent.valid == 1).all()
        for doc_mark_event in doc_mark_events:
            doc_mark_event.valid = 0

        es_id_list = []  # 删除doc 对应esdoc的列表
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        for doc_uuid in doc_ids:
            header = {"Content-Type": "application/json; charset=UTF-8"}
            search_json = {
                'uuid': {'type': 'term', 'value': str(doc_uuid)}
            }
            es_id_para = {"search_index": "document", "search_json": search_json}

            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)

            list_out = search_result.json()['data']['dataList']

            if list_out:
                es_id_list.append(list_out[0])

        if es_id_list:
            delete_para = {"delete_index": "document", "id_json": es_id_list}
            search_result = requests.post(url + '/deletebyId', data=json.dumps(delete_para), headers=header)
        else:
            print('No_delete')
    except Exception as e:
        print(str(e))
        pass


# 获取上传历史
@blue_print.route('/get_upload_history', methods=['GET'])
# @swag_from(get_upload_history_dict)
def get_upload_history():
    try:
        current_page = request.args.get('cur_page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        customer_uuid = request.args.get('customer_uuid', "")

        pagination = Document.query.filter_by(create_by_uuid=customer_uuid, valid=1).order_by(
            Document.create_time.desc()).paginate(
            current_page, page_size, False)

        data = [{
            "name": i.name,
            "status": 1,  # 上传状态：1成功
            "create_time": i.create_time.strftime('%Y-%m-%d %H:%M:%S')
        } for i in pagination.items]

        res = {
            "total_count": pagination.total,
            "page_count": pagination.pages,
            "data": data,
            "cur_page": pagination.page
        }
    except Exception as e:
        print(str(e))
        res = {}

    return jsonify(res)


# 获取文档信息
@blue_print.route('/get_info', methods=['GET'])
# @swag_from(get_info_dict)
def get_info():
    try:
        doc_uuid = request.args.get('doc_uuid', "")

        doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()
        customer = Customer.query.filter_by(uuid=doc.create_by_uuid, valid=1).first()
        permission = Permission.query.filter_by(id=customer.permission_id, valid=1).first()
        permission_list = Permission.query.filter_by(valid=1).all()
        lower_permission_id_list = []

        if not doc:
            doc_info = {
                "uuid": "",
                "name": "",
                "category": "",
                "create_by_uuid": "",
                "create_time": "",
                "keywords": [],
                "pre_doc_id": 0,
                "next_doc_id": 0,
                "favorite": 0,
                "html_path": ""
            }
        else:

            # ----------------------- 获取上下篇文章 --------------------------
            lower_permission_id_list = []

            for item in permission_list:
                if permission.power >= item.power:
                    lower_permission_id_list.append(item.id)

            documentPrevious = Document.query.filter(Document.permission_id.in_(lower_permission_id_list),
                                                     Document.catalog_uuid == doc.catalog_uuid,
                                                     Document.create_time < doc.create_time,
                                                     Document.valid == 1).order_by(
                Document.create_time.desc()).first()
            documentNext = Document.query.filter(Document.permission_id.in_(lower_permission_id_list),
                                                 Document.catalog_uuid == doc.catalog_uuid,
                                                 Document.valid == 1,
                                                 Document.create_time > doc.create_time).order_by(
                Document.create_time).first()
            # ----------------------- 获取上下篇文章 END --------------------------

            # ----------------------- 根据目录id，获取根目录tab权限 -----------------------
            flag, ancestorn_catalog_tagging_tabs = True, []
            print("uuid", doc.catalog_uuid)
            if doc.catalog_uuid:
                catalog = Catalog.query.filter_by(uuid=doc.catalog_uuid).first()
                print(str(catalog.uuid))
                if catalog:
                    an_catalog = Catalog.get_ancestorn_catalog(catalog.uuid)
                    if an_catalog:
                        flag, ancestorn_catalog_tagging_tabs = True, an_catalog.tagging_tabs
                    else:
                        flag, ancestorn_catalog_tagging_tabs = True, catalog.tagging_tabs
                # print(str(ancestorn_catalog_tagging_tabs),flag)
            # ----------------------- 根据目录id，获取根目录tab权限 END -----------------------

            doc_info = {
                "uuid": str(doc.uuid),
                "name": doc.name[0:doc.name.rindex(".")] if doc.name else "",
                "category": str(doc.catalog_uuid),
                "create_by_uuid": str(doc.create_by_uuid),
                "create_time": doc.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                "keywords": doc.keywords if doc.keywords else [],
                "pre_doc_id": documentPrevious.uuid if documentPrevious else None,
                "next_doc_id": documentNext.uuid if documentNext else None,
                "tagging_tabs": ancestorn_catalog_tagging_tabs if flag else [],
                "favorite": doc.is_favorite,
                "html_path": doc.html_path
            }
    except Exception as e:
        print(str(e))
        doc_info = {"uuid": "",
                    "name": "",
                    "category": "",
                    "create_by_uuid": "",
                    "create_time": "",
                    "keywords": [],
                    "pre_doc_id": 0,
                    "next_doc_id": 0,
                    "favorite": 0,
                    "html_path": ""
                    }

    return jsonify(doc_info)


# 获取实体分页展示
@blue_print.route('/get_entity_in_list_pagination', methods=['GET'])
# @swag_from(get_entity_in_list_pagination_dict)
def get_entity_in_list_pagination():
    try:
        search = request.args.get("search", "")
        customer_uuid = request.args.get("customer_uuid", "")
        cur_page = request.args.get("cur_page", 1, type=int)
        page_size = request.args.get("page_size", 10, type=int)
        docs_order_by_name = request.args.get("docs_order_by_name", 0, type=int)
        docs_order_by_create_time = request.args.get("docs_order_by_create_time", 0, type=int)


        res = {"data": [],
               "page_count": 0,
               "total_count": 0}
        doc_id_list = []
        if search:
            entitiy = Entity.query.filter(or_(Entity.name == search, Entity.synonyms.has_key(search))).first()
            if entitiy:
                category = EntityCategory.query.filter_by(uuid=entitiy.category_uuid, valid=1).first()
                if category.name == PLACE_BASE_NAME:
                    doc_mark_place_list = DocMarkPlace.query.filter_by(place_uuid=entitiy.uuid, valid=1).all()
                    for doc_mark_place in doc_mark_place_list:
                        doc_id_list.append(doc_mark_place.doc_uuid)
                else:
                    doc_mark_entity_list = DocMarkEntity.query.filter_by(entity_uuid=entitiy.uuid, valid=1).all()
                    for doc_mark_entity in doc_mark_entity_list:
                        doc_id_list.append(str(doc_mark_entity.doc_uuid))

                        # if YC_ROOT_URL:
                        #     url = YC_ROOT_URL + "/doc/get_entity_in_list_pagination"
                        #     print(url, flush=True)
                        #     resp = requests.get(url=url, params={"cusotmer_id": customer_id,
                        #                                          "entity_id": entitiy.id,
                        #                                          "cur_page": cur_page,
                        #                                          "page_size": page_size})
                        #
                        #     print(resp.text, flush=True)
                    # rows = json.loads(resp.text).get("rows", [])
                    data = []
                    leader_ids = get_leader_ids()
                    for doc_uuid in list(set(doc_id_list)):
                        doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()
                        if doc:
                            # i['name'] = doc.name
                            # i['create_username'] = Customer.get_username_by_id(doc.create_by)
                            # i['path'] = doc.get_full_path() if doc.get_full_path() else '已失效'
                            # i['extension'] = doc.category
                            # i['tag_flag'] = 1 if doc.status == 1 else 0
                            # i['status'] = doc.get_status_name()
                            # i['permission'] = 1 if Permission.judge_power(customer_id, doc.id) else 0
                            if leader_ids:
                                doc_mark_comments = DocMarkComment.query.filter(DocMarkComment.doc_uuid == doc.uuid,
                                                                                DocMarkComment.create_by_uuid.in_(
                                                                                    leader_ids),
                                                                                DocMarkComment.valid == 1).all()
                                # i["leader_operate"] = 1 if doc_mark_comments else 0
                                res = {
                                    "uuid": doc.uuid,
                                    "name": doc.name,
                                    "create_time": doc.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                                    "create_username": Customer.get_username_by_id(doc.create_by_uuid),
                                    'path': doc.get_full_path() if doc.get_full_path() else '已失效',
                                    'extension': doc.category,
                                    "tag_flag": 1 if doc.status == 1 else 0,
                                    'status': doc.get_status_name(),
                                    'permission': 1 if Permission.judge_power(customer_uuid, doc.uuid) else 0,
                                    'leader_operate': 1 if doc_mark_comments else 0
                                }
                            data.append(res)
                    data_sorted = data
                    if docs_order_by_create_time == 1:
                        data_sorted = sorted(data, key=lambda x: x.get('create_time', ''), reverse=True)
                    elif docs_order_by_create_time == 2:
                        data_sorted = sorted(data, key=lambda x: x.get('create_time', ''), reverse=False)
                    elif docs_order_by_name == 1:
                        data_sorted = sorted(data, key=lambda x: x.get('name', ''), reverse=True)
                    elif docs_order_by_name == 2:
                        data_sorted = sorted(data, key=lambda x: x.get('name', ''), reverse=False)
                    res = {"data": data_sorted,
                           "page_count": int(len(data) / page_size) + 1,
                           "total_count": len(data)}
        else:
            data = []
            leader_ids = get_leader_ids()

            pagination = Document.query.filter(Document.valid == 1).order_by(Document.create_time.desc()).paginate(
                cur_page, page_size, False)
            # pagination = Document.query.filter().order_by(Document.create_time.desc()).limit(100).offset(100).all()
            if leader_ids:
                for doc in pagination.items:
                    doc_mark_comments = DocMarkComment.query.filter(DocMarkComment.doc_uuid == doc.uuid,
                                                                    DocMarkComment.create_by_uuid.in_(leader_ids),
                                                                    DocMarkComment.valid == 1).all()

                    data_res = {
                        "name": doc.name,
                        "uuid": doc.uuid,
                        "create_time": doc.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                        "create_username": Customer.get_username_by_id(
                            doc.create_by_uuid) if doc.create_by_uuid else "",
                        'path': doc.get_full_path() if doc.get_full_path() else '已失效',
                        'extension': doc.category,
                        "tag_flag": 1 if doc.status == 1 else 0,
                        'status': doc.get_status_name(),
                        'permission': 1 if Permission.judge_power(customer_uuid, doc.uuid) else 0,
                        'leader_operate': 1 if doc_mark_comments else 0
                    }
                    data.append(data_res)
                data_sorted = data
                if docs_order_by_create_time == 1:
                    data_sorted = sorted(data, key=lambda x: x.get('create_time', ''), reverse=True)
                elif docs_order_by_create_time == 2:
                    data_sorted = sorted(data, key=lambda x: x.get('create_time', ''), reverse=False)
                elif docs_order_by_name == 1:
                    data_sorted = sorted(data, key=lambda x: x.get('name', ''), reverse=True)
                elif docs_order_by_name == 2:
                    data_sorted = sorted(data, key=lambda x: x.get('name', ''), reverse=False)
                res = {"data": data_sorted,
                       "page_count": int(len(data) / page_size) + 1,
                       "total_count": len(data)}

    except Exception as e:
        print(str(e))
        res = {"data": [],
               "page_count": 0,
               "total_count": 0}

    return jsonify(res)


# 判断文档权限
@blue_print.route('/judge_doc_permission', methods=['GET'])
# @swag_from(judge_doc_permission_dict)
def judge_doc_permission():
    customer_uuid = request.args.get("customer_uuid", "")
    doc_uuid = request.args.get("doc_uuid", "")
    doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()
    cus = Customer.query.filter_by(uuid=customer_uuid).first()
    doc_power = doc.get_power() if doc else 0
    cus_power = cus.get_power() if cus else 0
    if cus_power:
        if doc_power <= cus_power:
            res = success_res(msg="可以打开")
        else:
            res = fail_res(msg="此文档权限较高，无法打开")
    else:
        res = fail_res(msg="当前用户权限较低，无法操作")

    return res


# 模糊文档搜索分页展示
@blue_print.route('/get_search_doc_pagination', methods=['GET'])
# @swag_from(get_search_panigation_dict)
def get_search_pagination():
    try:
        customer_uuid = request.args.get("customer_uuid", "")
        search = request.args.get('search', "")
        search_type = request.args.get('search_type', "")
        page_size = request.args.get('page_size', 10, type=int)
        cur_page = request.args.get('cur_page', 1, type=int)
        docs_order_by_name = request.args.get("docs_order_by_name", 0, type=int)
        docs_order_by_create_time = request.args.get("docs_order_by_create_time", 0, type=int)
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        if search and search_type:
            if search[0] == "\"" or search[0] == "“":
                search_json = {search_type: {"type": "like", "value": search},
                               "sort": {"type": "normal", "sort": "create_time", "asc_desc": "desc"}}
            else:
                search_json = {search_type: {"type": "phrase", "value": search},
                               "sort": {"type": "normal", "sort": "create_time", "asc_desc": "desc"}}
        else:
            search_json = {}
        para = {"search_index": 'document', "search_json": search_json}
        header = {"Content-Type": "application/json"}
        esurl = url + "/searchCustom"

        search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
        # print(search_result, flush=True)
        data = []
        leader_ids = get_leader_ids()
        for doc in search_result.json()['data']['dataList']:
            doc_pg = Document.query.filter_by(uuid=doc['_source']['uuid'], valid=1).first()
            if doc_pg:
                path = doc_pg.get_full_path() if doc_pg else '已失效'
                create_username = Customer.get_username_by_id(doc_pg.create_by_uuid) if doc_pg else '无效用户'
                if leader_ids:
                    doc_mark_comments = DocMarkComment.query.filter(DocMarkComment.doc_uuid == doc_pg.uuid,
                                                                    DocMarkComment.create_by_uuid.in_(leader_ids),
                                                                    DocMarkComment.valid == 1).all()

                    data_item = {
                        'uuid': doc['_source']['uuid'],  # 修改es后改称uuid
                        'name': doc['_source']['name'],
                        'create_username': create_username,
                        'path': path,
                        'create_time': doc['_source']['create_time'],
                        'tag_flag': 1 if doc_pg.status == 1 else 0,
                        "status": doc_pg.get_status_name(),
                        'extension': doc_pg.category,
                        "permission": 1 if Permission.judge_power(customer_uuid, doc_pg.uuid) else 0,
                        "leader_operate": 1 if doc_mark_comments else 0
                    }
                    data.append(data_item)
        data_sorted = data
        if docs_order_by_create_time == 1:
            data_sorted = sorted(data, key=lambda x: x.get('create_time', ''), reverse=True)
        elif docs_order_by_create_time == 2:
            data_sorted = sorted(data, key=lambda x: x.get('create_time', ''), reverse=False)
        elif docs_order_by_name == 1:
            data_sorted = sorted(data, key=lambda x: x.get('name', ''), reverse=True)
        elif docs_order_by_name == 2:
            data_sorted = sorted(data, key=lambda x: x.get('name', ''), reverse=False)
        total_count = len(data_sorted)

        if total_count >= page_size * cur_page:
            list_return = data_sorted[page_size * (cur_page - 1):page_size * cur_page]

        elif total_count < page_size * cur_page and total_count > page_size * (cur_page - 1):
            list_return = data_sorted[page_size * (cur_page - 1):]
        else:
            list_return = []
        # print(esurl, para, flush=True)
        res = {'data': list_return,
               'page_count': math.ceil(total_count / page_size),
               'total_count': total_count}
    except Exception as e:
        print(str(e))
        res = {'data': [],
               'page_count': 1,
               'total_count': 0}
    return jsonify(res)


# # 高级搜索
# @blue_print.route('/search_advanced', methods=['POST'])
# # @swag_from('../swagger/search_advanced.yml')
# def search_advanced():
#     try:
#         start_date = request.json.get('start_date', "")
#         end_date = request.json.get('end_date', "")
#         # 时间参数
#         date = request.json.get('date', [])
#         time_range = request.json.get('time_range', [])
#         time_period = request.json.get('time_period', [])
#         frequency = request.json.get('frequency', [])
#         # 地点参数
#         place = request.json.get('place', [])
#         place_direction_distance = request.json.get('place_direction_distance', [])
#         location = request.json.get('location', [])
#         degrees = request.json.get('degrees', [])
#         length = request.json.get('length', [])
#         route = request.json.get('route', [])
#
#         dates = request.json.get('dates', {})
#
#         if dates.get("date_type", False):
#             date_type = dates.get("date_type", "")
#             date_value = dates.get("value", None)
#             if date_type == 'date':
#                 date = date_value
#             elif date_type == 'time_range':
#                 time_range = date_value
#             elif date_type == 'time_period':
#                 time_period = date_value
#             elif date_type == 'frequency':
#                 frequency = date_value
#
#         places = request.json.get('places', {})
#         if places.get("place_type", False):
#             place_type = places.get("place_type", "")
#             place_value = places.get("value", None)
#             if place_type == 'place':
#                 place = place_value
#             elif place_type == 'place_direction_distance':
#                 place_direction_distance = place_value
#             elif place_type == 'location':
#                 location = place_value
#             elif place_type == 'degrees':
#                 degrees = place_value
#             elif place_type == 'length':
#                 length = place_value
#             elif place_type == 'route':
#                 route = place_value
#
#         # 搜索内容无关参数
#         customer_uuid = request.json.get('customer_uuid', "")
#
#         # 其他搜索参数
#         entities = request.json.get('entities', [])
#         keywords = request.json.get('keywords', [])
#         event_categories = request.json.get('event_categories', {})
#         notes = request.json.get('notes', [])
#         notes_content = request.json.get('notes_content', [])
#         doc_type = request.json.get('doc_type', 0)
#         content = request.json.get('content', "")
#         url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
#         data_screen = get_es_doc(url, customer_uuid=customer_uuid, date=date, time_range=time_range,
#                                  time_period=time_period, frequency=frequency,
#                                  place=place, place_direction_distance=place_direction_distance, location=location,
#                                  degrees=degrees, length=length, route=route, entities=entities, keywords=keywords,
#                                  event_categories=event_categories,
#                                  notes=notes, doc_type=doc_type, content=content, notes_content=notes_content)
#
#         # 组装ids，和结构化数据
#         ids = []
#         for data in data_screen:
#             if data.get("uuid", False):
#                 ids.append(data["uuid"])
#
#         event_list = get_event_list_from_docs()
#
#         final_data = {
#             "doc": data_screen,
#             "event_list": event_list
#         }
#     except Exception as e:
#         print("Exception: ", str(e))
#         final_data = {
#             "doc": [],
#             "event_list": []
#         }
#     return jsonify(final_data)  # doc:原来格式数据 event_list:事件数据


# 高级搜索 doc_type
@blue_print.route('/search_advanced_doc_type1', methods=['POST'])
# @swag_from('../swagger/search_advanced_doc_type.yml')
def search_advanced_doc_type1():
    try:
        start_date = request.json.get('start_date', "")
        end_date = request.json.get('end_date', "")
        # 时间参数
        date = request.json.get('date', [])
        time_range = request.json.get('time_range', [])
        time_period = request.json.get('time_period', [])
        frequency = request.json.get('frequency', [])
        # 地点参数
        place = request.json.get('place', [])
        place_direction_distance = request.json.get('place_direction_distance', [])
        location = request.json.get('location', [])
        degrees = request.json.get('degrees', [])
        length = request.json.get('length', [])
        route = request.json.get('route', [])

        dates = request.json.get('dates', {})

        if dates.get("date_type", False):
            date_type = dates.get("date_type", "")
            date_value = dates.get("value", None)
            if date_type == 'date':
                date = date_value
            elif date_type == 'time_range':
                time_range = date_value
            elif date_type == 'time_period':
                time_period = date_value
            elif date_type == 'frequency':
                frequency = date_value

        places = request.json.get('places', {})
        if places.get("place_type", False):
            place_type = places.get("place_type", "")
            place_value = places.get("value", None)
            if place_type == 'place':
                place = place_value
            elif place_type == 'place_direction_distance':
                place_direction_distance = place_value
            elif place_type == 'location':
                location = place_value
            elif place_type == 'degrees':
                degrees = place_value
            elif place_type == 'length':
                length = place_value
            elif place_type == 'route':
                route = place_value

        # 搜索内容无关参数
        customer_uuid = request.json.get('customer_uuid', "")
        page_size = request.json.get('page_size', 10)
        cur_page = request.json.get('cur_page', 1)

        # 其他搜索参数
        entities = request.json.get('entities', [])
        keywords = request.json.get('keywords', [])
        event_categories = request.json.get('event_categories', {})
        notes = request.json.get('notes', [])
        notes_content = request.json.get('notes_content', [])
        doc_type = request.json.get('doc_type', 0)
        content = request.json.get('content', "")
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'

        data_screen = get_es_doc(url, customer_uuid=customer_uuid, date=date, time_range=time_range,
                                 time_period=time_period, frequency=frequency,
                                 place=place, place_direction_distance=place_direction_distance, location=location,
                                 degrees=degrees, length=length, route=route, entities=entities, keywords=keywords,
                                 event_categories=event_categories,
                                 notes=notes, doc_type=doc_type, content=content, notes_content=notes_content)

        # 组装ids，和结构化数据
        doc_ids = []
        data_by_doc_id = {}
        print(data_screen)
        for data in data_screen:
            if not data["name"]:
                doc = Document.query.filter_by(uuid=data["uuid"], valid=1).first()
                if doc:
                    data["name"] = doc.name if doc else ""
            if data["name"]:
                if data.get("uuid", False):
                    doc_ids.append(data["uuid"])
                if data.get("doc_type", False):
                    if data_by_doc_id.get(data["doc_type"], False) and len(
                            data_by_doc_id[data["doc_type"]]) <= page_size:
                        data_by_doc_id[data["doc_type"]].append(data)
                    else:
                        data_by_doc_id[data["doc_type"]] = [data]

        data_forms = [
            {"name": Catalog.get_name_by_id(doc_type), "data": data_by_doc_id[doc_type]}
            for doc_type in data_by_doc_id if Catalog.get_name_by_id(doc_type)]

        print(doc_ids, flush=True)

        res = {
            "doc": data_forms,
            "event_list": get_doc_events_to_earth(doc_ids),
            "event_list_group_by_entities": get_doc_events_to_earth_by_entities(doc_ids),
            "doc_ids": doc_ids
        }


    except Exception as e:
        print(str(e), flush=True)
        res = {"doc": [],
               "event_list": []}
    return jsonify(res)  # doc:原来格式数据 event_list:事件数据


def get_doc_events_to_earth(doc_ids):
    if isinstance(doc_ids, list):
        doc_mark_event_list = DocMarkEvent.query.filter(DocMarkEvent.doc_uuid.in_(doc_ids)).all()
        result = []
        for doc_mark_event in doc_mark_event_list:
            places = doc_mark_event.get_places()
            place_list = [{
                "word": i.word,
                "place_uuid": i.place_uuid,
                "place_lon": i.place_lon,
                "place_lat": i.place_lat
            } for i in places if i.place_lon and i.place_lat]
            if place_list:
                datetime = []
                if doc_mark_event.event_time and isinstance(doc_mark_event.event_time, list):
                    time_tag = DocMarkTimeTag.query.filter(DocMarkTimeTag.uuid.in_(doc_mark_event.event_time)).first()
                    if time_tag:
                        if time_tag.format_date:
                            datetime.append(time_tag.format_date.strftime("%Y-%m-%d %H:%M:%S"))
                        if time_tag.format_date_end:
                            datetime.append(time_tag.format_date_end.strftime("%Y-%m-%d %H:%M:%S"))
                if datetime:
                    object_list = doc_mark_event.get_object_entity_names()
                    object_list.extend(doc_mark_event.get_subject_entity_names())
                    if object_list:
                        result.append({
                            "title": doc_mark_event.title,
                            "object": object_list,
                            "datetime": datetime,
                            "place": place_list,
                            "event_uuid": doc_mark_event.uuid})
        print("result", result)
        res = sorted(result, key=lambda x: x.get('datetime', '')[0])
    else:
        res = []
    return res


def get_doc_events_to_earth_by_entities(doc_ids):
    if isinstance(doc_ids, list):
        doc_mark_event_list = DocMarkEvent.query.filter(DocMarkEvent.doc_uuid.in_(doc_ids)).all()
        event_dict = {}

        for doc_mark_event in doc_mark_event_list:
            object_uni_list = []
            places = doc_mark_event.get_places()
            place_list = [{
                "word": i.word,
                "place_uuid": i.place_uuid,
                "place_lon": i.place_lon,
                "place_lat": i.place_lat
            } for i in places if i.place_lon and i.place_lat]
            if place_list:
                datetime = []
                if doc_mark_event.event_time and isinstance(doc_mark_event.event_time, list):
                    time_tag = DocMarkTimeTag.query.filter(DocMarkTimeTag.uuid.in_(doc_mark_event.event_time)).first()
                    if time_tag:
                        if time_tag.format_date:
                            datetime.append(time_tag.format_date.strftime("%Y-%m-%d %H:%M:%S"))
                        if time_tag.format_date_end:
                            datetime.append(time_tag.format_date_end.strftime("%Y-%m-%d %H:%M:%S"))
                if datetime:
                    object_list = doc_mark_event.get_object_entity_names()
                    if doc_mark_event.get_subject_entity_names():
                        object_list.extend(doc_mark_event.get_subject_entity_names())
                    object_uni_list = list(set(object_list))
                if object_uni_list:

                    # 确立时间线的key值
                    # timeline_key = ",".join([str(i) for i in sorted(object_uni_list)])

                    item = {
                        "datetime": datetime,
                        "place": place_list,
                        "title": doc_mark_event.title,
                        "object": object_uni_list,
                        "event_uuid": doc_mark_event.uuid
                    }
                    for ob in object_uni_list:
                        if event_dict.get(ob, []):
                            event_dict[ob].append(item)
                        else:
                            event_dict[ob] = [item]
            # </editor-fold>

        res = [sorted(i, key=lambda x: x.get('datetime', '')[0]) for i in event_dict.values() if len(i) > 1]
    else:
        res = []
    return res


# 高级搜索结果doc_ids 筛选事件
@blue_print.route('/screen_event_by_time_range', methods=['POST'])
def get_events_by_doc_ids_and_time_range():
    try:
        doc_uuids = request.json.get('doc_uuids', [])
        start_time = request.json.get('start_time', '1900-01-01')
        end_time = request.json.get('end_time', '9999-12-31')
        res = get_event_list_from_docs(doc_uuids, start_time, end_time)
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


# 高级搜索分页展示
@blue_print.route('/search_advanced_pagination1', methods=['POST'])
# @swag_from('..swagger/search_advanced_pagination.yml')
def search_advanced_pagination1():
    # 时间参数
    date = request.json.get('date', [])
    time_range = request.json.get('time_range', [])
    time_period = request.json.get('time_period', [])
    frequency = request.json.get('frequency', [])
    # 地点参数
    place = request.json.get('place', [])
    place_direction_distance = request.json.get('place_direction_distance', [])
    location = request.json.get('location', [])
    degrees = request.json.get('degrees', [])
    length = request.json.get('length', [])
    route = request.json.get('route', [])

    dates = request.json.get('dates', {})

    if dates.get("date_type", False):
        date_type = dates.get("date_type", "")
        date_value = dates.get("value", None)
        if date_type == 'date':
            date = date_value
        elif date_type == 'time_range':
            time_range = date_value
        elif date_type == 'time_period':
            time_period = date_value
        elif date_type == 'frequency':
            frequency = date_value

    places = request.json.get('places', {})
    if places.get("place_type", False):
        place_type = places.get("place_type", "")
        place_value = places.get("value", None)
        if place_type == 'place':
            place = place_value
        elif place_type == 'place_direction_distance':
            place_direction_distance = place_value
        elif place_type == 'location':
            location = place_value
        elif place_type == 'degrees':
            degrees = place_value
        elif place_type == 'length':
            length = place_value
        elif place_type == 'route':
            route = place_value
    # 搜索内容无关参数
    customer_uuid = request.json.get('customer_uuid', '')
    page_size = request.json.get('page_size', 10)
    cur_page = request.json.get('cur_page', 1)

    # 其他搜索参数
    entities = request.json.get('entities', [])
    keywords = request.json.get('keywords', [])
    event_categories = request.json.get('event_categories', [])
    notes = request.json.get('notes', [])
    notes_content = request.json.get('notes_content', [])
    doc_type = request.json.get('doc_type', "")
    content = request.json.get('content', "")
    url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
    data_screen = get_es_doc(url, customer_uuid=customer_uuid, date=date, time_range=time_range,
                             time_period=time_period, frequency=frequency,
                             place=place, place_direction_distance=place_direction_distance, location=location,
                             degrees=degrees, length=length, route=route, entities=entities, keywords=keywords,
                             event_categories=event_categories,
                             notes=notes, doc_type=doc_type, content=content, notes_content=notes_content)

    data_screen_res = []
    leader_ids = get_leader_ids()
    for data in data_screen:
        print(data)
        doc = Document.query.filter_by(uuid=data["uuid"], valid=1).first()
        if doc:
            if not data["name"]:
                data["name"] = doc.name if doc else ""
            data['create_username'] = Customer.get_username_by_id(doc.create_by_uuid)
            data['path'] = doc.get_full_path() if doc.get_full_path() else '已失效'
            data['extension'] = doc.category
            data['tag_flag'] = 1 if doc.status == 1 else 0
            data['status'] = doc.get_status_name()
            data['permission'] = 1 if Permission.judge_power(customer_uuid, doc.uuid) else 0
            if leader_ids:
                doc_mark_comments = DocMarkComment.query.filter(DocMarkComment.doc_uuid == doc.uuid,
                                                                DocMarkComment.create_by_uuid.in_(
                                                                    leader_ids),
                                                                DocMarkComment.valid == 1).all()
                data["leader_operate"] = 1 if doc_mark_comments else 0
            data_screen_res.append(data)
    total_count = len(data_screen_res)
    if total_count >= page_size * cur_page:
        list_return = data_screen_res[page_size * (cur_page - 1):page_size * cur_page]

    elif total_count < page_size * cur_page and total_count > page_size * (cur_page - 1):
        list_return = data_screen_res[page_size * (cur_page - 1):]
    else:
        list_return = []

    res = {'data': list_return,
           'page_count': math.ceil(total_count / page_size),
           'total_count': total_count}

    return jsonify(res)


# 标记结果储存
@blue_print.route('/save_tagging_result', methods=['POST'])
# @swag_from('../swagger/save_tagging_result.yml')
def save_tagging_result():
    try:

        doc_uuid = request.json.get('doc_uuid', '')
        date = request.json.get('date', [])
        time_range = request.json.get('time_range', [])
        time_period = request.json.get('time_period', [])
        place = request.json.get('place', [])
        frequency = request.json.get('frequency', [])
        place_direction_distance = request.json.get('place_direction_distance', [])
        location = request.json.get('location', [])
        degrees = request.json.get('degrees', [])
        length = request.json.get('length', [])
        route = request.json.get('route', [])
        entities = request.json.get('entities', [])
        event_categories = request.json.get('event_categories', [])
        notes = request.json.get('notes', [])
        notes_content = request.json.get('notes_content', [])
        keywords = request.json.get('keywords', [])
        doc_type = request.json.get('doc_type', 0)
        if not doc_uuid:
            res = fail_res(msg="No doc_uuid")
        else:
            # 替换相应属性,修改es已有doc,如果传递参数做修改，没有传的参数不做修改
            key_value_json = {}

            if date:
                key_value_json["date"] = date
            if time_range:
                key_value_json["time_range"] = time_range
            if time_period:
                key_value_json["time_period"] = time_period
            if place:
                key_value_json["place"] = place
            if place_direction_distance:
                key_value_json["place_direction_distance"] = place_direction_distance
            if location:
                key_value_json["location"] = location
            if degrees:
                key_value_json["degrees"] = degrees
            if length:
                key_value_json["length"] = length
            if route:
                key_value_json["route"] = route
            if entities:
                key_value_json["entities"] = entities
            if event_categories:
                key_value_json["event_categories"] = event_categories
            if notes:
                key_value_json["notes"] = notes
            if doc_type:
                key_value_json["doc_type"] = doc_type
            if keywords:
                key_value_json["keywords"] = keywords
            if frequency:
                key_value_json["frequency"] = frequency
            if notes_content:
                key_value_json["notes_content"] = notes_content

            # 获得es对应doc
            url = f"http://{ES_SERVER_IP}:{ES_SERVER_PORT}"
            header = {"Content-Type": "application/json; charset=UTF-8"}
            search_json = {
                "uuid": {"type": "term", "value": doc_uuid}
            }
            es_id_para = {"search_index": "document", "search_json": search_json}

            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)
            try:
                es_id = search_result.json()['data']['dataList'][0]
            except:
                es_id = ''
            if es_id:
                inesert_para = {"update_index": 'document',
                                "data_update_json": [{es_id: key_value_json}]}
                requests.post(url + '/updatebyId', data=json.dumps(inesert_para), headers=header)
                res = success_res()
            else:
                res = fail_res(msg="can't find doc by doc_uuid in ES")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 获取最新上传文档的标注页面地址
@blue_print.route('/get_latest_upload_file_tagging_url', methods=['GET'])
# @swag_from(get_latest_upload_file_tagging_url)
def get_latest_upload_file_tagging_url():
    try:
        customer_uuid = request.args.get("uuid", '')
        doc = Document.query.filter_by(create_by_uuid=customer_uuid, valid=1).first()
        if doc and customer_uuid:
            url = YC_TAGGING_PAGE_URL + "?doc_id={0}&uid={1}&edit=1".format(doc.uuid, customer_uuid)
            res = success_res(data=url)
        else:
            res = fail_res(data="/#")
    except Exception as e:
        print(str(e))
        res = fail_res(data="/#")
    return res


# 收藏文件
@blue_print.route('/set_favorite', methods=['POST'])
# @swag_from(set_favorite)
def set_favorite():
    try:
        doc_uuid = request.json.get("doc_uuid", '')
        favorite = request.json.get("favorite", 0)
        favorite = int(favorite)
        doc = Document.query.filter_by(uuid=doc_uuid, valid=1).first()
        if doc:
            doc.is_favorite = favorite
            db.session.commit()
            res = success_res()
        else:
            res = fail_res(msg="文档不存在")
    except Exception as e:
        print(str(e))
        res = fail_res()
    return res


# ——————————————————————— 文档抽取、删选 —————————————————————————————


def get_es_doc(url, customer_uuid=0, date=[], time_range=[], time_period=[], place=[], place_direction_distance=[],
               location=[], degrees=[], length=[], route=[], entities=[], keywords=[], event_categories={}, notes=[],
               doc_type="", content="", frequency=[], notes_content=[]):
    search_json = {}
    if content:
        # search_json["name"] = {"type": "like", "value": content}
        search_json["content"] = {"type": "phrase", "value": content}
    if date:
        search_json["date"] = {"type": "id", "value": date}
    if time_period:
        search_json["time_period"] = {"type": "multi_term",
                                      "value": time_period}  # {"type": "like", "value": time_period}
    if frequency:
        search_json["frequency"] = {"type": "multi_term",
                                    "value": frequency}
    if place:
        search_json["place"] = {"type": "multi_term", "value": place}

    if place_direction_distance:  # need analysis
        place_direction_distance = place_direction_distance[0]
        search_json["place_direction_distance.place"] = {"type": "term", "value": place_direction_distance["place"]}
        search_json["place_direction_distance.direction"] = {"type": "term",
                                                             "value": place_direction_distance["direction"]}
        search_json["place_direction_distance.distance"] = {"type": "term",
                                                            "value": place_direction_distance["distance"]}
    if location:  # need analysis
        search_json["location.lat"] = {"type": "term", "value": location[0]["lat"]}
        search_json["location.lon"] = {"type": "term", "value": location[0]["lon"]}
    if length:
        search_json["length"] = {"type": "multi_term", "value": length}
    if keywords:
        search_json["keywords"] = {"type": "multi_term", "value": keywords}
    if route:
        search_json["route"] = {"type": "multi_term", "value": route}
    if notes:
        search_json["notes"] = {"type": "phrase", "value": notes[0]}
    if notes_content:
        search_json["notes_content"] = {"type": "phrase", "value": notes_content[0]}
    if doc_type:
        search_json["doc_type"] = {"type": "term", "value": str(doc_type)}
    if search_json:
        search_json["sort"] = {"type": "normal", "sort": "create_time", "asc_desc": "desc"}
    if not search_json:
        search_json["all"] = {"type": "all", "value": "create_time"}
    # 直接es查询
    para = {"search_index": 'document', "search_json": search_json}
    header = {"Content-Type": "application/json"}
    esurl = url + "/searchCustom"
    search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
    data = [doc['_source'] for doc in search_result.json()['data']['dataList']]
    data_screen = screen_doc(data, time_range=time_range, degrees=degrees,
                             entities=entities)  # event_categories=event_categories)

    return data_screen


def screen_doc(data_inppt, time_range=[], degrees=[], entities=[], event_categories=[]):
    data_output = []
    screen_dict = {}
    if time_range:
        screen_dict["time_range"] = time_range
    if degrees:
        for key in degrees['lon']:
            degrees['lon'][key] = int(degrees['lon'][key])
        for key in degrees['lat']:
            degrees['lat'][key] = int(degrees['lat'][key])
        screen_dict["degrees"] = degrees
    if entities:
        screen_dict["entities"] = {}
        screen_dict["entities"]["entities"] = []
        screen_dict["entities"]["name"] = []
        screen_dict["entities"]["value"] = []
        for ent in entities:
            if ent["entity"] and ent["category_uuid"]:
                screen_dict["entities"]["entities"].append({ent["entity"]: ent["category_uuid"]})
            elif ent["entity"] and not ent["category_uuid"]:
                screen_dict["entities"]["name"].append(ent["entity"])
            elif not ent["entity"] and ent["category_uuid"]:
                screen_dict["entities"]["value"].append(ent["category_uuid"])
    if event_categories:
        screen_dict["event_categories"] = []
        for eve in event_categories:
            screen_dict["event_categories"].append({eve["event_class"]: eve["event_category_uuid"]})

    true_value = len(screen_dict)

    for doc in data_inppt:
        sum_bool = 0
        if time_range and doc.get("time_range", False):

            time_range_bool = True
            try:
                time_range_list = [eval(doc["time_range"])]
            except:
                time_range_list = doc["time_range"]

            for range in time_range_list:
                print(range, screen_dict["time_range"], flush=True)
                if range["end_time"] < screen_dict["time_range"]["start_time"] or range["start_time"] > \
                        screen_dict["time_range"]["end_time"]:
                    time_range_bool = False
            sum_bool += time_range_bool

        if degrees and doc.get("degrees", False):
            degrees_list = doc["degrees"]
            degrees_bool = True
            # degrees_bool =[degree for degree in screen_dict["degrees"] if degree not in degrees_list]
            for deg in screen_dict["degrees"]:
                if deg not in degrees_list:
                    degrees_bool = False
                break
            sum_bool += degrees_bool

        if entities and doc.get("entities", False):
            entites_bool = True
            if type(doc["entities"]).__name__ == "str":
                entities_dic = [{ent: eval(doc["entities"])[ent]}
                                for ent in eval(doc["entities"])]
            else:
                entities_dic = doc["entities"]

            entities_names = [ent["name"] for ent in doc["entities"]]

            entities_values = [ent["category_uuid"] for ent in doc["entities"]]

            screen_entity_list = []

            for entity in screen_dict["entities"]["entities"]:
                key = list(entity.keys())[0]
                screen_entity_list.append({"name": key, "category_uuid": entity[key]})

            for entity in screen_entity_list:
                if entity not in entities_dic:
                    entites_bool = False
                    break

            if entites_bool and screen_dict["entities"]["name"]:
                entites_bool = False
                for entity_name in screen_dict["entities"]["name"]:
                    list_search = list(entity_name)
                    len_search = int(0.65 * len(list_search))
                    print(list_search, len_search, flush=True)
                    for doc_ent in entities_names:
                        list_doc = list(doc_ent)
                        uni_list_len = len([ent_letter for ent_letter in list_search if ent_letter in list_doc])
                        print(uni_list_len, flush=True)
                        if uni_list_len >= len_search and uni_list_len > 1:
                            entites_bool = True
                            break

            if entites_bool and screen_dict["entities"]["value"]:
                for entity_value in screen_dict["entities"]["value"]:
                    if entity_value not in entities_values:
                        entites_bool = False
                        break
            sum_bool += entites_bool

        # screen_dict["event_categories"] 为前端请求[{1:''}]
        # event_categories_dic[0] 为Es内存储事件类型

        if event_categories and doc.get("event_categories", False):
            if type(doc["event_categories"]).__name__ == "str":
                event_categories_dic = eval(doc["event_categories"])
            else:
                event_categories_dic = doc["event_categories"]

                event_value = list(screen_dict["event_categories"][0].values())[0]

                event_key = list(screen_dict["event_categories"][0].keys())[0]

            es_event_category_ids = [i.get("event_category_uuid", '') for i in event_categories_dic]
            es_event_class_ids = [i.get("event_class_uuid", '') for i in event_categories_dic]

            if event_key in es_event_class_ids:
                if event_value:
                    if event_value in es_event_category_ids:
                        event_bool = True
                    else:
                        event_bool = False
                else:
                    event_bool = True
            else:
                event_bool = False
            sum_bool += event_bool

        if sum_bool == true_value:
            data_output.append(doc)

    return data_output


# ——————————————————————— 文档抽取、删选 —————————————————————————————

# ——————————————————————— 提取关键词 —————————————————————————————
def get_lexicon(document):
    url = "http://{0}:{1}/lexicon".format(LEXICON_IP, LEXICON_PORT)
    response = requests.post(url=url,
                             data=json.dumps({'text': document, 'get_pos': '1'}),
                             headers={'Content-Type': 'application/json'})
    return json.loads(response.text)


def get_summary(title, content):
    data = {
        "title": title,
        "sentences": content,
        'get_summary': '1',
        'get_keywords': '1'}
    url = "http://{0}:{1}/summarization".format(SUMMARY_IP, SUMMARY_PORT)
    response = requests.post(url=url,
                             data=json.dumps(data),
                             headers={'Content-Type': 'application/json'})

    result = json.loads(response.text)
    return result


def get_keywords(content):
    try:
        if isinstance(content, list):
            content = ''.join(content)
            title = ""
            title_segmented = get_lexicon(title)['sentences']
            content_segmented = get_lexicon(content)['sentences']
            summary_return = get_summary(title_segmented, content_segmented[:30])
            keywords_result = [k[0] for k in summary_return['keywords'][:5]]

            res = keywords_result
        else:
            res = []
    except Exception as e:
        print("get_keywords error: ", str(e))
        res = []
    return res


# ——————————————————————— 提取关键词 —————————————————————————————
def get_event_list_from_docs(doc_uuids=[], start_date='1000-01-01', end_date='9999-12-31'):
    # <editor-fold desc="construct into event_list from docs order by event_time">
    event_list = []
    if doc_uuids:
        events = DocMarkEvent.query.filter(DocMarkEvent.doc_uuid.in_(doc_uuids), DocMarkEvent.valid == 1).all()
        for i in events:
            if i.event_address and isinstance(i.event_address, list):
                place_uuids = DocMarkPlace.query.with_entities(DocMarkPlace.place_uuid).filter(
                    DocMarkPlace.uuid.in_(i.event_address), DocMarkPlace.valid == 1).all()
                if place_uuids:
                    place_uuids = [str(i[0]) for i in place_uuids]
                    places = Entity.query.filter(Entity.uuid.in_(place_uuids), Entity.valid == 1).all()
                    if places:
                        objects, subjects, form_time = [], [], ""

                        if i.event_object and isinstance(i.event_object, list) and i.event_subject:
                            object_id_list = i.event_object
                            if i.event_subject:
                                object_id_list.extend([ele for ele in i.event_subject if ele])
                            object_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_uuid).filter(
                                DocMarkEntity.uuid.in_(object_id_list), DocMarkEntity.valid == 1).all()
                            if object_ids:
                                object_ids = [str(i[0]) for i in object_ids]
                                objects = Entity.query.filter(Entity.uuid.in_(object_ids), Entity.valid == 1).all()

                        # subject和object结合，返回给前端

                        if objects:
                            if i.event_time and isinstance(i.event_time, list):
                                mark_time_ids = i.event_time
                                times = DocMarkTimeTag.query.with_entities(DocMarkTimeTag.format_date,
                                                                           DocMarkTimeTag.format_date_end).filter(
                                    DocMarkTimeTag.uuid.in_(mark_time_ids), DocMarkTimeTag.valid == 1,
                                    or_(and_(DocMarkTimeTag.format_date.between(start_date, end_date),
                                             DocMarkTimeTag.time_type == 1),
                                        and_(DocMarkTimeTag.format_date > start_date,
                                             DocMarkTimeTag.format_date_end < end_date,
                                             DocMarkTimeTag.time_type == 2))
                                ).all()
                                for time_tag in times:
                                    datetime = []
                                    if time_tag[0]:
                                        datetime.append(time_tag[0])
                                    if time_tag[1]:
                                        datetime.append(time_tag[1])

                                    item = {
                                        "datetime": datetime,
                                        "place": [{
                                            "place_lat": place.latitude,
                                            "place_lon": place.longitude,
                                            "place_id": place.uuid,
                                            # "type": 1,
                                            "word": place.name,
                                        } for place in places],
                                        "title": i.title,
                                        "object": [i.name for i in objects],
                                        "event_id": i.uuid
                                    }
                                    event_list.append(item)
        # </editor-fold>
        event_list = sorted(event_list, key=lambda x: x.get('datetime', '')[0])
    return event_list


def get_event_list_from_docs_group_by_entities(doc_ids=[]):
    # <editor-fold desc="construct into event_list from docs group by subjects & objects order by event_time">
    event_list = []
    if doc_ids:
        event_dict = {}
        events = DocMarkEvent.query.filter(DocMarkEvent.doc_uuid.in_(doc_ids), DocMarkEvent.valid == 1).all()
        for i in events:
            if i.event_address and isinstance(i.event_address, list):
                place_ids = DocMarkPlace.query.with_entities(DocMarkPlace.place_uuid).filter(
                    DocMarkPlace.uuid.in_(i.event_address)).all()
                if place_ids:
                    place_ids = [str(i[0]) for i in place_ids]
                    places = Entity.query.filter(Entity.uuid.in_(place_ids), Entity.valid == 1).all()
                    if places:
                        object_ids, subject_ids = [], []
                        objects, subjects, form_time = [], [], []

                        if i.event_object and isinstance(i.event_object, list):
                            object_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_uuid).filter(
                                DocMarkEntity.uuid.in_(i.event_object), DocMarkEntity.valid == 1).all()
                            if object_ids:
                                object_ids = [str(i[0]) for i in object_ids]
                                objects = Entity.query.filter(Entity.uuid.in_(object_ids), Entity.valid == 1).all()

                        if i.event_subject and isinstance(i.event_subject, list):
                            subject_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_uuid).filter(
                                DocMarkEntity.uuid.in_(i.event_subject), DocMarkEntity.valid == 1).all()
                            if subject_ids:
                                subject_ids = [str(i[0]) for i in subject_ids]
                                subjects = Entity.query.filter(Entity.uuid.in_(subject_ids), Entity.valid == 1).all()

                        # subject和object结合，返回给前端
                        objects.extend(subjects)
                        if objects:
                            if i.event_time and isinstance(i.event_time, list):
                                mark_time_ids = i.event_time
                                times = DocMarkTimeTag.query.with_entities(DocMarkTimeTag.format_date,
                                                                           DocMarkTimeTag.format_date_end).filter(
                                    DocMarkTimeTag.uuid.in_(mark_time_ids), DocMarkTimeTag.valid == 1,
                                    DocMarkTimeTag.time_type.in_(['1', '2'])).all()
                                if times[0]:
                                    form_time.append(times[0])
                                if times[1]:
                                    form_time.append(times[1])
                            if object_ids + subject_ids and form_time:
                                # 确立时间线的key值
                                timeline_key = ",".join([str(i) for i in sorted(list(set(object_ids + subject_ids)))])

                                item = {
                                    "datetime": form_time,
                                    "place": [{
                                        "place_lat": place.latitude,
                                        "place_lon": place.longitude,
                                        "place_id": place.uuid,
                                        # "type": 1,
                                        "word": place.name,
                                    } for place in places],
                                    "title": i.title,
                                    "object": [i.name for i in objects],
                                    "event_id": i.uuid
                                }
                                if event_dict.get(timeline_key, []):
                                    event_dict[timeline_key].append(item)
                                else:
                                    event_dict[timeline_key] = [item]
        # </editor-fold>
        event_list = [sorted(i, key=lambda x: x.get('datetime', '')[0]) for i in event_dict.values()]
    return event_list


# ------------------处理经纬度----------------------------


def find_int_in_str(string):
    str_to_num = re.findall('(\d+)', string)[0]
    return int(str_to_num)


def find_dfm(dfm_string):
    d_ = find_int_in_str(dfm_string.split("°")[0])
    f_ = find_int_in_str(dfm_string.split("°")[1])
    return d_ + f_ / 60


@blue_print.route('search_advance_for_doc_uuids', methods=['POST'])
def search_advance_for_doc_uuids():
    # def search_advance_for_doc_uuids(dates, places, event_categories, entities):
    try:
        dates = request.json.get('dates', None)
        places = request.json.get('places', None)
        event_categories = request.json.get('event_categories', None)
        entities = request.json.get('entities', None)
        '''
        :param dates: {"date_type":"date/time_range/time_period/frequency", "value":"时间戳/{"start_time:"时间戳}"}
        :param places: {“place_type": "place", "value":""}
        places: {place_type: "place_direction_distance", value: [{place: "南海", direction: "东", distance: "0米"}]}
        {"place_type": "degrees", value: [{lat: {degree: "22", minute: "22", second: "22"}, lon: {degree: "32", minute: "22", second: "22"}}]}
        :param event_categories: {event_class: "", event_category_uuid: ""}
        : 
        :return: 
        '''
        doc_uuids_by_dates = []
        doc_uuids_by_place = []
        doc_uuids_by_event = []
        doc_uuids_by_entities = []
        if dates:
            time_tag_ids = []
            if dates.get("date_type", False):
                date_type = dates.get("date_type", "")
                date_value = dates.get("value", None)
                if date_type == 'date':
                    time_tags = DocMarkTimeTag.query.filter_by(format_date=date_value, time_type=1, valid=1).all()
                    doc_uuids_by_dates = [i.doc_uuid for i in time_tags]
                elif date_type == "time_range":
                    time_range = date_value
                    start_time = time_range.get("start_time", '')  # 前段输的是时间戳，要转成年月日形式
                    end_time = time_range.get("end_time", '')
                    if start_time and end_time:
                        time_range_time_tags = DocMarkTimeTag.query.filter_by(time_type=2, valid=1).all()
                        # 取出与该时间段有交集的事件
                        for time_range_time_tag in time_range_time_tags:
                            if not (end_time < time_range_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S') or
                                    start_time > time_range_time_tag.format_date_end.strftime(
                                        '%Y-%m-%d %H:%M:%S')):
                                time_tag_ids.append(str(time_range_time_tag.uuid))
                        # 取出时间点在该时间段内的事件
                        date_time_tags = DocMarkTimeTag.query.filter_by(time_type=1, valid=1).all()
                        for date_time_tag in date_time_tags:
                            if start_time < date_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S') < end_time:
                                time_tag_ids.append(str(date_time_tag.uuid))
                        time_tags = DocMarkTimeTag.query.filter(DocMarkTimeTag.uuid.in_(time_tag_ids),
                                                                DocMarkTimeTag.valid == 1).all()
                        doc_uuids_by_dates = [i.doc_uuid for i in time_tags]
                elif date_type == 'time_period':
                    time_tags = DocMarkTimeTag.query.filter_by(word=date_value, time_type=3, valid=1).all()
                    doc_uuids_by_dates = [i.doc_uuid for i in time_tags]
                else:  # date_type == 'frequency':
                    time_tags = DocMarkTimeTag.query.filter_by(word=date_value, time_type=4, valid=1).all()
                    doc_uuids_by_dates = [i.uuid for i in time_tags]

        if places:
            if places.get("place_type", False):
                place_type = places.get("place_type", "")
                place_value = places.get("value", None)
                if place_type == "place" and place_value:
                    base_entities = Entity.query.filter_by(name=place_value, valid=1).all()
                    for base_entity in base_entities:
                        if base_entity.category_name() == PLACE_BASE_NAME:
                            doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=base_entity.uuid, valid=1,
                                                                           type=1).all()  # multi
                            doc_uuids_by_place = [i.doc_uuid for i in doc_mark_places]

                elif place_type == "place_direction_distance" and place_value:
                    place_value = place_value[0]
                    distance, unit = devide_str(place_value.get('distance'))
                    if place_value.get('place') and place_value.get('direction') and place_value.get('distance'):
                        place_uuid_in_entity = Entity.query.filter_by(name=place_value.get('place'), valid=1).all()
                        for base_place in place_uuid_in_entity:
                            if base_place.category_name() == PLACE_BASE_NAME:
                                doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=base_place.uuid,
                                                                               direction=place_value.get('direction'),
                                                                               distance=str(distance), unit=unit,
                                                                               type=5, valid=1).all()
                                doc_uuids_by_place = [i.doc_uuid for i in doc_mark_places]
                                break

                elif place_type == "degrees" and place_value:
                    degrees = place_value
                    doc_mark_places = DocMarkPlace.query.filter_by(dms=degrees).all()
                    doc_uuids_by_place = [i.doc_uuid for i in doc_mark_places]
                    # if degrees.get("lon", None) and degrees.get("lat", None):
                    #     lon = degrees["lon"]
                    #     lat = degrees["lat"]
                    #     if lon.get("degrees", 0) and lon.get("direction", 0) and lon.get("distance", 0) and lat.get(
                    #             "degrees", 0) and lat.get("direction", 0) and lat.get("distance", 0):
                    #         lon = dfm_convert(lon.get("degrees"), lon.get("direction"), lon.get("distance", 0))
                    #         lat = dfm_convert(lat.get("degrees"), lat.get("direction"), lat.get("distance", 0))
                    #         # entity = Entity.query.filter_by(longitude=lon, latitude=lat, category_uuid="87d323a1-b233-4a82-9883-981da29d7b13", valid=1).first()
                    #         entities = Entity.query.filter_by(longitude=lon, latitude=lat, valid=1).all()
                    #         for entity in entities:
                    #             if entity.category_name() == PLACE_BASE_NAME:
                    #                 doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=entity.uuid, valid=1).all()
                    #                 doc_mark_place_ids = [str(i.uuid) for i in doc_mark_places]
                    #                 break
                # places: {place_type: "location", value: [{lat: "22.22", lon: "111.11"}]}
                elif place_type == 'location':
                    location = place_value[0]
                    if location.get("lon", None) and location.get("lat", None):
                        lon = location["lon"]
                        lat = location["lat"]
                        # entity = Entity.query.filter_by(longitude=lon, latitude=lat, category_uuid="87d323a1-b233-4a82-9883-981da29d7b13", valid=1).first()
                        base_entities = Entity.query.filter_by(longitude=lon, latitude=lat, valid=1).all()
                        for base_entity in base_entities:
                            if base_entity.category_name() == PLACE_BASE_NAME:
                                doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=base_entity.uuid,
                                                                               valid=1).all()
                                doc_uuids_by_place = [i.doc_uuid for i in doc_mark_places]
                elif place_type == 'length':
                    height, unit = devide_str(place_value)
                    doc_mark_places = DocMarkPlace.query.filter_by(height=str(height), unit=unit, valid=1, type=4).all()
                    doc_uuids_by_place = [i.doc_uuid for i in doc_mark_places]
                else:  # place_type == 'route'
                    place_list = []
                    route = set(place_value)
                    doc_mark_places = DocMarkPlace.query.filter_by(valid=1, type=6).all()
                    for doc_mark_place in doc_mark_places:
                        route_set = set(doc_mark_place.relation.split(','))
                        if (route_set - route):
                            place_list.append(doc_mark_place)
                    doc_uuids_by_place = [i.doc_uuid for i in place_list]

        if event_categories:
            condition = []
            event_categories = event_categories[0]
            event_class = event_categories.get('event_class')
            event_category = event_categories.get('event_category_uuid')
            if event_class:
                condition.append(DocMarkEvent.event_class_uuid == event_class)
            if event_category:
                condition.append(DocMarkEvent.event_type_uuid == event_category)
            condition = tuple(condition)
            doc_mark_events = DocMarkEvent.query.filter(and_(*condition), DocMarkEvent.valid == 1).all()
            doc_uuids_by_event = [i.doc_uuid for i in doc_mark_events]

        if entities:
            condition = []
            # entities: [{id: 0, entity: "中华", category_uuid: "7d2a3e03-7eac-4080-a9c3-735ca122b29a"}]
            data = entities[0]
            if data.get('entity'):
                condition.append(Entity.name == data.get('entity'))
            if data.get('category_uuid'):
                condition.append(Entity.category_uuid == data.get('category_uuid'))
            condition = tuple(condition)
            entity_uuids = Entity.query.with_entities(Entity.uuid).filter(and_(*condition), Entity.valid == 1).all()
            if entity_uuids:
                entity_uuids = [i[0] for i in entity_uuids]
            # print("a", entity_uuids)
            if entity_uuids:
                doc_mark_entities = DocMarkEntity.query.filter(DocMarkEntity.entity_uuid.in_(entity_uuids),
                                                               DocMarkEntity.valid == 1).all()  # multi
                print("a", len(doc_mark_entities))
                doc_uuids_by_entities = [i.doc_uuid for i in doc_mark_entities]

        print("时间，地点，实体，事件：", doc_uuids_by_dates, doc_uuids_by_place, doc_uuids_by_entities, doc_uuids_by_event)
        result_list = [i for i in [doc_uuids_by_dates, doc_uuids_by_place, doc_uuids_by_entities, doc_uuids_by_event] if
                       i]
        print("result_list:", result_list)
        result = []
        if result_list:
            result = result_list[0]
            for i in range(len(result_list) - 1):
                result = list(set(result_list[i]).intersection(set(result_list[i + 1])))
        res = success_res(data=result)
    except Exception as e:
        print(str(e))
        res = fail_res(msg=str(e))
    return jsonify(res)


@blue_print.route('/search_advanced_doc_type', methods=['POST'])
# @swag_from('../swagger/search_advanced_doc_type.yml')
def search_advanced_doc_type():
    try:

        dates = request.json.get('dates', {})

        places = request.json.get('places', {})

        # 搜索内容无关参数
        customer_uuid = request.json.get('customer_uuid', "")
        page_size = request.json.get('page_size', 10)
        cur_page = request.json.get('cur_page', 1)

        # 其他搜索参数
        entities = request.json.get('entities', [])
        keywords = request.json.get('keywords', [])
        event_categories = request.json.get('event_categories', {})
        notes = request.json.get('notes', [])
        notes_content = request.json.get('notes_content', [])
        doc_type = request.json.get('doc_type', 0)
        content = request.json.get('content', "")
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'

        uuid_advanced = search_advance_for_doc_uuids_test(dates, places, event_categories, entities)
        if dates or places or entities or event_categories:
            if not uuid_advanced:
                return {
                    "doc": [],
                    "event_list": [],
                    "event_list_group_by_entities": [],
                    "doc_ids": []
                }

        data_screen = get_es_doc_test(url, doc_uuid=uuid_advanced, keywords=keywords, notes=notes, doc_type=doc_type,
                                      content=content, notes_content=notes_content)
        # 组装ids，和结构化数据
        doc_ids = []
        data_by_doc_id = {}
        for data in data_screen:
            if not data["name"]:
                doc = Document.query.filter_by(uuid=data["uuid"], valid=1).first()
                if doc:
                    data["name"] = doc.name if doc else ""
            if data["name"]:
                if data.get("uuid", False):
                    doc_ids.append(data["uuid"])
                if data.get("doc_type", False):
                    if data_by_doc_id.get(data["doc_type"], False) and len(
                            data_by_doc_id[data["doc_type"]]) <= page_size:
                        data_by_doc_id[data["doc_type"]].append(data)
                    else:
                        data_by_doc_id[data["doc_type"]] = [data]

        data_forms = [
            {"name": Catalog.get_name_by_id(doc_type), "data": data_by_doc_id[doc_type]}
            for doc_type in data_by_doc_id if Catalog.get_name_by_id(doc_type)]

        print("final_test", doc_ids, flush=True)

        res = {
            "doc": data_forms,
            "event_list": get_doc_events_to_earth(doc_ids),
            "event_list_group_by_entities": get_doc_events_to_earth_by_entities(doc_ids),
            "doc_ids": doc_ids
        }


    except Exception as e:
        print(str(e), flush=True)
        res = {"doc": [],
               "event_list": []}
    return jsonify(res)  # doc:原来格式数据 event_list:事件数据


# 高级搜索分页展示
@blue_print.route('/search_advanced_pagination', methods=['POST'])
# @swag_from('..swagger/search_advanced_pagination.yml')
def search_advanced_pagination():
    # 时间参数

    dates = request.json.get('dates', {})

    places = request.json.get('places', {})

    # 搜索内容无关参数
    customer_uuid = request.json.get('customer_uuid', "")
    page_size = request.json.get('page_size', 10)
    cur_page = request.json.get('cur_page', 1)

    # 其他搜索参数
    entities = request.json.get('entities', [])
    keywords = request.json.get('keywords', [])
    event_categories = request.json.get('event_categories', {})
    notes = request.json.get('notes', [])
    notes_content = request.json.get('notes_content', [])
    doc_type = request.json.get('doc_type', 0)
    content = request.json.get('content', "")
    url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'

    # 排序参数
    docs_order_by_name = request.args.get("docs_order_by_name", 0, type=int)
    docs_order_by_create_time = request.args.get("docs_order_by_create_time", 0, type=int)

    uuid_advanced = search_advance_for_doc_uuids_test(dates, places, event_categories, entities)
    if dates or places or entities or event_categories:
        if not uuid_advanced:
            return {'data': [],
                    'page_count': math.ceil(0 / page_size),
                    'total_count': 0}
    print("after_uuid", uuid_advanced, flush=True)
    data_screen = get_es_doc_test(url, doc_uuid=uuid_advanced, keywords=keywords, notes=notes, doc_type=doc_type,
                                  content=content, notes_content=notes_content)

    data_screen_res = []
    leader_ids = get_leader_ids()
    for data in data_screen:
        # print(data)
        doc = Document.query.filter_by(uuid=data["uuid"], valid=1).first()
        if doc:
            if not data["name"]:
                data["name"] = doc.name if doc else ""
            data['create_username'] = Customer.get_username_by_id(doc.create_by_uuid)
            data['path'] = doc.get_full_path() if doc.get_full_path() else '已失效'
            data['extension'] = doc.category
            data['tag_flag'] = 1 if doc.status == 1 else 0
            data['status'] = doc.get_status_name()
            data['permission'] = 1 if Permission.judge_power(customer_uuid, doc.uuid) else 0
            if leader_ids:
                doc_mark_comments = DocMarkComment.query.filter(DocMarkComment.doc_uuid == doc.uuid,
                                                                DocMarkComment.create_by_uuid.in_(
                                                                    leader_ids),
                                                                DocMarkComment.valid == 1).all()
                data["leader_operate"] = 1 if doc_mark_comments else 0
            data_screen_res.append(data)
    total_count = len(data_screen_res)
    if total_count >= page_size * cur_page:
        list_return = data_screen_res[page_size * (cur_page - 1):page_size * cur_page]

    elif total_count < page_size * cur_page and total_count > page_size * (cur_page - 1):
        list_return = data_screen_res[page_size * (cur_page - 1):]
    else:
        list_return = []

    if docs_order_by_name:
        if docs_order_by_name == 2:
            list_return = sorted(list_return, key=lambda x: x.get('name', ''))
        else:
            list_return = sorted(list_return, key=lambda x: x.get('name', ''), reverse=True)

    if docs_order_by_create_time:
        if docs_order_by_create_time == 2:  # 升序
            list_return = sorted(list_return, key=lambda x: x.get('create_time', ''))
        else:  # 降序
            list_return = sorted(list_return, key=lambda x: x.get('create_time', ''), reverse=True)

    res = {'data': list_return,
           'page_count': math.ceil(total_count / page_size),
           'total_count': total_count}
    return jsonify(res)


def search_advance_for_doc_uuids_test(dates=[], places=[], event_categories=[], entities=[]):
    '''
    :param dates: {"date_type":"date/time_range/time_period/frequency", "value":"时间戳/{"start_time:"时间戳}"}
    :param places: {“place_type": "place", "value":""}
    places: {place_type: "place_direction_distance", value: [{place: "南海", direction: "东", distance: "0米"}]}
    {"place_type": "degrees", value: [{lat: {degree: "22", minute: "22", second: "22"}, lon: {degree: "32", minute: "22", second: "22"}}]}
    :param event_categories: {event_class: "", event_category_uuid: ""}
    :
    :return:
    '''
    # dates = request.json.get('dates', None)
    # places = request.json.get('places', None)
    # event_categories = request.json.get('event_categories', None)
    # entities = request.json.get('entities', None)
    doc_uuids_by_dates = []
    doc_uuids_by_place = []
    doc_uuids_by_event = []
    doc_uuids_by_entities = []
    if dates:
        time_tag_ids = []
        if dates.get("date_type", False):
            date_type = dates.get("date_type", "")
            date_value = dates.get("value", None)
            if date_type == 'date':
                date_f = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(str(date_value)[:-3])))
                print(date_f, flush=True)
                time_tags = DocMarkTimeTag.query.filter_by(format_date=date_f, time_type=1, valid=1).all()
                doc_uuids_by_dates = [i.doc_uuid for i in time_tags]
            elif date_type == "time_range":
                time_range = date_value
                start_time = time_range.get("start_time", '')  # 前段输的是时间戳，要转成年月日形式
                end_time = time_range.get("end_time", '')

                if start_time and end_time:
                    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(str(start_time)[:-3])))
                    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(str(end_time)[:-3])))
                    print("start_time", start_time, "end_time", end_time, flush=True)
                    time_range_time_tags = DocMarkTimeTag.query.filter_by(time_type=2, valid=1).all()
                    # 取出与该时间段有交集的事件
                    for time_range_time_tag in time_range_time_tags:
                        if not (end_time < time_range_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S') or
                                start_time > time_range_time_tag.format_date_end.strftime(
                                    '%Y-%m-%d %H:%M:%S')):
                            time_tag_ids.append(str(time_range_time_tag.uuid))
                    # 取出时间点在该时间段内的事件
                    date_time_tags = DocMarkTimeTag.query.filter_by(time_type=1, valid=1).all()
                    for date_time_tag in date_time_tags:
                        if start_time < date_time_tag.format_date.strftime('%Y-%m-%d %H:%M:%S') < end_time:
                            time_tag_ids.append(str(date_time_tag.uuid))
                    time_tags = DocMarkTimeTag.query.filter(DocMarkTimeTag.uuid.in_(time_tag_ids),
                                                            DocMarkTimeTag.valid == 1).all()
                    doc_uuids_by_dates = [i.doc_uuid for i in time_tags]
            elif date_type == 'time_period':
                time_tags = DocMarkTimeTag.query.filter_by(word=date_value, time_type=3, valid=1).all()
                doc_uuids_by_dates = [i.doc_uuid for i in time_tags]
            else:  # date_type == 'frequency':
                time_tags = DocMarkTimeTag.query.filter_by(word=date_value, time_type=4, valid=1).all()
                doc_uuids_by_dates = [i.uuid for i in time_tags]

    if places:
        if places.get("place_type", False):
            place_type = places.get("place_type", "")
            place_value = places.get("value", None)
            if place_type == "place" and place_value:
                base_entities = Entity.query.filter_by(name=place_value, valid=1).all()
                for base_entity in base_entities:
                    if base_entity.category_name() == PLACE_BASE_NAME:
                        doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=base_entity.uuid, valid=1,
                                                                       type=1).all()  # multi
                        doc_uuids_by_place = [i.doc_uuid for i in doc_mark_places]

            elif place_type == "place_direction_distance" and place_value:
                place_value = place_value[0]
                distance, unit = devide_str(place_value.get('distance'))
                if place_value.get('place') and place_value.get('direction') and place_value.get('distance'):
                    place_uuid_in_entity = Entity.query.filter_by(name=place_value.get('place'), valid=1).all()
                    for base_place in place_uuid_in_entity:
                        if base_place.category_name() == PLACE_BASE_NAME:
                            doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=base_place.uuid,
                                                                           direction=place_value.get('direction'),
                                                                           distance=str(distance), unit=unit,
                                                                           type=5, valid=1).all()
                            doc_uuids_by_place = [i.doc_uuid for i in doc_mark_places]
                            break

            elif place_type == "degrees" and place_value:
                degrees = dfm_format(place_value)
                doc_mark_places = DocMarkPlace.query.filter_by(dms=degrees).all()
                doc_uuids_by_place = [i.doc_uuid for i in doc_mark_places]

            # places: {place_type: "location", value: [{lat: "22.22", lon: "111.11"}]}
            elif place_type == 'location':
                location = place_value[0]
                if location.get("lon", None) and location.get("lat", None):
                    lon = location["lon"]
                    lat = location["lat"]
                    # entity = Entity.query.filter_by(longitude=lon, latitude=lat, category_uuid="87d323a1-b233-4a82-9883-981da29d7b13", valid=1).first()
                    base_entities = Entity.query.filter_by(longitude=lon, latitude=lat, valid=1).all()
                    for base_entity in base_entities:
                        if base_entity.category_name() == PLACE_BASE_NAME:
                            doc_mark_places = DocMarkPlace.query.filter_by(place_uuid=base_entity.uuid,
                                                                           valid=1).all()
                            doc_uuids_by_place = [i.doc_uuid for i in doc_mark_places]
            elif place_type == 'length':
                height, unit = devide_str(place_value)
                doc_mark_places = DocMarkPlace.query.filter_by(height=str(height), unit=unit, valid=1, type=4).all()
                doc_uuids_by_place = [i.doc_uuid for i in doc_mark_places]
            else:  # place_type == 'route'
                place_list = []
                route = set(place_value)
                doc_mark_places = DocMarkPlace.query.filter_by(valid=1, type=6).all()
                for doc_mark_place in doc_mark_places:
                    route_set = set(doc_mark_place.relation.split(','))
                    if (route_set - route):
                        place_list.append(doc_mark_place)
                doc_uuids_by_place = [i.doc_uuid for i in place_list]

    if event_categories:
        condition = []
        event_categories = event_categories[0]
        event_class = event_categories.get('event_class')
        event_category = event_categories.get('event_category_uuid')
        if event_class:
            condition.append(DocMarkEvent.event_class_uuid == event_class)
        if event_category:
            condition.append(DocMarkEvent.event_type_uuid == event_category)
        condition = tuple(condition)
        doc_mark_events = DocMarkEvent.query.filter(and_(*condition), DocMarkEvent.valid == 1).all()
        doc_uuids_by_event = [i.doc_uuid for i in doc_mark_events]

    if entities:
        condition = []
        # entities: [{id: 0, entity: "中华", category_uuid: "7d2a3e03-7eac-4080-a9c3-735ca122b29a"}]
        data = entities[0]
        if data.get('entity'):
            print(data['entity'], flush=True)
            entity_ins = data['entity']
            condition.append(or_(Entity.name.like(f'%{entity_ins}%'), Entity.synonyms.op('@>')([entity_ins])))
        if data.get('category_uuid'):
            condition.append(Entity.category_uuid == data.get('category_uuid'))
        condition = tuple(condition)
        entity_uuids = Entity.query.with_entities(Entity.uuid).filter(and_(*condition), Entity.valid == 1).all()
        if entity_uuids:
            entity_uuids = [i[0] for i in entity_uuids]
        # print("a", entity_uuids)
        if entity_uuids:
            doc_mark_entities = DocMarkEntity.query.filter(DocMarkEntity.entity_uuid.in_(entity_uuids),
                                                           DocMarkEntity.valid == 1).all()  # multi
            print("a", len(doc_mark_entities))
            doc_uuids_by_entities = [i.doc_uuid for i in doc_mark_entities]

    print("时间，地点，实体，事件：", doc_uuids_by_dates, doc_uuids_by_place, doc_uuids_by_entities, doc_uuids_by_event)
    result_list = [i for i in [doc_uuids_by_dates, doc_uuids_by_place, doc_uuids_by_entities, doc_uuids_by_event] if
                   i]
    print("result_list:", result_list)
    result = []
    if result_list:
        result = result_list[0]
        for i in range(len(result_list) - 1):
            result = list(set(result_list[i]).intersection(set(result_list[i + 1])))

    return [str(i) for i in result]


def get_es_doc_test(url, doc_uuid=[], keywords=[], notes=[], doc_type="", content="", notes_content=[]):
    search_json = {}
    if doc_uuid:
        search_json["uuid"] = {"type": "terms", "value": doc_uuid}
    if content:
        # search_json["name"] = {"type": "like", "value": content}
        search_json["content"] = {"type": "phrase", "value": content}
    if keywords:
        search_json["keywords"] = {"type": "multi_term", "value": keywords}
    if notes:
        search_json["notes"] = {"type": "phrase", "value": notes[0]}
    if notes_content:
        search_json["notes_content"] = {"type": "phrase", "value": notes_content[0]}
    if doc_type:
        search_json["doc_type"] = {"type": "term", "value": str(doc_type)}
    if search_json:
        search_json["sort"] = {"type": "normal", "sort": "create_time", "asc_desc": "desc"}
    if not search_json:
        search_json["all"] = {"type": "all", "value": "create_time"}
    # 直接es查询
    para = {"search_index": 'document', "search_json": search_json}
    header = {"Content-Type": "application/json"}
    esurl = url + "/searchCustom"
    search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
    data = [doc['_source'] for doc in search_result.json()['data']['dataList']]
    return data
