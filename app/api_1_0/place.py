from flask import jsonify, request
import requests
import json
import re

from . import api_place as blue_print
from ..conf import ES_SERVER_PORT, ES_SERVER_IP, PLACE_BASE_NAME, PLACE_BASE_SERVER_IP, USE_PLACE_SERVER, \
    PLACE_BASE_OLD_SERVER_IP
from ..models import Entity, EntityCategory
from .. import db
from .utils import success_res, fail_res


@blue_print.route('/get_search_pagination', methods=['GET'])
def get_search_pagination():
    try:
        search = request.args.get('search', "")
        page_size = request.args.get('page_size', 10, type=int)
        cur_page = request.args.get('cur_page', 1, type=int)

        # 不使用地名库服务，调es接口
        if not USE_PLACE_SERVER:
            catagory = EntityCategory.query.filter_by(name=PLACE_BASE_NAME, valid=1).first()
            category_id = catagory.id if catagory else 0

            url = f'http://{ES_SERVER_IP}:{ES_SERVER_PORT}'
            if not search:
                search_json = {}
            else:
                search_json = {"name": {"type": "text", "value": search, "boost": 5},
                               "synonyms": {"type": "text", "value": search, "boost": 1}}

            if category_id != 0:
                search_json['category_id'] = {"type": "id", "value": category_id}

            para = {"search_index": 'entity', "search_json": search_json, "pageSize": page_size,
                    "currentPage": cur_page}
            header = {"Content-Type": "application/json"}
            esurl = url + "/searchCustomPagination"
            search_result = requests.post(url=esurl, data=json.dumps(para), headers=header)
            total_count = search_result.json()['data']['totalCount']
            data = [{'id': entity['_source']['id'],
                     'name': entity['_source']['name'],
                     'props': entity['_source']['props'],
                     'synonyms': entity['_source']['synonyms'],
                     'summary': entity['_source']['summary'],
                     'category': EntityCategory.get_category_name(entity['_source']['category_id'])
                     } for entity in search_result.json()['data']['dataList']]

        else:
            data, total_count = get_place_from_base_server(page_size=page_size, cur_page=cur_page, search=search)

        res = {'data': data,
               'page_size': page_size,
               'cur_page': cur_page,
               'total_count': total_count}
    except Exception as e:
        print(str(e))
        res = []
    return jsonify(res)


# 调取地名服务
def get_place_from_base_server(page_size=10, cur_page=1, search=''):
    try:
        if not search:
            url = PLACE_BASE_OLD_SERVER_IP + '/query/batch'
            resp = requests.get(url, params={"limit": page_size, "offset": (cur_page - 1) * page_size})

            server_data = json.loads(resp.text)
            get_location = lambda x: re.search("POINT\((.*)\)", x).groups()
            data = [{
                "id": i.get('DMBS', ''),
                "name": i.get('DMMC', ''),
                "props": {"坐标": get_location(i.get('WZ', ''))[0]},
                "synonyms": [],
                "category": PLACE_BASE_NAME,
                "category_id": EntityCategory.get_category_id(PLACE_BASE_NAME),
            } for i in server_data]

            url = PLACE_BASE_SERVER_IP + '/query/count'
            resp = requests.get(url)
            total_count = int(resp.text) if resp.text else 0
        else:
            url = PLACE_BASE_SERVER_IP + '/query/placeName={0}'.format(search)
            resp = requests.get(url)

            server_data = json.loads(resp.text)
            get_location = lambda x: re.search("POINT\((.*)\)", x).groups()
            data = [{
                "id": i.get('DMBS', ''),
                "name": i.get('DMMC', ''),
                "props": {"坐标": get_location(i.get('WZ', ''))[0]},
                "synonyms": [],
                "category": PLACE_BASE_NAME,
                "category_id": EntityCategory.get_category_id(PLACE_BASE_NAME),
            } for i in server_data]

            total_count = page_size * cur_page

        return data, total_count
    except Exception as e:
        print(str(e))
        return [], 0
