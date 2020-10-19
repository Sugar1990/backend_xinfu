# -*- coding: UTF-8 -*-
from flask import jsonify, request
from sqlalchemy import or_, and_

from . import api_doc_mark_comment as blue_print
from ..models import DocMarkComment
from .. import db
from .utils import success_res, fail_res
import time


# 按id查询
@blue_print.route('/get_doc_mark_comment_by_id', methods=['GET'])
def get_doc_mark_comment_by_id():
    try:
        id = request.args.get("id", 0, type=int)
        doc_mark_comment = DocMarkComment.query.filter_by(id=id, valid=1).first()
        if doc_mark_comment:
            res = success_res({
                "id": doc_mark_comment.id,
                "doc_id": doc_mark_comment.doc_id,
                "name": doc_mark_comment.name,
                "position": doc_mark_comment.position,
                "comment": doc_mark_comment.comment,
                "create_by": doc_mark_comment.create_by,
                "create_time": doc_mark_comment.create_time.strftime("%Y--%m--%d %H:%M:%S") if doc_mark_comment.create_time else None,
                "update_by": doc_mark_comment.update_by,
                "update_time": doc_mark_comment.update_time.strftime("%Y--%m--%d %H:%M:%S") if doc_mark_comment.update_time else None
            })
        else:
            res = fail_res(msg="批注数据不存在")


    except Exception as e:
        print(str(e))
        res = fail_res({
            "id": -1,
            "doc_id": -1,
            "name": "",
            "position": "",
            "comment": "",
            "create_by": -1,
            "create_time": None,
            "update_by": -1,
            "update_time": None
        })

    return jsonify(res)


# 按doc_id查询
@blue_print.route('/get_doc_mark_comment_by_doc_id', methods=['GET'])
def get_doc_mark_comment_by_doc_id():
    try:
        doc_id = request.args.get("doc_id", 0, type=int)
        doc_mark_comment_list = DocMarkComment.query.filter_by(doc_id=doc_id, valid=1).all()
        if doc_mark_comment_list:
            res = success_res(data=[{
                "id": i.id,
                "doc_id": i.doc_id,
                "name": i.name,
                "position": i.position,
                "comment": i.comment,
                "create_by": i.create_by,
                "create_time": i.create_time.strftime("%Y--%m--%d %H:%M:%S") if i.create_time else None,
                "update_by": i.update_by,
                "update_time": i.update_time.strftime("%Y--%m--%d %H:%M:%S") if i.update_time else None
            } for i in doc_mark_comment_list])
        else:
            res = fail_res(msg="批注数据不存在")


    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


# add
@blue_print.route('/add_doc_mark_comment', methods=['POST'])
def add_doc_mark_comment():
    try:
        doc_id = request.json.get("doc_id", 0)
        name = request.json.get("name", "")
        position = request.json.get("position", "")
        comment = request.json.get("comment", "")
        create_by = request.json.get("create_by", 0)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_by = request.json.get("update_by", 0)
        update_time = request.json.get("update_time", None)



        if not (isinstance(doc_id, int) and isinstance(create_by, int) and isinstance(update_by, int)):
            res =fail_res(msg="参数 \"doc_id\"、\"create_by\"、\"update_by\" 应是整数类型")

        else:
            doc_mark_comment_same = DocMarkComment.query.filter_by(doc_id=doc_id, name=name,
                                                                   position=position, comment=comment, valid=1).first()
            if doc_mark_comment_same:
                res = fail_res(msg="相同批注已存在")
            else:
                doc_mark_comment = DocMarkComment(doc_id=doc_id, name=name, position=position,
                                                  comment=comment, create_by=create_by, create_time=create_time,
                                                  update_by=update_by, update_time=update_time, valid=1)
                db.session.add(doc_mark_comment)
                db.session.commit()
                res = success_res(data={"id":doc_mark_comment.id})


    except Exception as e:
        print(str(e))
        res = fail_res()

    return jsonify(res)


# modify
@blue_print.route('/modify_doc_mark_comment', methods=['PUT'])
def modify_doc_mark_comment():
    try:
        id = request.json.get("id", 0)
        doc_id = request.json.get("doc_id", 0)
        name = request.json.get("name", "")
        position = request.json.get("position", "")
        comment = request.json.get("comment", "")
        create_by = request.json.get("create_by", 0)
        create_time = request.json.get("create_time", None)
        update_by = request.json.get("update_by", 0)
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        if not (isinstance(id, int) and isinstance(doc_id, int)
                and isinstance(create_by, int) and isinstance(update_by, int)):
            res = fail_res(msg="参数 \"id\"、\"doc_id\" 、\"create_by\"、\"update_by\"应是整数类型")

        else:
            doc_mark_comment_same = DocMarkComment.query.filter_by(doc_id=doc_id, name=name,
                                                                 position=position, comment=comment, valid=1).first()
            if doc_mark_comment_same:
                res = fail_res(msg="相同批注已存在")
            else:
                doc_mark_comment = DocMarkComment.query.filter_by(id=id, valid=1).first()
                if doc_mark_comment:
                    if doc_id:
                        doc_mark_comment.doc_id = doc_id
                    if name:
                        doc_mark_comment.name = name
                    if position:
                        doc_mark_comment.position = position
                    if comment:
                        doc_mark_comment.comment = comment
                    if create_by:
                        doc_mark_comment.create_by = create_by
                    if create_time:
                        doc_mark_comment.create_time = create_time
                    if update_by:
                        doc_mark_comment.update_by = update_by
                    if update_time:
                        doc_mark_comment.update_time = update_time
                    db.session.commit()
                    res = success_res()
                else:
                    res = fail_res(msg="批注数据不存在")


    except Exception as e:
        print(str(e))
        res = fail_res()

    return jsonify(res)


# delete
@blue_print.route('/delete_doc_mark_comment_by_id', methods=['POST'])
def delete_doc_mark_comment_by_id():
    try:
        id = request.json.get("id", 0)
        if isinstance(id, int):
            doc_mark_comment = DocMarkComment.query.filter_by(id=id, valid=1).first()
            if doc_mark_comment:
                doc_mark_comment.valid = 0
                res = success_res()
            else:
                res = fail_res(msg="批注数据不存在")
        else:
            res = fail_res(msg="参数 \"id\" 应是整数类型")


    except Exception as e:
        print(str(e))
        res = fail_res()

    return jsonify(res)

