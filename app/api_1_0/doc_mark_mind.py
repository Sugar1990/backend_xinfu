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


@blue_print.route('/add_doc_mark_mind', methods=['POST'])
def add_doc_mark_mind():
    try:
        name = request.json.get('name')
        parent_id = request.json.get('parent_id')
        doc_id = request.json.get('doc_id')
        doc_mark_mind_same = DocMarkMind.query.filter_by(doc_id=doc_id, name=name, parent_id=parent_id, valid=1).first()
        if doc_mark_mind_same:
            res = fail_res(msg="导图已存在")
        else:
            doc_mark_mind = DocMarkMind(doc_id=doc_id, name=name, parent_id=parent_id, valid=1)
            db.session.add(doc_mark_mind)
            db.session.commit()
            res = success_res()
    except:
        db.session.rollback()
        res = fail_res()

    return jsonify(res)


@blue_print.route('/modify_doc_mark_mind', methods=['PUT'])
def modify_doc_mark_mind():
    try:
        doc_mark_mind_id = request.json.get('id', 0)
        name = request.json.get('name', '')
        parent_id = request.json.get('parent_id', 0)
        doc_id = request.json.get('doc_id', 0)
        if isinstance(doc_mark_mind_id, int):
            doc_mark_mind = DocMarkMind.query.filter_by(id=doc_mark_mind_id, valid=1).first()
            if doc_mark_mind:
                doc_mark_mind_same = DocMarkMind.query.filter_by(doc_id=doc_id, name=name, parent_id=parent_id,
                                                                 valid=1).first()
                if doc_mark_mind_same:
                    res = fail_res(msg="导图已存在")
                else:
                    if doc_id:
                        doc_mark_mind.doc_id = doc_id
                    if name:
                        doc_mark_mind.name = name
                    if parent_id:
                        doc_mark_mind.parent_id = parent_id
                    db.session.commit()
                    res = success_res()
            else:
                res = fail_res(msg="id不存在!")
        else:
            res = fail_res("paramter \"id\" is not int type")

    except RuntimeError:
        db.session.rollback()
        res = fail_res(msg="修改失败！")
    return jsonify(res)


@blue_print.route('/delete_doc_mark_mind', methods=['POST'])
def delete_doc_mark_mind():
    try:
        doc_mark_mind_id = request.json.get("id", 0)
        if isinstance(doc_mark_mind_id, int):
            doc_mark_mind = DocMarkMind.query.filter_by(id=doc_mark_mind_id, valid=1).first()
            if doc_mark_mind:
                doc_mark_mind.valid = 0
                res = success_res()
            else:
                res = fail_res(msg="操作对象不存在!")
        else:
            res = fail_res("paramter \"id\" is not int type")
    except:
        db.session.rollback()
        res = fail_res(msg="删除失败！")

    return jsonify(res)


@blue_print.route('/get_doc_mark_mind', methods=['GET'])
def get_doc_mark_mind():
    try:
        result = []
        doc_mark_mind_doc_id = request.args.get("doc_id", 0, type=int)
        doc_mark_mind = DocMarkMind.query.filter_by(doc_id=doc_mark_mind_doc_id,parent_id=0, valid=1).first()
        if doc_mark_mind:
            get_ancestorn_doc_mark_mind(doc_mark_mind.id,result)
            res_temp = [{
                "id": doc_mark_mind.id,
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



def get_ancestorn_doc_mark_mind(id,result=[]):
     doc_mark_mind_children = DocMarkMind.query.filter_by(parent_id=id, valid=1).all()
     for item in doc_mark_mind_children:
         res = {
             "id": item.id,
             "name": item.name,
             "children":[]
         }
         get_ancestorn_doc_mark_mind(item.id, res["children"])
         result.append(res)




