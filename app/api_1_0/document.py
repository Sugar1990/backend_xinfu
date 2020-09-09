# -*- coding: utf-8 -*-
import datetime
import hashlib
import json
import os

import requests
from flask import jsonify, request
from pypinyin import lazy_pinyin
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from . import api_document as blue_print
from .utils import success_res, fail_res, get_status_name
from .. import db, lock
from ..conf import LEXICON_IP, LEXICON_PORT, SUMMARY_IP, SUMMARY_PORT, YC_ROOT_URL, ES_SERVER_IP, ES_SERVER_PORT, \
    YC_TAGGING_PAGE_URL
from ..models import Document, Entity, Customer, Permission, Catalog
from ..serve.word_parse import extract_word_content


# 上传文档
@blue_print.route("/upload_doc", methods=['POST'])
def upload_doc():
    try:
        catalog_id = request.form.get('catalog_id', 0)
        uid = request.form.get('uid', 0)
        file_list = request.files.getlist('file', None)

        msg = ""
        for file_obj in file_list:
            path_filename = file_obj.filename
            path = path_filename.split("/")
            if path:
                path_catalog_name_list = [i.strip() for i in path[:-1]]
                if path_catalog_name_list:
                    with lock:
                        catalog_id = find_leaf_catalog_id(catalog_id, path_catalog_name_list, uid)

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
                        res = fail_res(msg="{0}文档已存在\n".format(path[-1]))
                    else:
                        doc = Document(name=path[-1],
                                       category=os.path.splitext(filename)[1],
                                       savepath='/static/{0}'.format(save_filename),
                                       catalog_id=catalog_id,
                                       content=content_list,
                                       create_by=uid,
                                       create_time=datetime.datetime.now(),
                                       permission_id=permission_id,
                                       status=0,
                                       keywords=keywords,
                                       md5=file_md5)

                        db.session.add(doc)
                        db.session.commit()

                        # 抽取id、name、content插入es数据库中
                        data_insert_json = [{
                            "id": doc.id,
                            "name": doc.name,
                            "content": doc.content,
                            "create_time": doc.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                            "keywords": doc.keywords
                        }]

                        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
                        header = {"Content-Type": "application/json; charset=UTF-8"}
                        para = {"data_insert_index": "document",
                                "data_insert_json": data_insert_json}

                        insert_result = requests.post(url + '/dataInsert', data=json.dumps(para),
                                                      headers=header)
                        print(insert_result.text)

                        if YC_ROOT_URL:
                            header = {"Content-Type": "application/x-form-urlencode; charset=UTF-8"}
                            url = YC_ROOT_URL + '/doc/preprocess?docId={0}'.format(doc.id)
                            yc_res = requests.post(url=url, headers=header)
                            print("doc_preprocess", yc_res)
                            doc.status = 1
                            db.session.commit()

                        res = success_res()
                else:
                    res = fail_res(msg="计算文件md5异常，上传失败")
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
def get_doc_realpath():
    try:
        doc_id = request.args.get('doc_id', 0, type=int)
        doc = Document.query.filter_by(id=doc_id).first()

        res = doc.savepath.replace('\n\"', '') if doc else ""
    except Exception as e:
        print(str(e))
        res = ""
    return jsonify(res)


# 获取文档内容
@blue_print.route('/get_content', methods=['GET'])
def get_content():
    try:
        doc_id = request.args.get('doc_id')
        doc = Document.query.filter_by(id=doc_id).first()
        res = doc.content if doc else []
    except:
        res = []
    return jsonify(res)


