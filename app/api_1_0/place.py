from flask import jsonify, request

from . import api_place as blue_print
from ..models import Entity
from .. import db
import json
from .utils import success_res, fail_res


@blue_print.route('/get_search_pagination', methods=['GET'])
def get_search_pagination():
    cur_page = request.args.get('cur_page', 1, type=int)
    page_size = request.args.get('page_size', 15, type=int)
    search = request.args.get('search', '')

    data = []

    res = {
        "data": data,  # 当前页数据
        "total_count": 0,  # 总条目数
        "page_count": 0,  # 总页数
    }
    return jsonify(res)
