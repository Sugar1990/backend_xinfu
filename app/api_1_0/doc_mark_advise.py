# -*- coding: UTF-8 -*-
from flask import jsonify, request
from . import api_doc_mark_advise as blue_print
from ..models import DocMarkAdvise, DocMarkTimeTag, DocMarkEntity, DocMarkPlace, DocMarkComment, Customer
from .. import db
from .utils import success_res, fail_res
import time
import uuid
from ..conf import ADMIN_ROLE_POWER

# 按id查询
@blue_print.route('/get_doc_mark_advise_by_id', methods=['GET'])
def get_doc_mark_advise_by_id():
    try:
        uuid = request.args.get("uuid", None)
        doc_mark_advise = DocMarkAdvise.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_advise:
            res = success_res({
                "uuid": doc_mark_advise.uuid,
                "doc_uuid": doc_mark_advise.doc_uuid,
                "mark_uuid": doc_mark_advise.mark_uuid,
                "type": doc_mark_advise.type,
                "content": doc_mark_advise.content,
                "create_by_uuid": doc_mark_advise.create_by_uuid,
                "create_time": doc_mark_advise.create_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_advise.create_time else None,
                "update_by_uuid": doc_mark_advise.update_by_uuid,
                "update_time": doc_mark_advise.update_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if doc_mark_advise.update_time else None
            })
        else:
            res = fail_res(msg="建议记录不存在")

    except Exception as e:
        print(str(e))
        res = fail_res({
            "uuid": '',
            "doc_uuid": '',
            "mark_uuid": '',
            "type": -1,
            "content": "",
            "create_by_uuid": '',
            "create_time": None,
            "update_by_uuid": '',
            "update_time": None
        })

    return jsonify(res)


# 按doc_id查询
@blue_print.route('/get_doc_mark_advise_by_doc_id', methods=['GET'])
def get_doc_mark_advise_by_doc_id():
    try:
        doc_uuid = request.args.get("doc_uuid", None)
        doc_mark_advise = DocMarkAdvise.query.filter_by(doc_uuid=doc_uuid, valid=1).all()
        res = success_res(data=[{
            "uuid": doc_mark_advise.uuid,
            "doc_uuid": doc_mark_advise.doc_uuid,
            "mark_uuid": doc_mark_advise.mark_uuid,
            "type": doc_mark_advise.type,
            "content": doc_mark_advise.content,
            "create_by_uuid": doc_mark_advise.create_by_uuid,
            "create_time": doc_mark_advise.create_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_advise.create_time else None,
            "update_by_uuid": doc_mark_advise.update_by_uuid,
            "update_time": doc_mark_advise.update_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_advise.update_time else None
        } for doc_mark_advise in doc_mark_advise])


    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


# 根据用户信息查询建议
@blue_print.route('/get_doc_mark_advise_by_create_by_id', methods=['GET'])
def get_doc_mark_advise_by_create_by_id():
    try:
        create_by_uuid = request.args.get("create_by_uuid", None)
        doc_uuid = request.args.get("doc_uuid", None)
        customer = Customer.query.filter_by(uuid=create_by_uuid, valid=1).first()
        if customer.get_power() != ADMIN_ROLE_POWER:
            doc_mark_advises = DocMarkAdvise.query.filter_by(create_by_uuid=create_by_uuid, doc_uuid=doc_uuid, valid=1).all()
        else:
            doc_mark_advises = DocMarkAdvise.query.filter_by(doc_uuid=doc_uuid, valid=1).all()
        res = success_res(data=[{
            "uuid": doc_mark_advise.uuid,
            "doc_uuid": doc_mark_advise.doc_uuid,
            "mark_uuid": doc_mark_advise.mark_uuid,
            "type": doc_mark_advise.type,
            "content": doc_mark_advise.content,
            "create_by_uuid": doc_mark_advise.create_by_uuid,
            "create_time": doc_mark_advise.create_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_advise.create_time else None,
            "update_by_uuid": doc_mark_advise.update_by_uuid,
            "update_time": doc_mark_advise.update_time.strftime(
                "%Y-%m-%d %H:%M:%S") if doc_mark_advise.update_time else None
        } for doc_mark_advise in doc_mark_advises])
    except Exception as e:
        print(str(e))
        res = fail_res(data=[])

    return jsonify(res)