# 更新文档信息
@blue_print.route('/modify_doc_info', methods=['PUT'])
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
def del_doc():
    doc_ids = request.json.get('doc_ids', [])
    customer_id = request.json.get('customer_id', 1)
    permission_flag = False
    try:
        customer = Customer.query.filter_by(id=customer_id).first()
        if customer:
            if doc_ids:
                Document.query.filter(Document.id.in_(doc_ids)).delete(synchronize_session=False)
                db.session.commit()
            power_ids = []
            for doc_id in doc_ids:
                doc = Document.query.filter_by(id=doc_id).first()
                if doc:
                    if doc.get_power() > customer.get_power():
                        permission_flag = True
                    else:
                        power_ids.append(doc.id)
                        db.session.delete(doc)
            db.session.commit()

            success_msg = "操作成功，其中部分文档权限不够，无法删除" if permission_flag else ''

            es_id_list = []  # 删除doc 对应esdoc的列表
            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            for doc_id in power_ids:

                header = {"Content-Type": "application/json; charset=UTF-8"}
                search_json = {
                    'id': {'type': 'id', 'value': doc_id}
                }
                es_id_para = {"search_index": "document", "search_json": search_json}

                search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)

                try:
                    list_out = search_result.json()['data']['dataList']

                    if list_out:
                        es_id_list.append(list_out[0])
                except:
                    print('eval_error', flush=True)
            try:
                if es_id_list:
                    delete_para = {"delete_index": "document", "id_json": es_id_list}
                    search_result = requests.post(url + '/deletebyId', data=json.dumps(delete_para), headers=header)
                    res = success_res(msg=success_msg)
                else:
                    print('No_delete')
            except:
                pass
            res = success_res()
        else:
            res = fail_res(msg='无效用户，操作失败')
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 获取上传历史
@blue_print.route('/get_upload_history', methods=['GET'])
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
def get_info():
    try:
        doc_id = request.args.get('doc_id', 0, type=int)
        doc = Document.query.filter_by(id=doc_id).first()
        customer = Customer.query.filter_by(id=doc.create_by, valid=1).first()
        permission = Permission.query.filter_by(id=customer.permission_id, valid=1).first()
        permission_list = Permission.query.filter_by(valid=1).all()
        lower_permission_id_list = []

        for item in permission_list:
            if permission.power >= item.power:
                lower_permission_id_list.append(item.id)

        documentPrevious = Document.query.filter(Document.permission_id.in_(lower_permission_id_list),
                                                 Document.create_time < doc.create_time).order_by(
            Document.create_time.desc()).first()
        documentNext = Document.query.filter(Document.permission_id.in_(lower_permission_id_list),
                                             Document.create_time > doc.create_time).order_by(
            Document.create_time).first()

        if not doc:
            doc_info = {
                "id": "",
                "name": "",
                "category": "",
                "create_time": "",
                "keywords": [],
                "pre_doc_id": 0,
                "next_doc_id": 0
            }
        else:
            if doc.catalog_id:
                catalog = Catalog.query.filter_by(id=doc.catalog_id).first()
                flag, ancestorn_catalog_tagging_tabs = get_ancestorn_catalog_tagging_tabs(catalog)
            else:
                flag, ancestorn_catalog_tagging_tabs = True, []
            doc_info = {
                "id": doc.id,
                "name": doc.name,
                "category": doc.category,
                "create_time": doc.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                "keywords": doc.keywords if doc.keywords else [],
                "pre_doc_id": documentPrevious.id if documentPrevious else 0,
                "next_doc_id": documentNext.id if documentNext else 0,
                "tagging_tabs": ancestorn_catalog_tagging_tabs if flag else []
            }
    except Exception as e:
        print(str(e))
        doc_info = {"id": "",
                    "name": "",
                    "category": "",
                    "create_time": "",
                    "keywords": [],
                    "pre_doc_id": 0,
                    "next_doc_id": 0
                    }

    return jsonify(doc_info)


# 递归查询父目录id
def get_ancestorn_catalog_tagging_tabs(catalog):
    if not catalog.parent_id:
        return True, catalog.tagging_tabs
    else:
        tmp_catalog = Catalog.query.filter_by(id=catalog.parent_id).first()
        if not tmp_catalog:
            return False, []
        return get_ancestorn_catalog_tagging_tabs(tmp_catalog)


