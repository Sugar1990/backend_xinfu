# -*- coding: utf-8 -*-
import datetime
import hashlib
import json
import math
import os
import time
import re
import requests
# from flasgger import swag_from
from flask import jsonify, request
from pypinyin import lazy_pinyin
from sqlalchemy import or_, and_
from werkzeug.utils import secure_filename

# from app.swagger.document_dict import *
from . import api_document as blue_print
from .get_leader_ids import get_leader_ids
from .utils import success_res, fail_res
from .. import db, lock
from ..conf import LEXICON_IP, LEXICON_PORT, SUMMARY_IP, SUMMARY_PORT, YC_ROOT_URL, ES_SERVER_IP, ES_SERVER_PORT, \
    YC_TAGGING_PAGE_URL, YC_ROOT_URL_PYTHON, EVENT_EXTRACTION_URL, PLACE_BASE_NAME
from ..models import Document, Entity, Customer, Permission, Catalog, DocMarkEntity, DocMarkPlace, DocMarkTimeTag, \
    DocMarkEvent, DocMarkComment, EntityCategory
from ..serve.word_parse import extract_word_content


@blue_print.route("/doc_adc", methods=['POST'])
# @swag_from('../swagger/save_tagging_result.yml')
def doc_adc():
    doc_ids = request.json.get('doc_ids', [])
    a1 = jsonify({"event_list": get_event_list_from_docs(doc_ids),
                  "event_list_group_by_entities": get_event_list_from_docs_group_by_entities(doc_ids)})
    return a1


