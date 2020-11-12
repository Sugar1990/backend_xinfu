# -*- coding: UTF-8 -*-
from flask import jsonify, request
from . import api_doc_mark_comment as blue_print
from ..models import DocMarkComment
from .. import db
from .utils import success_res, fail_res
import time
import uuid

# 按id查询
@blue_print.route('/get_doc_mark_comment_by_id', methods=['GET'])
def get_doc_mark_comment_by_id():
    try:
        uuid = request.args.get("uuid", None)
        doc_mark_comment = DocMarkComment.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_comment:
            res = success_res({
                "uuid": doc_mark_comment.uuid,
                "doc_uuid": doc_mark_comment.doc_uuid,
                "name": doc_mark_comment.name,
                "position": doc_mark_comment.position,
                "comment": doc_mark_comment.comment,
                "create_by_uuid": doc_mark_comment.create_by_uuid,
                "create_time": doc_mark_comment.create_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_comment.create_time else None,
                "update_by_uuid": doc_mark_comment.update_by_uuid,
                "update_time": doc_mark_comment.update_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_comment.update_time else None
            })
        else:
            res = fail_res(msg="批注数据不存在")

    except Exception as e:
        print(str(e))
        res = fail_res({
            "uuid": '',
            "doc_uuid": '',
            "name": "",
            "position": "",
            "comment": "",
            "create_by_uuid": '',
            "create_time": None,
            "update_by_uuid": '',
            "update_time": None
        })

    return jsonify(res)


# 按doc_id查询
@blue_print.route('/get_doc_mark_comment_by_doc_id', methods=['GET'])
def get_doc_mark_comment_by_doc_id():
    try:
        doc_uuid = request.args.get("doc_uuid", None)
        doc_mark_comment_list = DocMarkComment.query.filter_by(doc_uuid=doc_uuid, valid=1).all()
        res = success_res(data=[{
            "uuid": i.uuid,
            "doc_uuid": i.doc_uuid,
            "name": i.name,
            "position": i.position,
            "comment": i.comment,
            "create_by_uuid": i.create_by_uuid,
            "create_time": i.create_time.strftime("%Y-%m-%d %H:%M:%S") if i.create_time else None,
            "update_by_uuid": i.update_by_uuid,
            "update_time": i.update_time.strftime("%Y-%m-%d %H:%M:%S") if i.update_time else None
        } for i in doc_mark_comment_list])

    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


# add
@blue_print.route('/add_doc_mark_comment', methods=['POST'])
def add_doc_mark_comment():
    try:
        doc_uuid = request.json.get("doc_uuid", None)
        name = request.json.get("name", "")
        position = request.json.get("position", "")
        comment = request.json.get("comment", "")
        create_by_uuid = request.json.get("create_by_uuid", None)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_by_uuid = request.json.get("update_by_uuid", None)
        update_time = request.json.get("update_time", None)

        doc_mark_comment_same = DocMarkComment.query.filter_by(doc_uuid=doc_uuid, name=name,
                                                               position=position, comment=comment, valid=1).first()
        if doc_mark_comment_same:
            res = fail_res(msg="相同批注已存在")
        else:
            doc_mark_comment = DocMarkComment(uuid=uuid.uuid1(), doc_uuid=doc_uuid, name=name, position=position,
                                              comment=comment, create_by_uuid=create_by_uuid, create_time=create_time,
                                              update_by_uuid=update_by_uuid, update_time=update_time, valid=1)
            db.session.add(doc_mark_comment)
            db.session.commit()
            res = success_res(data={"uuid": doc_mark_comment.uuid})

    except Exception as e:
        print(str(e))
        res = fail_res()

    return jsonify(res)


# modify
@blue_print.route('/modify_doc_mark_comment', methods=['PUT'])
def modify_doc_mark_comment():
    try:
        uuid = request.json.get("uuid", None)
        doc_uuid = request.json.get("doc_uuid", None)
        name = request.json.get("name", "")
        position = request.json.get("position", "")
        comment = request.json.get("comment", "")
        create_by_uuid = request.json.get("create_by_uuid", None)
        create_time = request.json.get("create_time", None)
        update_by_uuid = request.json.get("update_by_uuid", None)
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        doc_mark_comment_same = DocMarkComment.query.filter_by(doc_uuid=doc_uuid, name=name,
                                                               position=position, comment=comment, valid=1).first()
        if doc_mark_comment_same:
            res = fail_res(msg="相同批注已存在")
        else:
            doc_mark_comment = DocMarkComment.query.filter_by(uuid=uuid, valid=1).first()
            if doc_mark_comment:
                if doc_uuid:
                    doc_mark_comment.doc_uuid = doc_uuid
                if name:
                    doc_mark_comment.name = name
                if position:
                    doc_mark_comment.position = position
                if comment:
                    doc_mark_comment.comment = comment
                if create_by_uuid:
                    doc_mark_comment.create_by_uuid = create_by_uuid
                if create_time:
                    doc_mark_comment.create_time = create_time
                if update_by_uuid:
                    doc_mark_comment.update_by_uuid = update_by_uuid
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
        uuid = request.json.get("uuid", None)
        doc_mark_comment = DocMarkComment.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_comment:
            doc_mark_comment.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="批注数据不存在")

    except Exception as e:
        print(str(e))
        res = fail_res()

    return jsonify(res)