# 获取实体分页展示
@blue_print.route('/get_entity_in_list_pagination', methods=['GET'])
def get_entity_in_list_pagination():
    try:
        search = request.args.get("search", "")
        cusotmer_id = request.args.get("cusotmer_id", 0, type=int)
        cur_page = request.args.get("cur_page", 1, type=int)
        page_size = request.args.get("page_size", 10, type=int)

        res = {"data": [],
               "page_count": 0,
               "total_count": 0}
        if search:
            entitiy = Entity.query.filter(or_(Entity.name == search, Entity.synonyms.has_key(search))).first()
            if entitiy:
                if YC_ROOT_URL:
                    url = YC_ROOT_URL + "/doc/get_entity_in_list_pagination"
                    resp = requests.get(url=url, params={"cusotmer_id": cusotmer_id,
                                                         "entity_id": entitiy.id,
                                                         "cur_page": cur_page,
                                                         "page_size": page_size})

                    data = json.loads(resp.text).get("rows", [])
                    count = json.loads(resp.text).get("total", 0)
                    for i in data:
                        i['create_username'] = '无效用户'
                        doc = Document.query.filter_by(id=i["id"]).first()
                        if doc:
                            i['name'] = doc.name
                            i['create_username'] = Customer.get_username_by_id(doc.create_by)
                            i['path'] = doc.get_full_path() if doc.get_full_path() else '已失效'
                    res = {"data": data,
                           "page_count": int(count / page_size) + 1,
                           "total_count": count}
    except Exception as e:
        res = {"data": [],
               "page_count": 0,
               "total_count": 0}

    return jsonify(res)


# 判断文档权限
@blue_print.route('/judge_doc_permission', methods=['GET'])
def judge_doc_permission():
    customer_id = request.args.get("customer_id", 0, type=int)
    doc_id = request.args.get("doc_id", 0, type=int)
    doc = Document.query.filter_by(id=doc_id).first()
    cus = Customer.query.filter_by(id=customer_id).first()
    doc_power = doc.get_power() if doc else 0
    cus_power = cus.get_power() if cus else 0
    if cus_power:
        if doc_power <= cus_power:
            res = success_res()
        else:
            res = fail_res(msg="此文档权限较高，无法打开")
    else:
        res = fail_res(msg="无效用户，无法操作")

    return res


# 模糊文档搜索分页展示
@blue_print.route('/get_search_doc_panigation', methods=['GET'])
def get_search_panigation():
    try:
        customer_id = request.args.get("customer_id", 0, type=int)
        document_name = request.args.get('search', "")
        page_size = request.args.get('page_size', 10, type=int)
        cur_page = request.args.get('cur_page', 1, type=int)
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        if not document_name:
            search_json = {}
        else:
            search_json = {"name": {"type": "text", "value": document_name, "boost": 1},
                           "sort": {"type": "normal", "sort": "create_time", "asc_desc": "desc"}}
        para = {"search_index": 'document', "search_json": search_json}
        header = {"Content-Type": "application/json"}
        esurl = url + "/searchCustom"

        search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
        # print(search_result, flush=True)
        data = []

        for doc in search_result.json()['data']['dataList']:
            doc_pg = Document.query.filter_by(id=doc['_source']['id']).first()
            path = doc_pg.get_full_path() if doc_pg else '已失效'
            create_username = Customer.get_username_by_id(doc_pg.create_by) if doc_pg else '无效用户'
            data_item = {
                'id': doc['_source']['id'],
                'name': doc['_source']['name'],
                'create_username': create_username,
                'path': path,
                'create_time': doc['_source']['create_time'],
                "status": get_status_name(doc_pg.status),
                "permission": 1 if Permission.judge_power(customer_id, doc_pg.id) else 0
            }
            data.append(data_item)

        total_count = len(data)

        if total_count > page_size * cur_page:
            list_return = data[page_size * (cur_page - 1):page_size * cur_page]

        elif total_count < page_size * cur_page and total_count > page_size * (cur_page - 1):
            list_return = data[page_size * (cur_page - 1):]
        else:
            list_return = []
        # print(esurl, para, flush=True)
        res = {'data': list_return,
               'page_count': int(total_count / page_size) + 1,
               'total_count': total_count}
    except Exception as e:
        print(str(e))
        res = {'data': [],
               'page_count': 0,
               'total_count': 0}
    return jsonify(res)