# 上传文档
@blue_print.route("/upload_doc", methods=['POST'])
# @swag_from(upload_doc_dict)
def upload_doc():
    try:
        catalog_id = request.form.get('catalog_id', 0)
        uid = request.form.get('uid', 0)
        file_list = request.files.getlist('file', None)
        catalog_id = int(catalog_id)

        for file_obj in file_list:
            path_filename = file_obj.filename
            path = path_filename.split("/")
            if path:
                path_catalog_name_list = [i.strip() for i in path[:-1]]
                if path_catalog_name_list:
                    with lock:
                        catalog_id = find_leaf_catalog_id(catalog_id, path_catalog_name_list, uid)

                if catalog_id:
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
                    customer = Customer.query.filter_by(id=uid).first()
                    if customer:
                        permission = Permission.query.filter_by(id=customer.permission_id).first()
                        if permission:
                            permission_id = permission.id

                        with open(file_savepath, 'rb') as f:
                            md5_hash = hashlib.md5(f.read())
                            file_md5 = md5_hash.hexdigest()

                        if file_md5:
                            doc = Document.query.filter_by(md5=file_md5, catalog_id=catalog_id).first()
                            if doc:
                                url = YC_TAGGING_PAGE_URL + "?doc_id={0}&uid={1}".format(doc.id, uid)
                                doc_power = doc.get_power() if doc else 0
                                cus_power = customer.get_power() if customer else 0
                                if cus_power:
                                    if doc_power <= cus_power:
                                        url += "&edit=1"
                                res = fail_res(data=url, msg="{0}文档已存在\n".format(path[-1]))
                            else:
                                datetime_now = datetime.datetime.now()
                                doc = Document(name=path[-1],
                                               category=os.path.splitext(filename)[1],
                                               savepath='/static/{0}'.format(save_filename),
                                               catalog_id=catalog_id,
                                               content=content_list,
                                               create_by=uid,
                                               create_time=datetime_now,
                                               permission_id=permission_id,
                                               status=0,
                                               keywords=keywords,
                                               md5=file_md5)

                                db.session.add(doc)
                                db.session.commit()

                                if YC_ROOT_URL_PYTHON:

                                    header = {"Content-Type": "application/json; charset=UTF-8"}
                                    url = YC_ROOT_URL_PYTHON + '/api/mark/result'
                                    new_str = '\r\n'.join(doc.content)
                                    body = {"content": new_str}

                                    data = json.dumps(body)
                                    yc_res = requests.post(url=url, data=data, headers=header)
                                    print("yc_res.status_code", yc_res.status_code)
                                    if yc_res.status_code in (200, 201):
                                        yc_res = yc_res.json()['data']
                                        res_entity = yc_res["entity"]
                                        res_place = yc_res["place"]
                                        res_time = yc_res["time"]
                                        res_concept = yc_res["concept"]
                                        # print("res_entity", res_entity)
                                        # print("res_place", res_place)
                                        # print("res_time", res_time)

                                        data_insert_entity = []
                                        for index, item_entity in enumerate(res_entity):
                                            entity_json = {}
                                            doc_mark_entity = DocMarkEntity(doc_id=doc.id, valid=1)
                                            if item_entity.get("word", ""):
                                                doc_mark_entity.word = item_entity["word"]
                                                entity_json["name"] = item_entity["word"]
                                            if item_entity.get("entity_id", 0):
                                                doc_mark_entity.entity_id = item_entity["entity_id"]
                                            if item_entity.get("entity_type_id", 0):
                                                entity_json["category_id"] = item_entity["entity_type_id"]
                                            if item_entity.get("word_count", ""):
                                                word_count_list = list(item_entity["word_count"].split(','))
                                                doc_mark_entity.appear_index_in_text = word_count_list

                                            db.session.add(doc_mark_entity)
                                            db.session.commit()
                                            item_entity["doc_mark_id"] = doc_mark_entity.id
                                            data_insert_entity.append(entity_json)
                                        # print("doc_mark_entity数据插入成功")

                                        for index, item_entity in enumerate(res_concept):
                                            entity_json = {}
                                            doc_mark_entity = DocMarkEntity(doc_id=doc.id, valid=1)
                                            if item_entity.get("word", ""):
                                                doc_mark_entity.word = item_entity["word"]
                                                entity_json["name"] = item_entity["word"]
                                            if item_entity.get("concept_id", 0):
                                                doc_mark_entity.entity_id = item_entity["concept_id"]
                                            if item_entity.get("concept_type_id", 0):
                                                entity_json["category_id"] = item_entity["concept_type_id"]
                                            if item_entity.get("word_count", ""):
                                                word_count_list = list(item_entity["word_count"].split(','))
                                                doc_mark_entity.appear_index_in_text = word_count_list

                                            db.session.add(doc_mark_entity)
                                            db.session.commit()
                                            item_entity["doc_mark_id"] = doc_mark_entity.id
                                            data_insert_entity.append(entity_json)

                                        data_insert_place = []
                                        # data_insert_location = []
                                        for index, item_place in enumerate(res_place):
                                            # location_json = {}
                                            doc_mark_place = DocMarkPlace(doc_id=doc.id, valid=1)
                                            if item_place.get("word", ""):
                                                doc_mark_place.word = item_place["word"]
                                                # data_insert_place.append(item_place["word"])
                                            if item_place.get("type", 0):
                                                doc_mark_place.type = item_place["type"]
                                            if item_place.get("place_id", 0):
                                                doc_mark_place.place_id = item_place["place_id"]

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
                                                if item_place.get("place_lon", ""):
                                                    doc_mark_place.place_lon = item_place("place_lon")
                                                    doc_mark_place.place_lon = place_lon
                                                # location_json["lon"] = item_place["place_lon"]
                                                if item_place.get("place_lat", ""):
                                                    doc_mark_place.place_lat = item_place["place_lat"]
                                                    doc_mark_place.place_lat = place_lat
                                                # location_json["lat"] = item_place["place_lat"]
                                            if item_place.get("word_count", ""):
                                                word_count_list = list(item_place["word_count"].split(','))
                                                doc_mark_place.appear_index_in_text = word_count_list

                                            # 经纬度都有值时添加到数据库中
                                            if doc_mark_place.type == 2:
                                                if doc_mark_place.place_lon and doc_mark_place.place_lat:
                                                    db.session.add(doc_mark_place)
                                                    db.session.commit()
                                                    item_place["doc_mark_id"] = doc_mark_place.id
                                                    # 合格的地名才同步es
                                                    data_insert_place.append(doc_mark_place.word)
                                            else:
                                                db.session.add(doc_mark_place)
                                                db.session.commit()
                                                item_place["doc_mark_id"] = doc_mark_place.id

                                                data_insert_place.append(doc_mark_place.word)

                                            # data_insert_location.append(location_json)
                                        # print("doc_mark_place数据插入成功")

                                        data_insert_date = []
                                        data_insert_time_range = []
                                        data_insert_time_period = []
                                        for index, item_time in enumerate(res_time):
                                            time_range_json = {}
                                            doc_mark_time_tag = DocMarkTimeTag(doc_id=doc.id, valid=1)
                                            if item_time.get("time_type", 0):
                                                doc_mark_time_tag.time_type = item_time["time_type"]
                                            if item_time.get("word", ""):
                                                doc_mark_time_tag.word = item_time["word"]
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
                                            item_time["doc_mark_id"] = doc_mark_time_tag.id
                                        # print("doc_mark_time_tag插入成功")

                                        doc.status = 2
                                        db.session.commit()

                                        print("yc_res: ", yc_res)

                                        # <editor-fold desc="返回event带解析封装接口">
                                        event_id_list = []
                                        event_res = {}
                                        event_res['content'] = doc.content
                                        event_res['result'] = yc_res
                                        header = {"Content-Type": "application/json; charset=UTF-8"}
                                        url = EVENT_EXTRACTION_URL + '/event_extraction'

                                        data = json.dumps(event_res)
                                        event_extraction_res = requests.post(url=url, data=data, headers=header)

                                        print("event_extraction_res.status_code", event_extraction_res.status_code)

                                        if event_extraction_res.status_code in (200, 201):
                                            data_insert_event = []

                                            for item in event_extraction_res.json()["result"]:
                                                event_json = {}
                                                doc_mark_event = DocMarkEvent(doc_id=doc.id, valid=1)
                                                if item.get("event_address", []):
                                                    doc_mark_event.event_address = item["event_address"]
                                                if item.get("event_class_id", 0):
                                                    doc_mark_event.event_class_id = item["event_class_id"]
                                                    event_json["event_class_id"] = item["event_class_id"]
                                                if item.get("event_category_id", 0):
                                                    doc_mark_event.event_type_id = item["event_category_id"]
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
                                                print(doc_mark_event.id)

                                                event_id_list.append(doc_mark_event.id)
                                                data_insert_event.append(event_json)
                                        else:
                                            res = fail_res(msg="调用event_extraction接口失败")
                                            return res
                                        # </editor-fold>

                                        # <editor-fold desc="调用yc文档预处理接口,eventIds暂时为空列表">
                                        eventIds = event_id_list
                                        header = {"Content-Type": "application/json; charset=UTF-8"}
                                        url = YC_ROOT_URL + '/doc/preprocess'
                                        body = {"docId": doc.id, "eventIds": eventIds}
                                        data = json.dumps(body)
                                        yc_res_event = requests.post(url=url, data=data, headers=header)

                                        print("yc_res_event.status_code", yc_res_event.status_code)
                                        # </editor-fold>
                                    else:
                                        res = fail_res(msg="上传成功，但预处理失败")
                                        return res

                                # 抽取id、name、content插入es数据库中
                                data_insert_json = [{
                                    "id": doc.id,
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
                                    "event_categories": data_insert_event
                                }]
                                an_catalog = Catalog.get_ancestorn_catalog(catalog_id)
                                doc_type_id = an_catalog.id if an_catalog else 0
                                if doc_type_id:
                                    data_insert_json[0]["doc_type"] = doc_type_id

                                url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
                                header = {"Content-Type": "application/json; charset=UTF-8"}
                                para = {"data_insert_index": "document",
                                        "data_insert_json": data_insert_json}

                                insert_result = requests.post(url + '/dataInsert', data=json.dumps(para),
                                                              headers=header)

                                url = YC_TAGGING_PAGE_URL + "?doc_id={0}&uid={1}".format(doc.id, uid)
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
        res = fail_res()
    return jsonify(res)


