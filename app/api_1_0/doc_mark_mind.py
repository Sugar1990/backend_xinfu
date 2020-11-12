# -*- coding:utf-8 -*-
# @Author :MaYuhui
# work_location: Bei Jing
# @File : doc_mark_mind.py 
# @Time : 2020/10/12 16:19

from flask import jsonify, request
from . import api_doc_mark_mind as blue_print
from ..models import DocMarkMind
from .. import db
from .utils import success_res, fail_res
import uuid


@blue_print.route('/add_doc_mark_mind', methods=['POST'])
def add_doc_mark_mind():
    try:
        name = request.json.get('name', '')
        parent_uuid = request.json.get('parent_uuid', None)
        doc_uuid = request.json.get('doc_uuid', None)
        doc_mark_mind_same = DocMarkMind.query.filter_by(doc_uuid=doc_uuid, name=name, parent_uuid=parent_uuid,
                                                         valid=1).first()
        if doc_mark_mind_same:
            res = fail_res(msg="导图已存在")
        else:
            doc_mark_mind = DocMarkMind(uuid=uuid.uuid1(), doc_uuid=doc_uuid, name=name, parent_uuid=parent_uuid,
                                        valid=1)
            db.session.add(doc_mark_mind)
            db.session.commit()
            res = success_res(data={"uuid": doc_mark_mind.uuid})
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/modify_doc_mark_mind', methods=['PUT'])
def modify_doc_mark_mind():
    try:
        doc_mark_mind_uuid = request.json.get('uuid', None)
        name = request.json.get('name', '')
        parent_uuid = request.json.get('parent_uuid', None)
        doc_uuid = request.json.get('doc_uuid', None)
        doc_mark_mind = DocMarkMind.query.filter_by(uuid=doc_mark_mind_uuid, valid=1).first()
        if doc_mark_mind:
            doc_mark_mind_same = DocMarkMind.query.filter_by(doc_uuid=doc_uuid, name=name, parent_uuid=parent_uuid,
                                                             valid=1).first()
            if doc_mark_mind_same:
                res = fail_res(msg="导图已存在")
            else:
                if doc_uuid:
                    doc_mark_mind.doc_uuid = doc_uuid
                if name:
                    doc_mark_mind.name = name
                if parent_uuid:
                    doc_mark_mind.parent_uuid = parent_uuid
                db.session.commit()
                res = success_res()
        else:
            res = fail_res(msg="uuid不存在!")

    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="修改失败！")
    return jsonify(res)


@blue_print.route('/delete_doc_mark_mind', methods=['POST'])
def delete_doc_mark_mind():
    try:
        doc_mark_mind_uuid = request.json.get("uuid", None)
        doc_mark_mind = DocMarkMind.query.filter_by(uuid=doc_mark_mind_uuid, valid=1).first()
        if doc_mark_mind:
            doc_mark_mind.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="操作对象不存在!")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


@blue_print.route('/get_doc_mark_mind', methods=['GET'])
def get_doc_mark_mind():
    try:
        result = []
        doc_mark_mind_doc_uuid = request.args.get("doc_uuid", None)
        doc_mark_mind = DocMarkMind.query.filter_by(doc_uuid=doc_mark_mind_doc_uuid, parent_uuid=None, valid=1).first()
        if doc_mark_mind:
            get_ancestorn_doc_mark_mind(doc_mark_mind.uuid, result)
            res_temp = [{
                "uuid": doc_mark_mind.uuid,
                "name": doc_mark_mind.name,
                "children": result
            }]
            res = success_res(data=res_temp)
        else:
            res = fail_res(data=[], msg="操作对象不存在!")

    except Exception as e:
        res_temp = []
        print(str(e))
        res = fail_res(data=res_temp)
    return jsonify(res)


def get_ancestorn_doc_mark_mind(uuid, result=[]):
    doc_mark_mind_children = DocMarkMind.query.filter_by(parent_uuid=uuid, valid=1).all()
    for item in doc_mark_mind_children:
        res = {
            "uuid": item.uuid,
            "name": item.name,
            "source": item._source,
            "doc_uuid": item.doc_uuid,
            "children": []
        }
        get_ancestorn_doc_mark_mind(item.uuid, res["children"])
        result.append(res)


@blue_print.route('/get_doc_mark_mind_by_parentId', methods=['GET'])
def get_doc_mark_mind_by_parentId():
    try:
        result = []
        parent_uuid = request.args.get("parent_uuid")
        if parent_uuid:
            doc_mark_mind = DocMarkMind.query.filter_by(parent_uuid=parent_uuid, valid=1).first()
            if doc_mark_mind:
                get_ancestorn_doc_mark_mind(doc_mark_mind.uuid, result)
                res_temp = [{
                    "uuid": doc_mark_mind.uuid,
                    "name": doc_mark_mind.name,
                    "_source": doc_mark_mind._source,
                    "children": result
                }]
                res = success_res(data=res_temp)
            else:
                res = fail_res(data=[], msg="操作对象不存在!")
        else:
            res = fail_res(msg="参数不能为空")

    except Exception as e:
        res_temp = []
        print(str(e))
        res = fail_res(data=res_temp)
    return jsonify(res)


@blue_print.route('/get_doc_mark_mind_by_ids', methods=['GET'])
def get_doc_mark_mind_by_ids():
    try:
        ids = request.args.get('uuid', '')
        if ids:
            doc_mark_mind = DocMarkMind.query.filter(DocMarkMind.uuid == ids, DocMarkMind.valid == 1).first()
            res = success_res(data={
                "uuid": doc_mark_mind.uuid,
                "name": doc_mark_mind.name,
                "doc_uuid": doc_mark_mind.doc_uuid,
                "parent_uuid": doc_mark_mind.parent_uuid,
                "_source": doc_mark_mind._source})
        else:
            res = fail_res(msg="参数不能为空")
    except Exception as e:
        print(str(e))
        res = fail_res(data={})
    return jsonify(res)