# 高级搜索
@blue_print.route('/search_advanced', methods=['POST'])
def search_advanced():
    # doc_id = request.json.get('doc_id', 0)
    dates = request.json.get('dates', [])
    places = request.json.get('places', [])
    entities = request.json.get('entities', [])
    keywords = request.json.get('keywords', [])
    event_categories = request.json.get('event_categories', {})
    notes = request.json.get('notes', [])
    doc_type = request.json.get('doc_type', "")
    content = request.json.get('content', "")
    start_date = request.json.get('start_date', "")
    end_date = request.json.get('end_date', "")
    url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'

    search_json = {}
    if content:
        search_json["name"] = {"type": "text", "value": content, "boost": 3}
        search_json["content"] = {"type": "text", "value": content, "boost": 1}
    if dates:
        if type(dates).__name__ == 'str':
            dates = dates.split(' - ')
        search_json["dates"] = {"type": "text", "value": ''.join(dates), "boost": 1}
    if keywords:
        search_json["keywords'"] = {"type": "text", "value": ''.join(keywords), "boost": 1}
    if places:
        if type(places).__name__ == 'str':
            places = places.split(' ')

            # search_json["places"] = {"type": "text", "value": ''.join(places), "boost": 1}
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
    data_screen = screen_doc(data, places=places, entities=entities, event_categories=event_categories,
                             notes=notes)

    # 组装ids，和结构化数据
    ids = []
    for data in data_screen:
        if data.get("id", False):
            ids.append(data["id"])

    # 雨辰接口
    if YC_ROOT_URL:
        body = {}
        if ids:
            body["ids"] = ids
        if start_date:
            body["startTime"] = start_date
        if end_date:
            body["endTime"] = end_date
        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = YC_ROOT_URL + "/event/listByDocIds"
        search_result = requests.post(url, data=json.dumps(body), headers=header)
        # print("/event/listByDocIds", search_result.text)
        final_data = {
            "doc": data_screen,
            "event_list": search_result.json()['data']
        }
    return jsonify(final_data)  # doc:原来格式数据 event_list:事件数据


def screen_doc(data_inppt, dates=[], places=[], entities=[], event_categories=[], notes=[]):
    data_output = []
    screen_dict = {}
    if dates:
        screen_dict["dates"] = dates
    if places:
        screen_dict["places"] = places
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
    if notes:
        screen_dict["notes"] = notes
    true_value = len(screen_dict)
    for doc in data_inppt:
        sum_bool = 0
        if dates and doc.get("dates", False):
            if type(doc["dates"]).__name__ == "str":
                dates_dic = eval(doc["dates"])
            else:
                dates_dic = doc["dates"]
            date_bool = bool([date for date in dates_dic if date in screen_dict["dates"]])
            sum_bool += date_bool
        else:
            date_bool = False
        if places and doc.get("places", False):
            if type(doc["places"]).__name__ == "str":
                places_dic = eval(doc["places"])
            else:
                places_dic = doc["places"]
            place_bool = bool([place for place in places_dic if place in screen_dict["places"]])
            sum_bool += place_bool
        else:
            place_bool = False
        if notes and doc.get("notes", False):
            if type(doc["notes"]).__name__ == "str":
                notes_dic = eval(doc["notes"])
            else:
                notes_dic = doc["notes"]
            note_bool = bool([note for note in notes_dic if note in screen_dict["notes"]])
            sum_bool += note_bool
        else:
            note_bool = False

        if entities and doc.get("entities", False):
            entites_bool = True
            if type(doc["entities"]).__name__ == "str":
                entities_dic = [{ent: eval(doc["entities"])[ent]}
                                for ent in eval(doc["entities"])]
            else:
                entities_dic = [{ent: doc["entities"][ent]}
                                for ent in doc["entities"]]

            entities_names = [ent for ent in eval(doc["entities"])]

            entities_values = list(eval(doc["entities"]).values())

            for entity in screen_dict["entities"]["entities"]:
                if entity not in entities_dic:
                    entites_bool = False
                    break
            if entites_bool and screen_dict["entities"]["name"]:
                for entity_name in screen_dict["entities"]["name"]:
                    if entity_name not in entities_names:
                        entites_bool = False
                        break
            if entites_bool and screen_dict["entities"]["value"]:
                for entity_value in screen_dict["entities"]["value"]:
                    if entity_value not in entities_values:
                        entites_bool = False
                        break

            sum_bool += entites_bool

        if event_categories and doc.get("event_categories", False):
            if type(doc["event_categories"]).__name__ == "str":
                event_categories_dic = eval(doc["event_categories"])
            else:
                event_categories_dic = doc["event_categories"]

            event_value = list(screen_dict["event_categories"][0].values())[0]

            event_key = list(screen_dict["event_categories"][0].keys())[0]

            if event_categories_dic.get(event_key, False):
                if event_value:
                    if event_value in event_categories_dic[str(event_key)]:
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