def find_leaf_catalog_id(parent_catalog_id, path_catalog_name_list, uid):
    if len(path_catalog_name_list) == 1:
        path_name = path_catalog_name_list[0]
        catalog = Catalog.query.filter_by(name=path_name).filter_by(parent_id=parent_catalog_id).first()
        if catalog:
            return catalog.id
        else:
            catalog = Catalog(name=path_name, parent_id=parent_catalog_id, create_by=uid,
                              create_time=datetime.datetime.now())
            db.session.add(catalog)
            db.session.commit()
            return catalog.id
    else:
        path_name = path_catalog_name_list.pop(0)
        catalog = Catalog.query.filter_by(name=path_name).filter_by(parent_id=parent_catalog_id).first()
        if catalog:
            return find_leaf_catalog_id(catalog.id, path_catalog_name_list, uid)
        else:
            catalog = Catalog(name=path_name, parent_id=parent_catalog_id, create_by=uid,
                              create_time=datetime.datetime.now())
            db.session.add(catalog)
            db.session.commit()
            return find_leaf_catalog_id(catalog.id, path_catalog_name_list, uid)


# 获得文档路径
@blue_print.route("/get_doc_realpath", methods=['GET'])
# @swag_from(get_doc_realpath_dict)
def get_doc_realpath():
    try:
        doc_id = request.args.get('doc_id', 0, type=int)
        doc = Document.query.filter_by(id=doc_id).first()

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
        docs = Document.query.all()
        doc_ids = [i.id for i in docs]
        res = modify_doc_es_doc_type(doc_ids)
    except Exception as e:
        print(str(e))
        res = fail_res()
    return jsonify(res)


# 修改doc在es中的doc_type（文档的祖目录id）
def modify_doc_es_doc_type(doc_ids):
    try:
        if isinstance(doc_ids, list):
            doc_list = Document.query.filter(Document.id.in_(doc_ids)).all()
            for doc in doc_list:
                # 获得es对应doc
                url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
                header = {"Content-Type": "application/json; charset=UTF-8"}
                search_json = {
                    "id": {"type": "id", "value": doc.id}
                }

                es_id_para = {"search_index": "document", "search_json": search_json}

                search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)
                try:
                    es_id = search_result.json()['data']['dataList'][0]
                except:
                    es_id = ''

                # 替换doc_type 修改es已有doc
                an_catalog = Catalog.get_ancestorn_catalog(doc.catalog_id)
                doc_type = an_catalog.id if an_catalog else 0
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
    catalog_id = request.json.get('catalog_id', 0)
    doc_ids = request.json.get('doc_ids', [])

    try:

        catalog = Catalog.query.filter_by(id=catalog_id).first()
        if not catalog:
            res = fail_res(msg="目标目录不存在")
        else:
            docs = Document.query.filter(Document.id.in_(doc_ids)).all()
            if docs:
                for doc in docs:
                    document_same = Document.query.filter(Document.md5 == doc.md5, Document.id != doc.id).first()
                    move_source_docs_to_target_catalog([doc], catalog_id)
                    res = success_res()
            else:
                res = fail_res(msg="移动文档不存在")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 移动文件到指定目录
def move_source_docs_to_target_catalog(source_docs=[], target_catalog_id=0):
    target_docs = Document.query.filter_by(catalog_id=target_catalog_id).all()

    # 重名：判断和处理重名文件；否则直接移动
    del_doc_id = []
    save_target_docs_dict = {i.md5: i for i in target_docs if i.md5 and i.id}
    for source_doc_item in source_docs:
        if source_doc_item.md5 in save_target_docs_dict:
            target_doc_item = save_target_docs_dict[source_doc_item.md5]
            if target_doc_item.status < 2 and source_doc_item.status > 1:
                # 目标文件未标注，移动文件已标注，删除目标文件
                del_doc_id.append(target_doc_item.id)
                source_doc_item.catalog_id = target_catalog_id
                modify_doc_es_doc_type([source_doc_item.id])
                db.session.commit()
            else:
                # 目标文件已标注，删除移动文件
                del_doc_id.append(source_doc_item.id)
        else:
            source_doc_item.catalog_id = target_catalog_id
            modify_doc_es_doc_type([source_doc_item.id])
            db.session.commit()
    delete_doc_in_pg_es(del_doc_id)


# 获取文档内容
@blue_print.route('/get_content', methods=['GET'])
# @swag_from(get_content_dict)
def get_content():
    try:
        doc_id = request.args.get('doc_id')
        doc = Document.query.filter_by(id=doc_id).first()
        res = doc.content if doc else []
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


