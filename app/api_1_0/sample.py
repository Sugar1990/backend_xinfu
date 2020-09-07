from flask import jsonify, request

from . import api_relation_category as blue_print
from ..models import RelationCategory
from .. import db
import json
from .utils import success_res, fail_res


@blue_print.route('/paginate_ajax', methods=['GET'])
def paginate_ajax():
    ### 重要参数:(当前页和每页条目数)
    current_page = request.form.get('page', 1, type=int)
    page_size = request.form.get('pageSize', 15, type=int)
    ### 对应各个表名(我们已经分表，所以不需要):
    table_name = request.form.get('tablename')
    # 注意下面的order_by:(目前可以只实现以id排序查看，后续可能实现多种排序方式)
    pagination = RelationCategory.query.order_by(RelationCategory.id). \
        filter_by(TABLENAME=table_name). \
        paginate(current_page, page_size, False)

    data = []
    for item in pagination.items:
        data.append({
            ## 对应models.py中的字段
            "id": item.id,
            "commoncode": item.COMMONCODE,
            "name": item.name,
            "description": item.DESCRIPTION,
            "synonym": item.SYNONYM
        })
    data = {
        "type": 0,
        "totalCount": pagination.total,  # 总条目数
        "totalPage": pagination.pages,  # 总页数
        "data": data,  # 当前页数据
        "currentPage": pagination.page  # 当前页标记
    }
    return json.dumps(data)