# 标记结果储存
@blue_print.route('/save_tagging_result', methods=['POST'])
def save_tagging_result():
    try:

        doc_id = request.json.get('doc_id', 0)
        dates = request.json.get('dates', [])
        places = request.json.get('places', [])
        entities = request.json.get('entities', [])
        event_categories = request.json.get('event_categories', [])
        notes = request.json.get('notes', [])
        keywords = request.json.get('keywords', [])
        doc_type = request.json.get('doc_type', 0)
        if not doc_id:
            res = fail_res(msg="No doc_id")
        else:
            # 替换相应属性,修改es已有doc,如果传递参数做修改，没有传的参数不做修改
            key_value_json = {}
            if dates:
                key_value_json["dates"] = dates
            if places:
                key_value_json["places"] = places
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
            if es_id:
                # print(key_value_json, flush=True)
                inesert_para = {"update_index": 'document',
                                "data_update_json": [{es_id: key_value_json}]}
                # print(inesert_para, flush=True)
                requests.post(url + '/updatebyId', data=json.dumps(inesert_para), headers=header)
                res = success_res()
            else:
                res = fail_res(msg="can't find doc by doc_id in ES")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


# 高级搜索分页展示
@blue_print.route('/search_advanced_Pagination', methods=['POST'])
def search_advanced_Pagination():
    # doc_id = request.json.get('doc_id', 0)
    page_size = request.json.get('page_size', 10)
    cur_page = request.json.get('cur_page', 1)
    dates = request.json.get('dates', [])
    places = request.json.get('places', [])
    entities = request.json.get('entities', [])
    keywords = request.json.get('keywords', [])
    event_categories = request.json.get('event_categories', {})
    notes = request.json.get('notes', [])
    doc_type = request.json.get('doc_type', 0)
    content = request.json.get('content', "")
    url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'

    search_json = {}
    if content:
        search_json["name"] = {"type": "text", "value": content, "boost": 3}
        search_json["content"] = {"type": "text", "value": content, "boost": 1}
    if dates:
        if type(dates).__name__ == 'str':
            dates = dates.split(' - ')
        search_json["dates"] = {"type": "text", "value": ''.join(dates), "boost": 1}
    if keywords:
        search_json["keywords'"] = {"type": "text", "value": ''.join(keywords), "boost": 1}
    if places:
        if type(places).__name__ == 'str':
            places = places.split(' ')

        # search_json["places"] = {"type": "text", "value": ''.join(places), "boost": 1}
    if doc_type:
        search_json["doc_type"] = {"type": "id", "value": doc_type}
    if search_json:
        search_json["sort"] = {"type": "normal", "sort": "create_time", "asc_desc": "desc"}

    # 直接es查询
    para = {"search_index": 'document', "search_json": search_json}
    header = {"Content-Type": "application/json"}
    esurl = url + "/searchCustom"
    search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
    # print(search_result['data']['dataList'][0]['_source'], flush=True)
    data = [doc['_source'] for doc in search_result.json()['data']['dataList']]
    data_screen = screen_doc(data, places=places, entities=entities, event_categories=event_categories,
                             notes=notes)  # dates=dates,

    total_count = len(data_screen)
    if total_count > page_size * cur_page:
        list_return = data_screen[page_size * (cur_page - 1):page_size * cur_page]

    elif total_count < page_size * cur_page and total_count > page_size * (cur_page - 1):
        list_return = data_screen[page_size * (cur_page - 1):]
    else:
        list_return = []

    res = {'data': list_return,
           'page_count': int(total_count / page_size) + 1,
           'total_count': total_count}
    return jsonify(res)


# 获取最新上传文档的标注页面地址
@blue_print.route('/get_latest_upload_file_tagging_url', methods=['GET'])
def get_latest_upload_file_tagging_url():
    try:
        customer_id = request.args.get("uid", 0, type=int)
        doc = Document.query.filter_by(create_by=customer_id).first()
        if doc and customer_id:
            url = YC_TAGGING_PAGE_URL + "?doc_id={0}&uid={1}".format(doc.id, customer_id)
            res = success_res(data=url)
        else:
            res = fail_res(data="/#")
    except:
        res = fail_res(data="/#")
    return res


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