# 更新文档信息
@blue_print.route('/modify_doc_info', methods=['PUT'])
# @swag_from(modify_doc_info_dict)
def modify_doc_info():
    try:
        doc_id = request.json.get('doc_id', 0)
        name = request.json.get('name', '')
        status = request.json.get('status', 0)

        doc = Document.query.filter_by(id=doc_id).first()
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
                "id": {"type": "id", "value": doc_id}
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
    doc_ids = request.json.get('doc_ids', [])
    customer_id = request.json.get('customer_id', 0)
    permission_flag = False
    status_flag = False
    try:
        customer = Customer.query.filter_by(id=customer_id).first()
        if customer:
            del_doc_ids = []
            for doc_id in doc_ids:
                doc = Document.query.filter_by(id=doc_id).first()
                if doc:
                    if doc.get_power() > customer.get_power():
                        permission_flag = True
                    else:
                        if doc.status < 2:
                            del_doc_ids.append(doc.id)
                        else:
                            status_flag = True

            delete_doc_in_pg_es(del_doc_ids)

            if del_doc_ids:
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
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 真实删除doc操作
def delete_doc_in_pg_es(doc_ids):
    try:
        for doc_id in doc_ids:
            doc = Document.query.filter_by(id=doc_id).first()
            if doc:
                db.session.delete(doc)
                db.session.commit()

        es_id_list = []  # 删除doc 对应esdoc的列表
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        for doc_id in doc_ids:
            header = {"Content-Type": "application/json; charset=UTF-8"}
            search_json = {
                'id': {'type': 'id', 'value': doc_id}
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
        customer_id = request.args.get('customer_id', 0, type=int)

        pagination = Document.query.filter_by(create_by=customer_id).order_by(Document.create_time.desc()).paginate(
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
        doc_id = request.args.get('doc_id', 0, type=int)
        doc = Document.query.filter_by(id=doc_id).first()
        customer = Customer.query.filter_by(id=doc.create_by, valid=1).first()
        permission = Permission.query.filter_by(id=customer.permission_id, valid=1).first()
        permission_list = Permission.query.filter_by(valid=1).all()
        lower_permission_id_list = []

        if not doc:
            doc_info = {
                "id": "",
                "name": "",
                "category": "",
                "create_time": "",
                "keywords": [],
                "pre_doc_id": 0,
                "next_doc_id": 0,
                "favorite": 0
            }
        else:

            # ----------------------- 获取上下篇文章 --------------------------
            lower_permission_id_list = []

            for item in permission_list:
                if permission.power >= item.power:
                    lower_permission_id_list.append(item.id)

            documentPrevious = Document.query.filter(Document.permission_id.in_(lower_permission_id_list),
                                                     Document.catalog_id == doc.catalog_id,
                                                     Document.create_time < doc.create_time).order_by(
                Document.create_time.desc()).first()
            documentNext = Document.query.filter(Document.permission_id.in_(lower_permission_id_list),
                                                 Document.catalog_id == doc.catalog_id,
                                                 Document.create_time > doc.create_time).order_by(
                Document.create_time).first()
            # ----------------------- 获取上下篇文章 END --------------------------

            # ----------------------- 根据目录id，获取根目录tab权限 -----------------------
            flag, ancestorn_catalog_tagging_tabs = True, []
            if doc.catalog_id:
                catalog = Catalog.query.filter_by(id=doc.catalog_id).first()
                if catalog:
                    an_catalog = Catalog.get_ancestorn_catalog(catalog.id)
                    if an_catalog:
                        flag, ancestorn_catalog_tagging_tabs = True, an_catalog.tagging_tabs
            # ----------------------- 根据目录id，获取根目录tab权限 END -----------------------

            doc_info = {
                "id": doc.id,
                "name": doc.name,
                "category": doc.category,
                "create_time": doc.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                "keywords": doc.keywords if doc.keywords else [],
                "pre_doc_id": documentPrevious.id if documentPrevious else 0,
                "next_doc_id": documentNext.id if documentNext else 0,
                "tagging_tabs": ancestorn_catalog_tagging_tabs if flag else [],
                "favorite": doc.is_favorite
            }
    except Exception as e:
        print(str(e))
        doc_info = {"id": "",
                    "name": "",
                    "category": "",
                    "create_time": "",
                    "keywords": [],
                    "pre_doc_id": 0,
                    "next_doc_id": 0,
                    "favorite": 0
                    }

    return jsonify(doc_info)


# 获取实体分页展示
@blue_print.route('/get_entity_in_list_pagination', methods=['GET'])
# @swag_from(get_entity_in_list_pagination_dict)
def get_entity_in_list_pagination():
    try:
        search = request.args.get("search", "")
        customer_id = request.args.get("customer_id", 0, type=int)
        cur_page = request.args.get("cur_page", 1, type=int)
        page_size = request.args.get("page_size", 10, type=int)

        res = {"data": [],
               "page_count": 0,
               "total_count": 0}
        doc_id_list = []
        if search:
            entitiy = Entity.query.filter(or_(Entity.name == search, Entity.synonyms.has_key(search))).first()
            if entitiy:
                category = EntityCategory.query.filter_by(id=entitiy.category_id, valid=1).first()
                if category.name == PLACE_BASE_NAME:
                    doc_mark_place_list = DocMarkPlace.query.filter_by(place_id=entitiy.id, valid=1).all()
                    for doc_mark_place in doc_mark_place_list:
                        doc_id_list.append(doc_mark_place.doc_id)
                else:
                    doc_mark_entity_list = DocMarkEntity.query.filter_by(entity_id=entitiy.id, valid=1).all()
                    for doc_mark_entity in doc_mark_entity_list:
                        doc_id_list.append(doc_mark_entity.doc_id)

                # if YC_ROOT_URL:
                #     url = YC_ROOT_URL + "/doc/get_entity_in_list_pagination"
                #     print(url, flush=True)
                #     resp = requests.get(url=url, params={"cusotmer_id": customer_id,
                #                                          "entity_id": entitiy.id,
                #                                          "cur_page": cur_page,
                #                                          "page_size": page_size})
                #
                #     print(resp.text, flush=True)
                    #rows = json.loads(resp.text).get("rows", [])
                    data = []
                    leader_ids = get_leader_ids()
                    for doc_id in list(set(doc_id_list)):
                        doc = Document.query.filter_by(id=doc_id).first()
                        if doc:
                            # i['name'] = doc.name
                            # i['create_username'] = Customer.get_username_by_id(doc.create_by)
                            # i['path'] = doc.get_full_path() if doc.get_full_path() else '已失效'
                            # i['extension'] = doc.category
                            # i['tag_flag'] = 1 if doc.status == 1 else 0
                            # i['status'] = doc.get_status_name()
                            # i['permission'] = 1 if Permission.judge_power(customer_id, doc.id) else 0
                            if leader_ids:
                                doc_mark_comments = DocMarkComment.query.filter(DocMarkComment.doc_id == doc.id,
                                                                                DocMarkComment.create_by.in_(
                                                                                    leader_ids),
                                                                                DocMarkComment.valid == 1).all()
                                #i["leader_operate"] = 1 if doc_mark_comments else 0
                                res = {
                                    "name": doc.name,
                                    "create_username": Customer.get_username_by_id(doc.create_by),
                                    'path': doc.get_full_path() if doc.get_full_path() else '已失效',
                                    'extension': doc.category,
                                    "tag_flag": 1 if doc.status == 1 else 0,
                                    'status': doc.get_status_name(),
                                    'permission': 1 if Permission.judge_power(customer_id, doc.id) else 0,
                                    'leader_operate': 1 if doc_mark_comments else 0
                                }
                            data.append(res)
                    res = {"data": data,
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
    customer_id = request.args.get("customer_id", 0, type=int)
    doc_id = request.args.get("doc_id", 0, type=int)
    doc = Document.query.filter_by(id=doc_id).first()
    cus = Customer.query.filter_by(id=customer_id).first()
    doc_power = doc.get_power() if doc else 0
    cus_power = cus.get_power() if cus else 0
    if cus_power:
        if doc_power <= cus_power:
            res = success_res(msg="可以打开")
        else:
            res = fail_res(msg="此文档权限较高，无法打开")
    else:
        res = fail_res(msg="无效用户，无法操作")

    return res


# 模糊文档搜索分页展示
@blue_print.route('/get_search_doc_pagination', methods=['GET'])
# @swag_from(get_search_panigation_dict)
def get_search_pagination():
    try:
        customer_id = request.args.get("customer_id", 0, type=int)
        search = request.args.get('search', "")
        search_type = request.args.get('search_type', "")
        page_size = request.args.get('page_size', 10, type=int)
        cur_page = request.args.get('cur_page', 1, type=int)
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
            doc_pg = Document.query.filter_by(id=doc['_source']['id']).first()
            if doc_pg:
                path = doc_pg.get_full_path() if doc_pg else '已失效'
                create_username = Customer.get_username_by_id(doc_pg.create_by) if doc_pg else '无效用户'
                if leader_ids:
                    doc_mark_comments = DocMarkComment.query.filter(DocMarkComment.doc_id == doc_pg.id,
                                                                    DocMarkComment.create_by.in_(leader_ids),
                                                                    DocMarkComment.valid == 1).all()

                    data_item = {
                        'id': doc['_source']['id'],
                        'name': doc['_source']['name'],
                        'create_username': create_username,
                        'path': path,
                        'create_time': doc['_source']['create_time'],
                        'tag_flag': 1 if doc_pg.status == 1 else 0,
                        "status": doc_pg.get_status_name(),
                        'extension': doc_pg.category,
                        "permission": 1 if Permission.judge_power(customer_id, doc_pg.id) else 0,
                        "leader_operate": 1 if doc_mark_comments else 0
                    }
                    data.append(data_item)

        total_count = len(data)

        if total_count >= page_size * cur_page:
            list_return = data[page_size * (cur_page - 1):page_size * cur_page]

        elif total_count < page_size * cur_page and total_count > page_size * (cur_page - 1):
            list_return = data[page_size * (cur_page - 1):]
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


# 高级搜索
@blue_print.route('/search_advanced', methods=['POST'])
# @swag_from('../swagger/search_advanced.yml')
def search_advanced():
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
        customer_id = request.json.get('customer_id', 0)

        # 其他搜索参数
        entities = request.json.get('entities', [])
        keywords = request.json.get('keywords', [])
        event_categories = request.json.get('event_categories', {})
        notes = request.json.get('notes', [])
        notes_content = request.json.get('notes_content', [])
        doc_type = request.json.get('doc_type', 0)
        content = request.json.get('content', "")
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        data_screen = get_es_doc(url, customer_id=customer_id, date=date, time_range=time_range,
                                 time_period=time_period, frequency=frequency,
                                 place=place, place_direction_distance=place_direction_distance, location=location,
                                 degrees=degrees, length=length, route=route, entities=entities, keywords=keywords,
                                 event_categories=event_categories,
                                 notes=notes, doc_type=doc_type, content=content, notes_content=notes_content)

        # 组装ids，和结构化数据
        ids = []
        for data in data_screen:
            if data.get("id", False):
                ids.append(data["id"])

        event_list = get_event_list_from_docs()

        final_data = {
            "doc": data_screen,
            "event_list": event_list
        }
    except Exception as e:
        print("Exception: ", str(e))
        final_data = {
            "doc": [],
            "event_list": []
        }
    return jsonify(final_data)  # doc:原来格式数据 event_list:事件数据


# 高级搜索 doc_type
@blue_print.route('/search_advanced_doc_type', methods=['POST'])
# @swag_from('../swagger/search_advanced_doc_type.yml')
def search_advanced_doc_type():
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
        customer_id = request.json.get('customer_id', 0)
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

        data_screen = get_es_doc(url, customer_id=customer_id, date=date, time_range=time_range,
                                 time_period=time_period, frequency=frequency,
                                 place=place, place_direction_distance=place_direction_distance, location=location,
                                 degrees=degrees, length=length, route=route, entities=entities, keywords=keywords,
                                 event_categories=event_categories,
                                 notes=notes, doc_type=doc_type, content=content, notes_content=notes_content)

        # 组装ids，和结构化数据
        doc_ids = []
        data_by_doc_id = {}
        for data in data_screen:
            if not data["name"]:
                doc = Document.query.filter_by(id=data['id']).first()
                if doc:
                    data["name"] = doc.name if doc else ""
            if data["name"]:
                if data.get("id", False):
                    doc_ids.append(data["id"])
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
        print(get_event_list_from_docs_group_by_entities(doc_ids), flush=True)

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


def get_event_list_from_docs(doc_ids=[], start_date='1000-01-01', end_date='9999-12-31'):
    # <editor-fold desc="construct into event_list from docs order by event_time">
    event_list = []
    if doc_ids:
        events = DocMarkEvent.query.filter(DocMarkEvent.doc_id.in_(doc_ids)).all()
        for i in events:
            if i.event_address and isinstance(i.event_address, list):
                place_ids = DocMarkPlace.query.with_entities(DocMarkPlace.place_id).filter(
                    DocMarkPlace.id.in_(i.event_address)).all()
                if place_ids:
                    place_ids = [i[0] for i in place_ids]
                    places = Entity.query.filter(Entity.id.in_(place_ids), Entity.valid == 1).all()
                    if places:
                        objects, subjects, form_time = [], [], ""

                        if i.event_object and isinstance(i.event_object, list) and i.event_subject:
                            object_id_list = i.event_object
                            object_id_list.extend(i.subject_object)
                            object_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_id).filter(
                                DocMarkEntity.id.in_(object_id_list)).all()
                            if object_ids:
                                object_ids = [i[0] for i in object_ids]
                                objects = Entity.query.filter(Entity.id.in_(object_ids), Entity.valid == 1).all()

                        # subject和object结合，返回给前端

                        if objects:
                            if i.event_time and isinstance(i.event_time, list):
                                mark_time_ids = i.event_time
                                times = DocMarkTimeTag.query.with_entities(DocMarkTimeTag.format_date).filter(
                                    DocMarkTimeTag.id.in_(mark_time_ids),
                                    or_(and_(DocMarkTimeTag.format_date.between(start_date, end_date),
                                             DocMarkTimeTag.time_type == 1),
                                        and_(DocMarkTimeTag.format_date > start_date,
                                             DocMarkTimeTag.format_date_end < end_date,
                                             DocMarkTimeTag.time_type == 2))
                                ).all()
                                for time_tag in times:
                                    item = {
                                        "datetime": time_tag.format_date,
                                        "place": [{
                                            "place_lat": place.latitude,
                                            "place_lon": place.longitude,
                                            "place_id": place.id,
                                            # "type": 1,
                                            "word": place.name,
                                        } for place in places],
                                        "title": i.title,
                                        "object": [i.name for i in objects],
                                        "event_id": i.id
                                    }
                                    event_list.append(item)
        # </editor-fold>
        event_list = sorted(event_list, key=lambda x: x.get('datetime', ''))
    return event_list


def get_event_list_from_docs_group_by_entities(doc_ids=[]):
    # <editor-fold desc="construct into event_list from docs group by subjects & objects order by event_time">
    event_list = []
    if doc_ids:
        event_dict = {}
        events = DocMarkEvent.query.filter(DocMarkEvent.doc_id.in_(doc_ids)).all()
        for i in events:
            if i.event_address and isinstance(i.event_address, list):
                place_ids = DocMarkPlace.query.with_entities(DocMarkPlace.place_id).filter(
                    DocMarkPlace.id.in_(i.event_address)).all()
                if place_ids:
                    place_ids = [i[0] for i in place_ids]
                    places = Entity.query.filter(Entity.id.in_(place_ids), Entity.valid == 1).all()
                    if places:
                        object_ids, subject_ids = [], []
                        objects, subjects, form_time = [], [], ""

                        if i.event_object and isinstance(i.event_object, list):
                            object_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_id).filter(
                                DocMarkEntity.id.in_(i.event_object)).all()
                            if object_ids:
                                object_ids = [i[0] for i in object_ids]
                                objects = Entity.query.filter(Entity.id.in_(object_ids), Entity.valid == 1).all()

                        if i.event_subject and isinstance(i.event_subject, list):
                            subject_ids = DocMarkEntity.query.with_entities(DocMarkEntity.entity_id).filter(
                                DocMarkEntity.id.in_(i.event_subject)).all()
                            if subject_ids:
                                subject_ids = [i[0] for i in subject_ids]
                                subjects = Entity.query.filter(Entity.id.in_(subject_ids), Entity.valid == 1).all()

                        # subject和object结合，返回给前端
                        objects.extend(subjects)
                        if objects:
                            if i.event_time and isinstance(i.event_time, list):
                                mark_time_ids = i.event_time
                                times = DocMarkTimeTag.query.with_entities(DocMarkTimeTag.format_date).filter(
                                    DocMarkTimeTag.id.in_(mark_time_ids),
                                    DocMarkTimeTag.time_type.in_(['1', '2'])).all()
                                if times:
                                    form_time = times[0]

                            if object_ids + subject_ids and form_time:
                                # 确立时间线的key值
                                timeline_key = ",".join([str(i) for i in sorted(list(set(object_ids + subject_ids)))])

                                item = {
                                    "datetime": form_time,
                                    "place": [{
                                        "place_lat": place.latitude,
                                        "place_lon": place.longitude,
                                        "place_id": place.id,
                                        # "type": 1,
                                        "word": place.name,
                                    } for place in places],
                                    "title": i.title,
                                    "object": [i.name for i in objects],
                                    "event_id": i.id
                                }

                                if event_dict.get(timeline_key, []):
                                    event_dict[timeline_key].append(item)
                                else:
                                    event_dict[timeline_key] = [item]
        # </editor-fold>
        event_list = [sorted(i, key=lambda x: x.get('datetime', '')) for i in event_dict.values()]
    return event_list


def get_doc_events_to_earth(doc_ids):
    doc_mark_event_list = DocMarkEvent.query.filter(DocMarkEvent.doc_id.in_(doc_ids)).all()
    result = []
    for doc_mark_event in doc_mark_event_list:
        places = doc_mark_event.get_places()
        place_list = [{
            "word": i.word,
            "place_id": i.place_id,
            "place_lon": i.place_lon,
            "place_lat": i.place_lat
        } for i in places if i.place_lon and i.place_lat]
        if place_list:
            datetime = ""
            if doc_mark_event.event_time:
                time_tag = DocMarkTimeTag.query.filter(DocMarkTimeTag.id.in_(doc_mark_event.event_time)).first()
                if time_tag:
                    if time_tag.format_date:
                        datetime = time_tag.format_date.strftime("%Y-%m-%d %H:%M:%S")
            if datetime:
                object_list = doc_mark_event.get_object_entity_names()
                object_list.extend(doc_mark_event.get_subject_entity_names())
                if object_list:
                    result.append({
                        "title": doc_mark_event.title,
                        "object": object_list,
                        "datetime": datetime,
                        "place": place_list,
                        "event_id": doc_mark_event.id})
    res = sorted(result, key=lambda x: x.get('datetime', ''))
    return res


def get_doc_events_to_earth_by_entities(doc_ids):
    doc_mark_event_list = DocMarkEvent.query.filter(DocMarkEvent.doc_id.in_(doc_ids)).all()
    event_dict = {}
    for doc_mark_event in doc_mark_event_list:
        places = doc_mark_event.get_places()
        place_list = [{
            "word": i.word,
            "place_id": i.place_id,
            "place_lon": i.place_lon,
            "place_lat": i.place_lat
        } for i in places if i.place_lon and i.place_lat]
        if place_list:
            datetime = ""
            if doc_mark_event.event_time:
                time_tag = DocMarkTimeTag.query.filter(DocMarkTimeTag.id.in_(doc_mark_event.event_time)).first()
                if time_tag:
                    if time_tag.format_date:
                        datetime = time_tag.format_date.strftime("%Y-%m-%d %H:%M:%S")
            if datetime:
                object_list = doc_mark_event.get_object_entity_names()
                object_list.extend(doc_mark_event.get_subject_entity_names())
                object_uni_list = list(set(object_list))
            if object_uni_list:

                # 确立时间线的key值
                timeline_key = ",".join([str(i) for i in sorted(object_uni_list)])

                item = {
                    "datetime": datetime,
                    "place": place_list,
                    "title": doc_mark_event.title,
                    "object": object_uni_list,
                    "event_id": doc_mark_event.id
                }

                if event_dict.get(timeline_key, []):
                    event_dict[timeline_key].append(item)
                else:
                    event_dict[timeline_key] = [item]
        # </editor-fold>
        res = [sorted(i, key=lambda x: x.get('datetime', '')) for i in event_dict.values()]
    return res


# 高级搜索结果doc_ids 筛选事件
@blue_print.route('/screen_event_by_time_range', methods=['POST'])
def get_events_by_doc_ids_and_time_range():
    try:
        doc_ids = request.json.get('doc_ids', [])
        start_time = request.json.get('start_time', '1900-01-01')
        end_time = request.json.get('end_time', '9999-12-31')
        res = get_event_list_from_docs(doc_ids, start_time, end_time)
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


# 高级搜索分页展示
@blue_print.route('/search_advanced_pagination', methods=['POST'])
# @swag_from('..swagger/search_advanced_pagination.yml')
def search_advanced_pagination():
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
    customer_id = request.json.get('customer_id', 0)
    page_size = request.json.get('page_size', 10)
    cur_page = request.json.get('cur_page', 1)

    # 其他搜索参数
    entities = request.json.get('entities', [])
    keywords = request.json.get('keywords', [])
    event_categories = request.json.get('event_categories', [])
    notes = request.json.get('notes', [])
    notes_content = request.json.get('notes_content', [])
    doc_type = request.json.get('doc_type', 0)
    content = request.json.get('content', "")
    url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
    data_screen = get_es_doc(url, customer_id=customer_id, date=date, time_range=time_range,
                             time_period=time_period, frequency=frequency,
                             place=place, place_direction_distance=place_direction_distance, location=location,
                             degrees=degrees, length=length, route=route, entities=entities, keywords=keywords,
                             event_categories=event_categories,
                             notes=notes, doc_type=doc_type, content=content, notes_content=notes_content)

    data_screen_res = []
    leader_ids = get_leader_ids()
    for data in data_screen:
        doc = Document.query.filter_by(id=data['id']).first()
        if doc:
            if not data["name"]:
                data["name"] = doc.name if doc else ""
            data['create_username'] = Customer.get_username_by_id(doc.create_by)
            data['path'] = doc.get_full_path() if doc.get_full_path() else '已失效'
            data['extension'] = doc.category
            data['tag_flag'] = 1 if doc.status == 1 else 0
            data['status'] = doc.get_status_name()
            data['permission'] = 1 if Permission.judge_power(customer_id, doc.id) else 0
            if leader_ids:
                doc_mark_comments = DocMarkComment.query.filter(DocMarkComment.doc_id == doc.id,
                                                                DocMarkComment.create_by.in_(
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

    '''
    list_return = []
    with open(os.path.join(os.getcwd(), 'static', 'search_advanced_pagination.json'), 'r', encoding='utf-8') as f:
        print("read search_advanced_doc_type.json")
        res_json = json.loads(f.read())
        list_return = res_json.get("data", [])
        for i in range(5):
            list_return += list_return
        total_count = len(list_return)
        list_return = list_return[page_size * (cur_page - 1):page_size * cur_page]
    '''

    res = {'data': list_return,
           'page_count': math.ceil(total_count / page_size),
           'total_count': total_count}

    return jsonify(res)


# 标记结果储存
@blue_print.route('/save_tagging_result', methods=['POST'])
# @swag_from('../swagger/save_tagging_result.yml')
def save_tagging_result():
    try:

        doc_id = request.json.get('doc_id', 0)
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
        if not doc_id:
            res = fail_res(msg="No doc_id")
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
                "id": {"type": "id", "value": doc_id}
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
                res = fail_res(msg="can't find doc by doc_id in ES")
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
        customer_id = request.args.get("uid", 0, type=int)
        doc = Document.query.filter_by(create_by=customer_id).order_by(Document.id.desc()).first()
        if doc and customer_id:
            url = YC_TAGGING_PAGE_URL + "?doc_id={0}&uid={1}&edit=1".format(doc.id, customer_id)
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
        doc_id = request.json.get("doc_id", 0)
        favorite = request.json.get("favorite", 0)
        print(type(doc_id))
        if isinstance(doc_id, str) and not doc_id.isdigit():
            res = fail_res(msg="文档id格式有误")
        elif isinstance(favorite, str) and not favorite.isdigit():
            res = fail_res(msg="收藏参数有误")
        else:
            doc_id = int(doc_id)
            favorite = int(favorite)
            doc = Document.query.filter_by(id=doc_id).first()
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


def get_es_doc(url, customer_id=0, date=[], time_range=[], time_period=[], place=[], place_direction_distance=[],
               location=[], degrees=[], length=[], route=[], entities=[], keywords=[], event_categories={}, notes=[],
               doc_type=0, content="", frequency=[], notes_content=[]):
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
        search_json["doc_type"] = {"type": "id", "value": doc_type}
    if search_json:
        search_json["sort"] = {"type": "normal", "sort": "create_time", "asc_desc": "desc"}

    # 直接es查询
    para = {"search_index": 'document', "search_json": search_json}
    header = {"Content-Type": "application/json"}
    esurl = url + "/searchCustom"
    search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
    data = [doc['_source'] for doc in search_result.json()['data']['dataList']]
    data_screen = screen_doc(data, time_range=time_range, degrees=degrees, entities=entities,
                             event_categories=event_categories)
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
            if ent["entity"] and ent["category_id"]:
                screen_dict["entities"]["entities"].append({ent["entity"]: ent["category_id"]})
            elif ent["entity"] and not ent["category_id"]:
                screen_dict["entities"]["name"].append(ent["entity"])
            elif not ent["entity"] and ent["category_id"]:
                screen_dict["entities"]["value"].append(ent["category_id"])
    if event_categories:
        screen_dict["event_categories"] = []
        for eve in event_categories:
            screen_dict["event_categories"].append({eve["event_class"]: eve["event_category_id"]})

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

            entities_values = [ent["category_id"] for ent in doc["entities"]]

            screen_entity_list = []

            for entity in screen_dict["entities"]["entities"]:
                key = list(entity.keys())[0]
                screen_entity_list.append({"name": key, "category_id": entity[key]})

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

            es_event_category_ids = [i.get("event_category_id", 0) for i in event_categories_dic]
            es_event_class_ids = [i.get("event_class_id", 0) for i in event_categories_dic]

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

#------------------处理经纬度----------------------------


def find_int_in_str(string):
    str_to_num = re.findall('(\d+)', string)[0]
    return int(str_to_num)


def find_dfm(dfm_string):
    d_ = find_int_in_str(dfm_string.split("°")[0])
    f_ = find_int_in_str(dfm_string.split("°")[1])
    return d_ + f_/60