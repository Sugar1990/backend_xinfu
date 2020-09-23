# from flasgger import swag_from
from flask import jsonify, request
import json
from . import api_initial as blue_print
from ..models import Customer, EntityCategory, Document, Catalog
from .. import db
from ..conf import ADMIN_NAME, ADMIN_PWD, ASSIS_NAME, ASSIS_PWD, TAG_TABS, PLACE_BASE_NAME, ES_SERVER_IP, ES_SERVER_PORT
from .utils import success_res, fail_res
import requests
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


@blue_print.route('/pg_insert_es', methods=['GET'])
# @swag_from(pg_insert_es_dict)
def pg_insert_es():
    pg_table = request.args.get('pg_table', '')  # 同步数据为entity或者document
    try:
        if pg_table == 'entity':
            es_mapping_dict = {
                "id": "id",
                "name": "ik_keyword",
                # "synonyms": "ik",
                # "props": "ik",
                "summary": "ik",
                "category_id": "id"
            }
            pg_dict = {"id": {"col_type": "align", "entity": "id"},
                       "name": {"col_type": "", "entity": "name"},
                       "synonyms": {"col_type": "", "entity": "synonyms"},
                       "props": {"col_type": "", "entity": "props"},
                       "category_id": {"col_type": "", "entity": "category_id"},
                       "summary": {"col_type": "", "entity": "summary"}}
        elif pg_table == 'document':
            es_mapping_dict = {
                "id": "id",
                "name": "ik_keyword",
                # "content": "ik",
                # "keywords": "ik",
                # "create_time": "time",
                # "dates": "ik",  # 多个时间，
                # "places": "ik",  # 多个地点
                # "entities": "ik",  # [{name: category_id}, …]  # 多个实体，含名称和类型id
                # "event_categories": "ik",  # [{event_class: event_category}, …]
                "doc_type": "id",
                # "notes": "ik"
            }
            pg_dict = {"id": {"col_type": "align", "document": "id"},
                       "name": {"col_type": "", "document": "name"},
                       "content": {"col_type": "", "document": "content"},
                       "keywords": {"col_type": "", "document": "keywords"},
                       "create_time": {"col_type": "", "document": "create_time"}
                       }

        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        header = {"Content-Type": "application/json"}
        esurl = url + "/pg_insert_es"
        para = {"pg_dict": pg_dict, "es_index_name": pg_table, "es_mapping_dict": es_mapping_dict}
        search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
        print(search_result, flush=True)
        res = success_res()
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/delete_index', methods=['GET'])
# @swag_from(delete_index_dict)
def delete_index():
    es_index = request.args.get('es_index', '')  # 删除数据为entity或者document
    try:
        if es_index == 'entity' or es_index == 'document':
            para = {"delete_index": es_index}
            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            esurl = url + "/deleteIndex"
            search_result = requests.get(url=esurl, params=para, headers={})
            res = success_res()
        else:
            res = fail_res(msg="only support es_index == 'entity' or es_index == 'document' ")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()
    return jsonify(res)


@blue_print.route('/update_es_doc', methods=['GET'])
# @swag_from(update_es_doc_dict)
def update_es_doc():
    try:
        docs = Document.query.all()
        url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
        header = {"Content-Type": "application/json; charset=UTF-8"}
        for doc in docs:
            doc_id = doc.id
            an_catalog = Catalog.get_ancestorn_catalog(doc.catalog_id)
            doc_type = an_catalog.id if an_catalog else 0

            # 获得es对应doc
            search_json = {
                "id": {"type": "id", "value": doc_id}
            }

            es_id_para = {"search_index": "document", "search_json": search_json}

            search_result = requests.post(url + '/searchId', data=json.dumps(es_id_para), headers=header)
            try:
                es_id = search_result.json()['data']['dataList'][0]
            except:
                es_id = ''
            # 替换name 修改es已有do
            key_value_json = {'doc_type': doc_type}
            inesert_para = {"update_index": 'document',
                            "data_update_json": [{es_id: key_value_json}]}
            requests.post(url + '/updatebyId', data=json.dumps(inesert_para), headers=header)
            res = success_res()
    except Exception as e:
        print(str(e))
        res = fail_res()
    return res


@blue_print.route('/pg_insert_es_test', methods=['GET'])
def pg_insert_test():
    pg_table = request.args.get('pg_table', '')  # 同步数据为entity或者document

    if pg_table == 'entity':
        es_mapping_dict = {
            "id": "id",
            "name": "ik_keyword",
            #"synonyms": "ik",
            #"props": "ik",
            "summary": "ik",
            "category_id": "id"
        }
        pg_dict = {"id": {"col_type": "align", "entity": "id"},
                   "name": {"col_type": "", "entity": "name"},
                   "synonyms": {"col_type": "", "entity": "synonyms"},
                   "props": {"col_type": "", "entity": "props"},
                   "category_id": {"col_type": "", "entity": "category_id"},
                   "summary": {"col_type": "", "entity": "summary"}}
    elif pg_table != 'entity':
        es_mapping_dict = {
            "id": "id",
            "name": "ik_keyword",
            "create_time": "time",

        }
        pg_dict = {"id": {"col_type": "align", pg_table: "id"},
                   "name": {"col_type": "", pg_table: "name"},
                   "content": {"col_type": "", pg_table: "content"},
                   "keywords": {"col_type": "", pg_table: "keywords"},
                   "create_time": {"col_type": "", pg_table: "create_time"},
                   "entities": {"col_type": "", pg_table: "entities"},
                   "event_categories": {"col_type": "", pg_table: "event_categories"},
                   "doc_type": {"col_type": "", pg_table: "doc_type"},
                   "place": {"col_type": "", pg_table: "place"},
                   "place_direction_distance": {"col_type": "", pg_table: "place_direction_distance"},
                   "location": {"col_type": "", pg_table: "location"},
                   "degrees": {"col_type": "", pg_table: "degrees"},
                   "length": {"col_type": "", pg_table: "length"},
                   "route": {"col_type": "", pg_table: "route"},
                   "notes": {"col_type": "", pg_table: "notes"},
                   "date": {"col_type": "", pg_table: "date"},
                   "time_range": {"col_type": "", pg_table: "time_range"},
                   "time_period": {"col_type": "", pg_table: "time_period"},
                   }

    url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
    header = {"Content-Type": "application/json"}
    esurl = url + "/pg_insert_es"
    para = {"pg_dict": pg_dict, "es_index_name": "document1", "es_mapping_dict": es_mapping_dict}
    print(para, flush=True)
    search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
    print(search_result, flush=True)
    return success_res()