# add
@blue_print.route('/add_doc_mark_advise', methods=['POST'])
def add_doc_mark_advise():
    try:
        doc_uuid = request.json.get("doc_uuid", None)
        mark_uuid = request.json.get("mark_uuid", None)
        type = request.json.get("type", 0)
        content = request.json.get("content", "")
        create_by_uuid = request.json.get("create_by_uuid", None)
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_by_uuid = request.json.get("update_by_uuid", None)
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        doc_mark_advise_same = DocMarkAdvise.query.filter_by(doc_uuid=doc_uuid, mark_uuid=mark_uuid, type=type,
                                                               content=content, valid=1).first()
        if doc_mark_advise_same:
            res = fail_res(msg="相同建议已存在")
        else:
            flag =True
            if type in [1, 2]:
                doc_mark_entity = DocMarkEntity.query.filter_by(uuid=mark_uuid, valid=1).first()
                if doc_mark_entity:
                    pass
                else:
                    flag = False
                    res = fail_res(msg="标注实体或概念不存在,建议插入失败！")
            elif type == 3:
                doc_mark_time_tag = DocMarkTimeTag.query.filter_by(uuid=mark_uuid, valid=1).first()
                if doc_mark_time_tag:

                    pass
                else:
                    flag = False
                    res = fail_res(msg="标注时间不存在,建议插入失败！")
            elif type == 4:
                doc_mark_place = DocMarkPlace.query.filter_by(uuid=mark_uuid, valid=1).first()
                if doc_mark_place:
                    pass
                else:
                    flag = False
                    res = fail_res(msg="标注地点不存在,建议插入失败！")
            else:
                doc_mark_comment = DocMarkComment.query.filter_by(uuid=mark_uuid, valid=1).first()
                if doc_mark_comment:
                    pass
                else:
                    flag = False
                    res = fail_res(msg="标注批注不存在,建议插入失败！")
            if flag:
                doc_mark_advise = DocMarkAdvise(uuid=uuid.uuid1(),
                                                doc_uuid=doc_uuid,
                                                mark_uuid=mark_uuid,
                                                type=type,
                                                content=content,
                                                create_by_uuid=create_by_uuid,
                                                create_time=create_time,
                                                update_by_uuid=update_by_uuid,
                                                update_time=update_time,
                                                valid=1)
                db.session.add(doc_mark_advise)
                db.session.commit()
                res = success_res(data={"uuid": doc_mark_advise.uuid})
            else:
                pass

    except Exception as e:
        print(str(e))
        res = fail_res()

    return jsonify(res)


# modify
@blue_print.route('/modify_doc_mark_advise', methods=['PUT'])
def modify_doc_mark_advise():
    try:
        uuid = request.json.get("uuid", None)
        doc_uuid = request.json.get("doc_uuid", None)
        mark_uuid = request.json.get("mark_uuid", None)
        type = request.json.get("type", 0)
        content = request.json.get("content", "")
        create_by_uuid = request.json.get("create_by_uuid", None)
        create_time = request.json.get("create_time", None)
        update_by_uuid = request.json.get("update_by_uuid", None)
        update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        doc_mark_advise_same = DocMarkAdvise.query.filter_by(doc_uuid=doc_uuid, mark_uuid=mark_uuid, type=type,
                                                               content=content, valid=1).first()
        if doc_mark_advise_same:
            res = fail_res(msg="相同建议已存在")
        else:
            doc_mark_advise = DocMarkAdvise.query.filter_by(uuid=uuid, valid=1).first()
            if doc_mark_advise:
                if doc_uuid:
                    doc_mark_advise.doc_uuid = doc_uuid
                if mark_uuid:
                    doc_mark_advise.mark_uuid = mark_uuid
                if type:
                    doc_mark_advise.type = type
                if content:
                    doc_mark_advise.content = content
                if create_by_uuid:
                    doc_mark_advise.create_by_uuid = create_by_uuid
                if create_time:
                    doc_mark_advise.create_time = create_time
                if update_by_uuid:
                    doc_mark_advise.update_by_uuid = update_by_uuid
                if update_time:
                    doc_mark_advise.update_time = update_time
                db.session.commit()
                res = success_res()
            else:
                res = fail_res(msg="建议记录不存在")

    except Exception as e:
        print(str(e))
        res = fail_res()

    return jsonify(res)


# delete
@blue_print.route('/delete_doc_mark_advise_by_id', methods=['POST'])
def delete_doc_mark_advise_by_id():
    try:
        uuid = request.json.get("uuid", None)
        doc_mark_advise = DocMarkAdvise.query.filter_by(uuid=uuid, valid=1).first()
        if doc_mark_advise:
            doc_mark_advise.valid = 0
            res = success_res()
        else:
            res = fail_res(msg="建议记录不存在")

    except Exception as e:
        print(str(e))
        res = fail_res()

    return jsonify(res)
