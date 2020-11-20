# -*- coding: UTF-8 -*-
import json
import os
import time
import urllib.request
import requests

from flask import jsonify, request
from sqlalchemy.dialects.postgresql import JSONB

from . import api_sync_offline as blue_print
from ..models import db
from .utils import success_res, fail_res
from sqlalchemy import create_engine, MetaData, Table, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from ..conf import PG_USER_NAME, PG_USER_PASSWORD, PG_DB_NAME, LOCAL_IP, LOCAL_PG_PORT, LOCAL_PORT


@blue_print.route('/show_local_database_information', methods=['GET'])
def show_target_database_information():
    data = {"target_pg_db_server_ip": LOCAL_IP, "target_pg_db_port": LOCAL_PG_PORT,
            "target_pg_user_name": PG_USER_NAME,
            "target_pg_user_password": PG_USER_PASSWORD, "target_pg_db_name": PG_DB_NAME}
    return data


@blue_print.route('/conn_pg', methods=['GET'])
def conn_pgs():
    conn = request.args
    PG_IP = conn.get('pg_db_server_ip')
    PG_PORT = conn.get('pg_db_port')
    PG_USER_NAME = conn.get('pg_user_name')
    PG_PWD = conn.get('pg_user_password')
    PG_DB_NAME = conn.get('pg_db_name')
    if not all([PG_IP, PG_PORT, PG_USER_NAME, PG_PWD, PG_DB_NAME]):
        return jsonify(fail_res())
    try:
        source_postgres = 'postgresql://%s:%s@%s:%s/%s' % (
            PG_USER_NAME, PG_PWD, PG_IP,
            PG_PORT,
            PG_DB_NAME)
        engine = create_engine(source_postgres)
        available_tables = engine.execute('SELECT datname FROM pg_database').fetchall()
        database_name = []
        for dataname in available_tables:
            database_name.append(dataname[0])

        def is_template(str):
            return not str.startswith('template')

        database_names = list(filter(is_template, database_name))
        res = success_res(msg="连接成功")
    except:
        res = fail_res(msg="连接失败")
    return jsonify(res)


@blue_print.route('/sync_data', methods=['POST'])
def sync_source():
    try:
        SOURCE_PG_USER_NAME = request.json.get('source_pg_user_name')
        SOURCE_PG_USER_PASSWORD = request.json.get('source_pg_user_password')
        SOURCE_PG_DB_SERVER_IP = request.json.get('source_pg_db_server_ip')
        SOURCE_PG_DB_PORT = request.json.get('source_pg_db_port')
        SOURCE_PG_DB_NAME = request.json.get('source_pg_db_name')
        TARGET_PG_DB_SERVER_IP = request.json.get('target_pg_db_server_ip')
        TARGET_PG_DB_PORT = request.json.get('target_pg_db_port')
        TARGET_PG_USER_NAME = request.json.get('target_pg_user_name')
        TARGET_PG_USER_PASSWORD = request.json.get('target_pg_user_password')
        TARGET_PG_DB_NAME = request.json.get('target_pg_db_name')

        # 建立动态数据库的链接
        source_postgres = 'postgresql://%s:%s@%s:%s/%s' % (
            SOURCE_PG_USER_NAME, SOURCE_PG_USER_PASSWORD, SOURCE_PG_DB_SERVER_IP,
            SOURCE_PG_DB_PORT,
            SOURCE_PG_DB_NAME)
        engine = create_engine(source_postgres)
        # 定义模型类继承父类及数据连接会话
        DBsession = sessionmaker(bind=engine)  # 类似于游标
        dbsession = scoped_session(DBsession)
        Base = declarative_base()  # 定义一个给其他类继承的父类

        # 建立动态数据库的链接
        target_postgres = 'postgresql://%s:%s@%s:%s/%s' % (
            TARGET_PG_USER_NAME, TARGET_PG_USER_PASSWORD, TARGET_PG_DB_SERVER_IP,
            TARGET_PG_DB_PORT,
            TARGET_PG_DB_NAME)
        target_engine = create_engine(target_postgres)
        # 定义模型类继承父类及数据连接会话
        target_DBsession = sessionmaker(bind=target_engine)  # 类似于游标
        target_dbsession = scoped_session(target_DBsession)
        Target_Base = declarative_base()  # 定义一个给其他类继承的父类

        # md = MetaData(bind=engine)  # 元数据: 主要是指数据库表结构、关联等信息

        class SyncRecords(Target_Base):
            __tablename__ = 'sync_records'
            id = db.Column(db.Integer, primary_key=True)
            system_name = db.Column(db.String)
            sync_time = db.Column(db.TIMESTAMP)

            def __repr__(self):
                return '<SyncRecords %r>' % self.system_name

        # 获取上次同步时间
        sync_record = target_dbsession.query(SyncRecords).filter_by(system_name=SOURCE_PG_DB_SERVER_IP).first()
        sync_time = sync_record.sync_time

        # 更新同步时间
        sync_record.sync_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        target_dbsession.commit()

        # 记录同步结果
        res_records = []

        # <editor-fold desc="sync_offline of Customer">
        # 定义模型类
        try:
            class Customer(Target_Base):  # 自动加载表结构
                __tablename__ = 'customer'
                uuid = db.Column(db.String, primary_key=True)
                username = db.Column(db.Text)
                pwd = db.Column(db.Text)
                permission_id = db.Column(db.Integer)
                valid = db.Column(db.Integer)
                token = db.Column(db.String)
                _source = db.Column(db.String)
                power_score = db.Column(db.Float)
                troop_number = db.Column(db.String)
                create_time = db.Column(db.DateTime)
                update_time = db.Column(db.DateTime)

                def __repr__(self):
                    return '<Customer %r>' % self.username

            class OfflineCustomer(Base):  # 自动加载表结构
                # __table__ = Table('customer', md, autoload=True)
                __tablename__ = 'customer'
                uuid = db.Column(db.String, primary_key=True)
                username = db.Column(db.Text)
                pwd = db.Column(db.Text)
                permission_id = db.Column(db.Integer)
                valid = db.Column(db.Integer)
                token = db.Column(db.String)
                _source = db.Column(db.String)
                power_score = db.Column(db.Float)
                troop_number = db.Column(db.String)
                create_time = db.Column(db.DateTime)
                update_time = db.Column(db.DateTime)

                def __repr__(self):
                    return '<Customer %r>' % self.username

            # offline所有uuid/troop_number，唯一性（去重）判断
            uuids_and_troop_in_offline = dbsession.query(OfflineCustomer).with_entities(OfflineCustomer.uuid,
                                                                                        OfflineCustomer.troop_number).filter(
                OfflineCustomer.valid == 1, or_(OfflineCustomer.create_time > sync_time, OfflineCustomer.update_time > sync_time)).all()
            troop_numbers_in_offline = [i[1] for i in uuids_and_troop_in_offline]

            # online所有uuid/troop_number，唯一性（去重）判断
            uuids_and_troop_in_online = target_dbsession.query(Customer).with_entities(Customer.uuid, Customer.troop_number).filter(
                Customer.valid==1).all()
            troop_numbers_in_online = [i[1] for i in uuids_and_troop_in_online]

            # 记录uuid变化----customer_uuid_dict_trans
            online_dict_trans = {}
            customer_uuid_dict_trans = {}

            for i in uuids_and_troop_in_online:
                if i[1] not in online_dict_trans.keys():
                    online_dict_trans[i[1]] = i[0]  # [{"troop_number": "uuid"}]

            # 遍历offline所有数据，不做时间筛选，构造dict
            uuids_and_troop_in_offline_for_dict = dbsession.query(OfflineCustomer).with_entities(OfflineCustomer.uuid,
                                                                                                 OfflineCustomer.troop_number).filter_by(
                valid=1).all()

            for offline_customer in uuids_and_troop_in_offline_for_dict:
                # offtroop存在, {"offuuid": "onuuid"}, offtroop不存在, {"offuuid": "offuuid"}
                customer_uuid_dict_trans[offline_customer[0]] = online_dict_trans[
                    offline_customer[1]] if online_dict_trans.get(offline_customer[1], "") else offline_customer[0]

            # offline-online：计算是否有要插入的数据
            offline_troop_numbers_to_insert = list(set(troop_numbers_in_offline).difference(set(troop_numbers_in_online)))
            # offline-online：计算是否有要更新的数据
            offline_troop_numbers_to_update = list(set(troop_numbers_in_offline).intersection(set(troop_numbers_in_online)))

            # 如果有要插入的数据
            if offline_troop_numbers_to_insert:
                offline_customers = dbsession.query(OfflineCustomer).filter(
                    OfflineCustomer.troop_number.in_(offline_troop_numbers_to_insert)).all()
                sync_customers = [Customer(uuid=i.uuid,
                                           username=i.username,
                                           pwd=i.pwd,
                                           permission_id=i.permission_id,
                                           valid=i.valid,
                                           token=i.token,
                                           _source=i._source,
                                           power_score=i.power_score,
                                           troop_number=i.troop_number,
                                           create_time=i.create_time,
                                           update_time=i.update_time) for i in offline_customers]
                # target_dbsession.add_all(sync_customers)
                # target_dbsession.commit()
                target_dbsession.add_all(sync_customers)
                target_dbsession.commit()

                # 如果有要更新的数据  即_source相同，off_uuid=on_uuid
                if offline_troop_numbers_to_update:
                    offline_customers = dbsession.query(OfflineCustomer).filter(
                        OfflineCustomer.troop_number.in_(offline_troop_numbers_to_update)).all()
                    for offline_customer in offline_customers:
                        online_customer = target_dbsession.query(Customer).filter_by(uuid=offline_customer.uuid,
                                                                   _source=offline_customer._source, valid=1).first()
                        if online_customer:
                            online_customer.username = offline_customer.username
                            online_customer.pwd = offline_customer.pwd
                            online_customer.power_score = offline_customer.power_score
                            online_customer.update_time = offline_customer.update_time
                target_dbsession.commit()
            # print("customer_uuid_dict_trans:", customer_uuid_dict_trans)
            res_records.append(f"用户表同步完成！新增{len(offline_troop_numbers_to_insert)}条数据，更新{len(offline_troop_numbers_to_update)}条数据。")
        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("用户表同步失败！")

        # </editor-fold>

        # <editor-fold desc="sync_offline of EntityCategory">
        # # 定义模型类
        try:
            class EntityCategory(Target_Base):  # 自动加载表结构
                # __table__ = Table('customer', md, autoload=True)
                __tablename__ = 'entity_category'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                valid = db.Column(db.Integer)  # 取值0或1，0表示已删除，1表示正常
                type = db.Column(db.Integer)  # 1：实体（地名、国家、人物...）；2：概念（条约公约、战略、战法...）
                _source = db.Column(db.String)
                create_time = db.Column(db.DateTime)
                update_time = db.Column(db.DateTime)

                def __repr__(self):
                    return '<EntityCategory %r>' % self.uuid

            class OfflineEntityCategory(Base):  # 自动加载表结构
                # __table__ = Table('customer', md, autoload=True)
                __tablename__ = 'entity_category'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                valid = db.Column(db.Integer)  # 取值0或1，0表示已删除，1表示正常
                type = db.Column(db.Integer)  # 1：实体（地名、国家、人物...）；2：概念（条约公约、战略、战法...）
                _source = db.Column(db.String)
                create_time = db.Column(db.DateTime)
                update_time = db.Column(db.DateTime)

                def __repr__(self):
                    return '<EntityCategory %r>' % self.uuid

            # offline所有name，唯一性（去重）判断
            uuids_and_names_in_offline_ec = dbsession.query(OfflineEntityCategory).with_entities(OfflineEntityCategory.uuid,
                                                                                                 OfflineEntityCategory.name).filter(
                OfflineEntityCategory.valid == 1,
                or_(OfflineEntityCategory.create_time > sync_time, OfflineEntityCategory.update_time > sync_time)).all()
            uuids_in_offline = [i[0] for i in uuids_and_names_in_offline_ec]
            names_in_offline = [i[1] for i in uuids_and_names_in_offline_ec]

            # online所有name，唯一性（去重）判断
            uuids_and_names_in_online_ec = target_dbsession.query(EntityCategory).with_entities(EntityCategory.uuid,
                                                                              EntityCategory.name).filter(
                EntityCategory.valid == 1).all()
            uuids_in_online = [i[0] for i in uuids_and_names_in_online_ec]
            names_in_online = [i[1] for i in uuids_and_names_in_online_ec]

            # 记录uuid变化----ec_uuid_dict_trans
            online_dict_trans = {}
            ec_uuid_dict_trans = {}

            for i in uuids_and_names_in_online_ec:
                if i[1] not in online_dict_trans.keys():
                    online_dict_trans[i[1]] = i[0]  # {"onname": "onuuid"}

            # 遍历offline所有数据，不做时间筛选，构造dict
            uuids_and_names_in_offline_ec_for_dict = dbsession.query(OfflineEntityCategory).with_entities(OfflineEntityCategory.uuid,
                                                                                                 OfflineEntityCategory.name).filter(
                OfflineEntityCategory.valid == 1).all()

            for offline_ec in uuids_and_names_in_offline_ec_for_dict:
                # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
                ec_uuid_dict_trans[offline_ec[0]] = online_dict_trans[
                    offline_ec[1]] if online_dict_trans.get(offline_ec[1], "") else offline_ec[0]

            # offline-online：计算是否有要插入的数据
            offline_names_to_insert = list(set(names_in_offline).difference(set(names_in_online)))

            # offline-online：计算是否有要更新的数据
            offline_uuids_to_update = list(set(uuids_in_offline).intersection(set(uuids_in_online)))

            # 如果有要插入的数据
            if offline_names_to_insert:
                offline_entity_cateogories = dbsession.query(OfflineEntityCategory).filter(
                    OfflineEntityCategory.name.in_(offline_names_to_insert)).all()
                sync_entity_categories = [EntityCategory(uuid=i.uuid,
                                                         name=i.name,
                                                         valid=i.valid,
                                                         type=i.type,
                                                         _source=i._source,
                                                         create_time=i.create_time,
                                                         update_time=i.update_time) for i in offline_entity_cateogories]
                target_dbsession.add_all(sync_entity_categories)
                target_dbsession.commit()

            # 如果有要更新的数据
            if offline_uuids_to_update:
                offline_entity_cateogories = dbsession.query(OfflineEntityCategory).filter(
                    OfflineEntityCategory.uuid.in_(offline_uuids_to_update)).all()
                for offline_ec in offline_entity_cateogories:
                    online_ec = target_dbsession.query(EntityCategory).filter_by(uuid=offline_ec.uuid,
                                                                                 _source=offline_ec._source, valid=1).first()
                    if online_ec:
                        online_ec.name = offline_ec.name
                        online_ec.type = offline_ec.type
                        online_ec.update_time = offline_ec.update_time
                target_dbsession.commit()
            # print("ec_uuid_dict_trans:", ec_uuid_dict_trans)
            res_records.append(
                f"实体类型表同步完成！新增{len(offline_names_to_insert)}条数据，更新{len(offline_uuids_to_update)}条数据。")
        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("实体类型表同步失败！")

        # </editor-fold>

        # <editor-fold desc="sync_offline of RelationCategory">
        # 定义模型类
        try:
            class RelationCategory(Target_Base):  # 自动加载表结构
                __tablename__ = 'relation_category'
                uuid = db.Column(db.String, primary_key=True)
                source_entity_category_uuids = db.Column(db.JSON)  # NOTE: not null
                target_entity_category_uuids = db.Column(db.JSON)
                relation_name = db.Column(db.Text)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                create_time = db.Column(db.DateTime)
                update_time = db.Column(db.DateTime)

                def __repr__(self):
                    return '<RelationCategory %r>' % self.uuid

            class OfflineRelationCategory(Base):  # 自动加载表结构
                __tablename__ = 'relation_category'
                uuid = db.Column(db.String, primary_key=True)
                source_entity_category_uuids = db.Column(db.JSON)  # NOTE: not null
                target_entity_category_uuids = db.Column(db.JSON)
                relation_name = db.Column(db.Text)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                create_time = db.Column(db.DateTime)
                update_time = db.Column(db.DateTime)

                def __repr__(self):
                    return '<RelationCategory %r>' % self.uuid

            # 查找上次同步时间后新增和修改的数据
            relation_categories_in_offline = dbsession.query(OfflineRelationCategory).filter(
                OfflineRelationCategory.valid == 1,
                or_(OfflineRelationCategory.create_time > sync_time, OfflineRelationCategory.update_time > sync_time)).all()
            # 更新ec_uuid_dict_trans
            new_ec_uuid_dict_trans = {}
            for key, value in ec_uuid_dict_trans.items():
                print(key, value)
                new_ec_uuid_dict_trans[str(key)] = str(ec_uuid_dict_trans.get(key))
            # print(new_ec_uuid_dict_trans)

            rc_uuid_dict_trans = {}
            insert_num = 0
            update_num = 0
            # 根据name、source/targer_entity_category_ids判重，选择新增还是更新相同来源的数据
            for offline_rc in relation_categories_in_offline:
                # 更新source/target_entity_category_uuids
                for index, value in enumerate(offline_rc.source_entity_category_uuids):
                    offline_rc.source_entity_category_uuids[index] = new_ec_uuid_dict_trans.get(value)
                for index, value in enumerate(offline_rc.target_entity_category_uuids):
                    offline_rc.target_entity_category_uuids[index] = new_ec_uuid_dict_trans.get(value)

                input_source_ids_set = set(offline_rc.source_entity_category_uuids)
                input_target_ids_set = set(offline_rc.target_entity_category_uuids)

                # 查找相同关系名称的数据
                relation_same = target_dbsession.query(RelationCategory).filter_by(relation_name=offline_rc.relation_name, valid=1).all()
                if relation_same:
                    for item in relation_same:
                        source_ids_db = set(item.source_entity_category_uuids)
                        target_ids_db = set(item.target_entity_category_uuids)

                        # 已存在--offline新数据数据与库里已有数据相等或是库里数据的子集
                        if input_source_ids_set.issubset(
                                source_ids_db) and input_target_ids_set.issubset(target_ids_db):
                            # 来源相同，则更新数据
                            if item._source == offline_rc._source:
                                item.source_entity_category_uuids = offline_rc.source_entity_category_uuids
                                item.target_entity_category_uuids = offline_rc.target_entity_category_uuids
                                rc_uuid_dict_trans[offline_rc.uuid] = item.uuid
                                update_num += 1
                                break
                            #来源不同，保留主库
                            else:
                                rc_uuid_dict_trans[offline_rc.uuid] = item.uuid
                                break

                        # update--源ids相等 and 目标ids不相等  update目标ids  取并集
                        elif (input_source_ids_set == source_ids_db) and input_target_ids_set != target_ids_db:
                            target_ids_result = list(input_target_ids_set.union(target_ids_db))
                            # 来源相同，则更新数据
                            if item._source == offline_rc._source:
                                item.target_entity_category_uuids = target_ids_result
                                rc_uuid_dict_trans[offline_rc.uuid] = item.uuid
                                update_num += 1
                                break
                            # 来源不同，保留主库
                            else:
                                rc_uuid_dict_trans[offline_rc.uuid] = item.uuid
                                break

                        # update--目标ids相等 and 源ids不相等  update源ids  取并集
                        elif (input_source_ids_set != source_ids_db) and input_target_ids_set == target_ids_db:
                            source_ids_result = list(input_source_ids_set.union(source_ids_db))
                            # 来源相同，则更新数据
                            if item._source == offline_rc._source:
                                item.source_entity_category_uuids = source_ids_result
                                rc_uuid_dict_trans[offline_rc.uuid] = item.uuid
                                update_num += 1
                                break
                            # 来源不同，保留主库
                            else:
                                rc_uuid_dict_trans[offline_rc.uuid] = item.uuid
                                break

                        # update--库里已有数据是输入数据的子集
                        elif source_ids_db.issubset(
                                input_source_ids_set) and target_ids_db.issubset(input_target_ids_set):
                            # 来源相同，则更新数据
                            if item._source == offline_rc._source:
                                item.source_entity_category_uuids = offline_rc.source_entity_category_uuids
                                item.target_entity_category_uuids = offline_rc.target_entity_category_uuids
                                rc_uuid_dict_trans[offline_rc.uuid] = item.uuid
                                update_num += 1
                                break
                            # 来源不同，保留主库
                            else:
                                rc_uuid_dict_trans[offline_rc.uuid] = item.uuid
                                break
                        # insert--相同关系名，但源、目标实体类型不同
                        else:
                            rc = RelationCategory(uuid=offline_rc.uuid,
                                                  source_entity_category_uuids=offline_rc.source_entity_category_uuids,
                                                  target_entity_category_uuids=offline_rc.target_entity_category_uuids,
                                                  relation_name=offline_rc.relation_name,
                                                  _source=offline_rc._source,
                                                  valid=1)
                            target_dbsession.add(rc)
                            target_dbsession.commit()
                            rc_uuid_dict_trans[offline_rc.uuid] = offline_rc.uuid
                            insert_num += 1
                            break
                else:
                    rc = RelationCategory(uuid=offline_rc.uuid, source_entity_category_uuids=offline_rc.source_entity_category_uuids,
                                          target_entity_category_uuids=offline_rc.target_entity_category_uuids, relation_name=offline_rc.relation_name,
                                          valid=1)
                    target_dbsession.add(rc)
                    target_dbsession.commit()
                    rc_uuid_dict_trans[offline_rc.uuid] = offline_rc.uuid
                    insert_num += 1

            res_records.append(
                f"关系类型表同步完成！新增{insert_num}条数据，更新{update_num}条数据。")
        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("关系类型表同步失败！")

        # </editor-fold>

        # <editor-fold desc="sync_offline of Entity">
        # 定义模型类
        try:
            class Entity(Target_Base):  # 自动加载表结构
                __tablename__ = 'entity'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                synonyms = db.Column(JSONB)
                props = db.Column(JSONB)
                category_uuid = db.Column(db.String)
                summary = db.Column(db.Text)
                valid = db.Column(db.Integer)
                longitude = db.Column(db.Float)
                latitude = db.Column(db.Float)
                _source = db.Column(db.String)
                create_time = db.Column(db.DateTime)
                update_time = db.Column(db.DateTime)

                def __repr__(self):
                    return '<Entity %r>' % self.uuid

            class OfflineEntity(Base):  # 自动加载表结构
                __tablename__ = 'entity'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                synonyms = db.Column(JSONB)
                props = db.Column(JSONB)
                category_uuid = db.Column(db.String)
                summary = db.Column(db.Text)
                valid = db.Column(db.Integer)
                longitude = db.Column(db.Float)
                latitude = db.Column(db.Float)
                _source = db.Column(db.String)
                create_time = db.Column(db.DateTime)
                update_time = db.Column(db.DateTime)

                def __repr__(self):
                    return '<Entity %r>' % self.uuid

            # 更新category_uuids
            entities_in_offline = dbsession.query(OfflineEntity).filter(OfflineEntity.valid == 1,
                                                                        or_(OfflineEntity.create_time > sync_time,
                                                                            OfflineEntity.update_time> sync_time)).all()
            for i in entities_in_offline:
                i.category_uuid = ec_uuid_dict_trans.get(i.category_uuid)
                print(i.category_uuid)

            # offline所有name+category_uuid，唯一性（去重）判断
            names_and_cate_uuids_in_offline = dbsession.query(OfflineEntity).with_entities(OfflineEntity.name,
                                                                                           OfflineEntity.category_uuid,
                                                                                           OfflineEntity.uuid).filter(
                OfflineEntity.valid == 1,
                or_(OfflineEntity.create_time > sync_time, OfflineEntity.update_time > sync_time)).all()
            diff_sign_in_offline = [i[0] + str(i[1]) for i in names_and_cate_uuids_in_offline]

            # online所有name+category_uuid，唯一性（去重）判断
            names_and_cate_uuids_in_online = target_dbsession.query(Entity).with_entities(Entity.name, Entity.category_uuid,
                                                                        Entity.uuid).filter(Entity.valid == 1, Entity.category_uuid!=None).all()
            diff_sign_in_online = [i[0] + str(i[1]) for i in names_and_cate_uuids_in_online]

            # 记录uuid变化----entity_uuid_dict_trans
            online_dict_trans_entity = {}
            entity_uuid_dict_trans = {}

            for i in names_and_cate_uuids_in_online:
                if i[0] + str(i[1]) not in online_dict_trans_entity.keys():
                    online_dict_trans_entity[i[0] + str(i[1])] = i[2]  # {"onname+oncate_uuid": "onuuid"}
            # print("entity:", online_dict_trans)
            for offline_entity in names_and_cate_uuids_in_offline:
                # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
                entity_uuid_dict_trans[offline_entity[2]] = online_dict_trans_entity[
                    offline_entity[0] + str(offline_entity[1])] if online_dict_trans_entity.get(offline_entity[0] + str(offline_entity[1]),
                                                                                    "") else offline_entity[2]

            # offline-online：计算是否有要插入的数据
            offline_diff = list(set(diff_sign_in_offline).difference(set(diff_sign_in_online)))
            offline_name_diff = [i[0:-36] for i in offline_diff]
            print(offline_name_diff)
            offline_cate_uuid_diff = [i[-36:] for i in offline_diff]
            print(offline_cate_uuid_diff)

            # offline-online: 取交集，需要更新synonyms和props-----应该用uuid取交集
            offline_inter = list(set(diff_sign_in_offline).intersection(set(diff_sign_in_online)))
            offline_name_inter = [i[0:-36] for i in offline_inter]
            offline_cate_uuid_inter = [i[-36:] for i in offline_inter]

            # 如果有要更新的数据----更新synonyms和props
            if offline_inter:
                online_entities_update = target_dbsession.query(Entity).filter(Entity.name.in_(offline_name_inter),
                                                               Entity.category_uuid.in_(offline_cate_uuid_inter)).all()
                for online_entity in online_entities_update:
                    offline_entity = dbsession.query(OfflineEntity).filter_by(name=online_entity.name,
                                                                              category_uuid=online_entity.category_uuid).first()
                    online_entity.synonyms = list(set(online_entity.synonyms.append(offline_entity.synonyms)))
                    offline_entity.props.update(online_entity.props)  # 相同属性保留online的值
                    online_entity.props = offline_entity.props
                    online_entity.summary = online_entity.summary  # 不更新summary
                    # online_entity.summary = online_entity.summary + ' ' + offline_entity.summary + "——来自" + offline_entity._source

                target_dbsession.commit()

            # 如果有要插入的数据
            if offline_diff:
                offline_entities = dbsession.query(OfflineEntity).filter(
                    OfflineEntity.name.in_(offline_name_diff),
                    OfflineEntity.category_uuid.in_(offline_cate_uuid_diff)).all()
                sync_entities = [Entity(uuid=i.uuid, name=i.name, synonyms=i.synonyms, props=i.props,
                                        category_uuid=i.category_uuid, summary=i.summary, valid=i.valid,
                                        longitude=i.longitude, latitude=i.latitude, _source=i._source,
                                        create_time=i.create_time,
                                        update_time=i.update_time) for i in offline_entities]
                target_dbsession.add_all(sync_entities)
                target_dbsession.commit()

            res_records.append(
                f"实体表同步完成！新增{len(offline_diff)}条数据，更新{len(offline_inter)}条数据。")
        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("实体表同步失败！")

        # </editor-fold>

        # <editor-fold desc="sync_offline of EventClass">
        # 定义模型类
        try:
            class EventClass(Target_Base):  # 自动加载表结构
                # __table__ = Table('customer', md, autoload=True)
                __tablename__ = 'event_class'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_time = db.Column(db.TIMESTAMP)

                def __repr__(self):
                    return '<EventClass %r>' % self.uuid

            class OfflineEventClass(Base):  # 自动加载表结构
                # __table__ = Table('customer', md, autoload=True)
                __tablename__ = 'event_class'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_time = db.Column(db.TIMESTAMP)

                def __repr__(self):
                    return '<EventClass %r>' % self.uuid

            # offline所有name，唯一性（去重）判断
            uuids_and_names_in_offline_evcl = dbsession.query(OfflineEventClass).with_entities(OfflineEventClass.uuid,
                                                                                               OfflineEventClass.name).filter(
                OfflineEventClass.valid == 1,
                or_(OfflineEventClass.create_time > sync_time, OfflineEventClass.update_time > sync_time)).all()
            uuids_in_offline = [i[0] for i in uuids_and_names_in_offline_evcl]
            names_in_offline = [i[1] for i in uuids_and_names_in_offline_evcl]

            # online所有name，唯一性（去重）判断
            uuids_and_names_in_online_evcl = target_dbsession.query(EventClass).with_entities(EventClass.uuid, EventClass.name).filter(
                EventClass.valid == 1).all()
            uuids_in_online = [i[0] for i in uuids_and_names_in_online_evcl]
            names_in_online = [i[1] for i in uuids_and_names_in_online_evcl]

            # 记录uuid变化----event_class_uuid_dict_trans
            online_dict_trans = {}
            event_class_uuid_dict_trans = {}

            for i in uuids_and_names_in_online_evcl:
                if i[1] not in online_dict_trans.keys():
                    online_dict_trans[i[1]] = i[0]  # {"onname": "onuuid"}

            # offline所有name，构造dict
            uuids_and_names_in_offline_evcl_for_dict = dbsession.query(OfflineEventClass).with_entities(
                OfflineEventClass.uuid,
                OfflineEventClass.name).filter(OfflineEventClass.valid == 1).all()

            for offline_ec in uuids_and_names_in_offline_evcl_for_dict:
                # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
                event_class_uuid_dict_trans[offline_ec[0]] = online_dict_trans[
                    offline_ec[1]] if online_dict_trans.get(offline_ec[1], "") else offline_ec[0]

            # offline-online：计算是否有要插入的数据
            offline_names_to_insert = list(set(names_in_offline).difference(set(names_in_online)))
            # offline-online：计算是否有要更新的数据,以uuid为判重标准
            offline_uuids_to_update = list(set(uuids_in_offline).intersection(set(uuids_in_online)))

            # 如果有要插入的数据
            if offline_names_to_insert:
                offline_event_classes = dbsession.query(OfflineEventClass).filter(
                    OfflineEventClass.name.in_(offline_names_to_insert)).all()
                sync_event_classes = [EventClass(uuid=i.uuid,
                                                 name=i.name,
                                                 valid=i.valid,
                                                 _source=i._source,
                                                 create_time=i.create_time,
                                                 update_time=i.update_time) for i in offline_event_classes]
                target_dbsession.add_all(sync_event_classes)
                target_dbsession.commit()

            # 如果有要更新的数据,更新的数据是前几次同步时由该离线系统插入的数据，uuid未改变
            if offline_uuids_to_update:
                offline_event_classes = dbsession.query(OfflineEventClass).filter(
                    OfflineEventClass.uuid.in_(offline_uuids_to_update)).all()
                for offline_evcl in offline_event_classes:
                    online_evcl = target_dbsession.query(EventClass).filter_by(uuid=offline_evcl.uuid, _source=offline_evcl._source, valid=1).first()
                    online_evcl.name = offline_evcl.name
                    online_evcl.update_time = offline_evcl.update_time
                target_dbsession.commit()

            res_records.append(
                f"事件类别表同步完成！新增{len(offline_names_to_insert)}条数据，更新{len(offline_uuids_to_update)}条数据。")
        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("事件类别表同步失败！")

        # </editor-fold>

        # <editor-fold desc="sync_offline of EventCategory">
        # 定义模型类
        try:
            class EventCategory(Target_Base):  # 自动加载表结构
                __tablename__ = 'event_category'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                event_class_uuid = db.Column(db.String)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_time = db.Column(db.TIMESTAMP)

                def __repr__(self):
                    return '<EventCategory %r>' % self.uuid

            class OfflineEventCategory(Base):  # 自动加载表结构
                __tablename__ = 'event_category'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                event_class_uuid = db.Column(db.String)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_time = db.Column(db.TIMESTAMP)

                def __repr__(self):
                    return '<EventCategory %r>' % self.uuid

            # 更新event_class_uuid
            event_categories_in_offline = dbsession.query(OfflineEventCategory).filter(OfflineEventCategory.valid == 1, or_(
                OfflineEventCategory.create_time > sync_time, OfflineEventCategory.update_time > sync_time)).all()
            for i in event_categories_in_offline:
                i.event_class_uuid = event_class_uuid_dict_trans.get(i.event_class_uuid)

            # offline所有name, 唯一性（去重）判断
            names_and_class_uuids_in_offline = dbsession.query(OfflineEventCategory).with_entities(
                OfflineEventCategory.name, OfflineEventCategory.uuid).filter(OfflineEventCategory.valid == 1, or_(
                OfflineEventCategory.create_time > sync_time, OfflineEventCategory.update_time > sync_time)).all()
            diff_sign_in_offline = [i[0] for i in names_and_class_uuids_in_offline]
            uuids_in_offline = [i[1] for i in names_and_class_uuids_in_offline]

            # online所有name, 唯一性（去重）判断
            names_and_class_uuids_in_online = target_dbsession.query(EventCategory).with_entities(EventCategory.name,
                                                                                EventCategory.uuid).filter(
                EventCategory.valid == 1).all()
            diff_sign_in_online = [i[0] for i in names_and_class_uuids_in_online]
            uuids_in_online = [i[1] for i in names_and_class_uuids_in_online]

            # 记录uuid变化----event_cate_uuid_dict_trans
            online_dict_trans = {}
            event_cate_uuid_dict_trans = {}

            for i in names_and_class_uuids_in_online:
                if i[0] not in online_dict_trans.keys():
                    online_dict_trans[i[0]] = i[1]  # {"online_name": "onuuid"}

            # offline所有name, 构造dict
            names_and_class_uuids_in_offline_for_dict = dbsession.query(OfflineEventCategory).with_entities(
                OfflineEventCategory.name, OfflineEventCategory.uuid).filter(OfflineEventCategory.valid == 1).all()

            for offline_event_category in names_and_class_uuids_in_offline_for_dict:
                # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
                event_cate_uuid_dict_trans[offline_event_category[1]] = online_dict_trans[
                    offline_event_category[0]] if online_dict_trans.get(
                    offline_event_category[0], "") else offline_event_category[1]

            # offline-online：计算是否有要插入的数据
            offline_diff_to_insert = list(set(diff_sign_in_offline).difference(set(diff_sign_in_online)))
            # offline-online：计算是否有要更新的数据
            offline_uuids_to_update = list(set(uuids_in_offline).intersection(set(uuids_in_online)))

            # 如果有要插入的数据
            if offline_diff_to_insert:
                offline_event_categories = dbsession.query(OfflineEventCategory).filter(
                    OfflineEventCategory.name.in_(offline_diff_to_insert)).all()
                sync_event_categories = [EventCategory(uuid=i.uuid, name=i.name,
                                                       event_class_uuid=i.event_class_uuid, valid=i.valid,
                                                       _source=i._source, create_time=i.create_time,
                                                       update_time=i.update_time) for i in offline_event_categories]
                target_dbsession.add_all(sync_event_categories)
                target_dbsession.commit()

            # 如果有要更新的数据
            if offline_uuids_to_update:
                offline_event_categories = dbsession.query(OfflineEventCategory).filter(
                    OfflineEventCategory.uuid.in_(offline_uuids_to_update)).all()
                for offline_event_cate in offline_event_categories:
                    online_event_cate = target_dbsession.query(EventCategory).filter_by(uuid=offline_event_cate.uuid,
                                                                      _source=offline_event_cate._source, valid=1).first()
                    if online_event_cate:
                        online_event_cate.name = offline_event_cate.name
                        online_event_cate.event_class_uuid = offline_event_cate.event_class_uuid
                        online_event_cate.update_time = offline_event_cate.update_time
                target_dbsession.commit()
            res_records.append(
                f"事件类型表同步完成！新增{len(offline_diff_to_insert)}条数据，更新{len(offline_uuids_to_update)}条数据。")
        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("事件类型表同步失败！")
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkComment">
        # 定义模型类
        try:
            class DocMarkComment(Target_Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_comment'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                name = db.Column(db.Text)
                position = db.Column(db.String)
                comment = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                appear_index_in_text = db.Column(db.String)
                locate_position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkComment %r>' % self.uuid

            class OfflineDocMarkComment(Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_comment'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                name = db.Column(db.Text)
                position = db.Column(db.String)
                comment = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                appear_index_in_text = db.Column(db.String)
                locate_position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkComment %r>' % self.uuid


            doc_mark_comment_in_offline = dbsession.query(OfflineDocMarkComment).filter(OfflineDocMarkComment.valid == 1,
                                                                                        or_(
                                                                                            OfflineDocMarkComment.create_time > sync_time,
                                                                                            OfflineDocMarkComment.update_time > sync_time)).all()
            doc_mark_comment_uuids_in_offline = [i.uuid for i in doc_mark_comment_in_offline]
            doc_mark_comment_uuids_in_online = target_dbsession.query(DocMarkComment).with_entities(DocMarkComment.uuid).filter_by(valid=1).all()

            # 更新create_by_uuid、update_by_uuid
            for i in doc_mark_comment_in_offline:
                i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
                i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)

            # offline-online：计算是否有要插入的数据
            offline_dmm_to_insert = list(set(doc_mark_comment_uuids_in_offline).difference(set(doc_mark_comment_uuids_in_online)))
            # offline-online：计算是否有要更新的数据
            offline_dmm_to_update = list(set(doc_mark_comment_uuids_in_offline).intersection(set(doc_mark_comment_uuids_in_online)))

            # 同步offline_doc_mark_comment
            if offline_dmm_to_insert:
                offline_dmm_to_insert = dbsession.query(OfflineDocMarkComment).filter(OfflineDocMarkComment.uuid.in_(offline_dmm_to_insert)).all()
                sync_doc_mark_comments = [DocMarkComment(uuid=i.uuid, doc_uuid=i.doc_uuid, name=i.name, position=i.position,
                                                        comment=i.comment, create_by_uuid=i.create_by_uuid,
                                                        create_time=i.create_time, locate_position=i.locate_position,
                                                        update_by_uuid=i.update_by_uuid, update_time=i.update_time,
                                                        _source=i._source, appear_index_in_text=i.appear_index_in_text,
                                                        valid=i.valid) for i in offline_dmm_to_insert]
                target_dbsession.add_all(sync_doc_mark_comments)
                target_dbsession.commit()
            if offline_dmm_to_update:
                for dmm_uuid_offline in offline_dmm_to_update:
                    dmm_online = target_dbsession.query(DocMarkComment).filter_by(uuid=dmm_uuid_offline, valid=1).first()
                    dmm_offline = dbsession.query(OfflineDocMarkComment).filter_by(uuid=dmm_uuid_offline, valid=1).first()
                    dmm_online.doc_uuid = dmm_offline.doc_uuid
                    dmm_online.name = dmm_offline.name
                    dmm_online.position = dmm_offline.position
                    dmm_online.comment = dmm_offline.comment
                    dmm_online.create_by_uuid = dmm_offline.create_by_uuid
                    dmm_online.create_time = dmm_offline.create_time
                    dmm_online.update_by_uuid = dmm_offline.update_by_uuid
                    dmm_online.update_time = dmm_offline.update_time
                    dmm_online.valid = dmm_offline.valid
                    dmm_online._source = dmm_offline._source
                    dmm_online.appear_index_in_text = dmm_offline.appear_index_in_text
                    dmm_online.locate_position = dmm_offline.locate_position
                target_dbsession.commit()
            res_records.append(
                f"批注记录表同步完成！新增{len(offline_dmm_to_insert)}条数据，更新{len(offline_dmm_to_update)}条数据。")
        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("批注记录表同步失败！")
        # print("doc_mark_comment success")

        # </editor-fold>

        # 同步doc_mark相关表
        def insert_and_update_records(source_db, target_db, fields=[]):
            records_in_source_db = dbsession.query(source_db).filter(source_db.valid == 1,
                                                                   or_(
                                                                       source_db.create_time > sync_time,
                                                                       source_db.update_time > sync_time)).all()
            uuids_in_source_db = [i.uuid for i in records_in_source_db]
            uuids_in_target_db = target_dbsession.query(target_db).with_entities(target_db.uuid).filter_by(valid=1).all()
            uuids_in_target_db = [i[0] for i in uuids_in_target_db]
            # 更新create_by_uuid、update_by_uuid
            for i in records_in_source_db:
                i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid) if i.create_by_uuid else None
                i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid) if i.update_by_uuid else None

            # source_db-target_db：计算是否有要插入的数据
            records_to_insert = list(set(uuids_in_source_db).difference(set(uuids_in_target_db)))
            # source_db-target_db：计算是否有要更新的数据
            records_to_update = list(set(uuids_in_source_db).intersection(set(uuids_in_target_db)))

            # 同步
            if records_to_insert:
                records_to_insert = dbsession.query(source_db).filter(
                    source_db.uuid.in_(records_to_insert)).all()
                for item in records_to_insert:
                    cons = [("{} = item.{}".format(field, field)) for field in fields]
                    cons = tuple(cons)
                    cons = ','.join(cons)
                    sync_record_insert = eval(f"target_db({cons})")
                    target_dbsession.add(sync_record_insert)
                target_dbsession.commit()

            if records_to_update:
                for uuid_source_db in records_to_update:
                    record_target_db = target_dbsession.query(target_db).filter_by(uuid=uuid_source_db, valid=1).first()
                    record_source_db = dbsession.query(source_db).filter_by(uuid=uuid_source_db, valid=1).first()
                    for field in fields:
                        if field != 'uuid':
                            exec(f"record_target_db.{field} = record_source_db.{field}")
                    target_dbsession.commit()

            return len(records_to_insert), len(records_to_update)


        # <editor-fold desc="sync_offline of DocMarkEntity">
        # 定义模型类
        try:
            class DocMarkEntity(Target_Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_entity'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                word = db.Column(db.String)
                entity_uuid = db.Column(db.String)
                source = db.Column(db.Integer)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                appear_index_in_text = db.Column(db.JSON)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                appear_text = db.Column(db.String)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkEntity %r>' % self.uuid

            class OfflineDocMarkEntity(Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_entity'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                word = db.Column(db.String)
                entity_uuid = db.Column(db.String)
                source = db.Column(db.Integer)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                appear_text = db.Column(db.String)
                appear_index_in_text = db.Column(db.JSON)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkEntity %r>' % self.uuid

            doc_mark_entity_in_offline = dbsession.query(OfflineDocMarkEntity).filter(
                OfflineDocMarkEntity.valid == 1,
                or_(
                    OfflineDocMarkEntity.create_time > sync_time,
                    OfflineDocMarkEntity.update_time > sync_time)).all()

            # 将doc_mark_entity的entity_uuid更新到dict里
            entity_uuid_in_dme = dbsession.query(OfflineDocMarkEntity).with_entities(
                OfflineDocMarkEntity.entity_uuid).filter_by(valid=1).distinct().all()
            for entity_uuid in entity_uuid_in_dme:
                if entity_uuid not in entity_uuid_dict_trans.keys():
                    entity_sign_in_offline = dbsession.query(OfflineEntity).with_entities(OfflineEntity.name,
                                                                                          OfflineEntity.category_uuid,
                                                                                          OfflineEntity.uuid).filter_by(
                        valid=1, uuid=entity_uuid).first()
                    entity_sign_in_offline = entity_sign_in_offline[0] + str(
                        ec_uuid_dict_trans.get(entity_sign_in_offline[1]))
                    entity_uuid_dict_trans[entity_uuid] = online_dict_trans_entity.get(entity_sign_in_offline)

            # 更新create_by_uuid、update_by_uuid、entity_uuid
            for i in doc_mark_entity_in_offline:
                i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
                i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)
                i.entity_uuid = entity_uuid_dict_trans.get(i.entity_uuid)

            fields = ["uuid", "doc_uuid", "word", "entity_uuid", "source", "create_by_uuid", "create_time",
                      "update_by_uuid", "update_time", "appear_text", "appear_index_in_text", "_source", "valid", "position"]

            insert_num, update_num = insert_and_update_records(OfflineDocMarkEntity, DocMarkEntity, fields)
            res_records.append(f"标注实体表同步完成！新增{insert_num}条数据，更新{update_num}条数据。")

        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("标注实体表同步失败！")

        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkPlace">
        # 定义模型类
        try:
            class DocMarkPlace(Target_Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_place'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                word = db.Column(db.Text)
                type = db.Column(db.Integer)
                place_uuid = db.Column(db.String)
                direction = db.Column(db.Text)
                place_lon = db.Column(db.Text)
                place_lat = db.Column(db.Text)
                height = db.Column(db.Text)
                unit = db.Column(db.Text)
                dms = db.Column(db.JSON)
                distance = db.Column(db.Integer)
                relation = db.Column(db.Text)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.DateTime)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.DateTime)
                valid = db.Column(db.Integer)
                entity_or_sys = db.Column(db.Integer)
                appear_index_in_text = db.Column(db.JSON)
                _source = db.Column(db.String)
                word_count = db.Column(db.String)
                word_sentence = db.Column(db.String)
                source_type = db.Column(db.Integer)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkPlace %r>' % self.uuid

            class OfflineDocMarkPlace(Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_place'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                word = db.Column(db.Text)
                type = db.Column(db.Integer)
                place_uuid = db.Column(db.String)
                direction = db.Column(db.Text)
                place_lon = db.Column(db.Text)
                place_lat = db.Column(db.Text)
                height = db.Column(db.Text)
                unit = db.Column(db.Text)
                dms = db.Column(db.JSON)
                distance = db.Column(db.Integer)
                relation = db.Column(db.Text)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.DateTime)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.DateTime)
                valid = db.Column(db.Integer)
                entity_or_sys = db.Column(db.Integer)
                appear_index_in_text = db.Column(db.JSON)
                _source = db.Column(db.String)
                word_count = db.Column(db.String)
                word_sentence = db.Column(db.String)
                source_type = db.Column(db.Integer)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkPlace %r>' % self.uuid

            doc_mark_place_in_offline = dbsession.query(OfflineDocMarkPlace).filter(
                OfflineDocMarkPlace.valid == 1,
                or_(
                    OfflineDocMarkPlace.create_time > sync_time,
                    OfflineDocMarkPlace.update_time > sync_time)).all()

            # 将doc_mark_place的place_uuid更新到dict里
            place_uuid_in_dmp = dbsession.query(OfflineDocMarkPlace).with_entities(
                OfflineDocMarkPlace.place_uuid).filter_by(valid=1).distinct().all()
            for place_uuid in place_uuid_in_dmp:
                if place_uuid not in entity_uuid_dict_trans.keys():
                    entity_sign_in_offline = dbsession.query(OfflineEntity).with_entities(OfflineEntity.name,
                                                                                                   OfflineEntity.category_uuid,
                                                                                                   OfflineEntity.uuid).filter_by(
                        valid=1, uuid=place_uuid).first()
                    entity_sign_in_offline = entity_sign_in_offline[0] + str(ec_uuid_dict_trans.get(entity_sign_in_offline[1]))
                    entity_uuid_dict_trans[place_uuid] = online_dict_trans_entity.get(entity_sign_in_offline)

            # 更新create_by_uuid、update_by_uuid、place_uuid
            for i in doc_mark_place_in_offline:
                i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
                i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)
                i.place_uuid = entity_uuid_dict_trans.get(i.place_uuid)

            # 同步offline_doc_mark_place
            fields = ["uuid", "doc_uuid", "word", "type", "place_uuid", "direction", "place_lon", "place_lat",
                      "height", "unit", "dms", "distance", "relation", "create_by_uuid", "create_time",
                      "update_by_uuid", "update_time", "entity_or_sys", "appear_index_in_text", "_source", "valid",
                      "word_count", "word_sentence", "source_type", "position"]

            insert_num, update_num = insert_and_update_records(OfflineDocMarkPlace, DocMarkPlace, fields)
            res_records.append(f"标注地点表同步完成！新增{insert_num}条数据，更新{update_num}条数据。")

        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("标注地点表同步失败！")

        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkRelationProperty">
        # 定义模型类
        try:
            class DocMarkRelationProperty(Target_Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_relation_property'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                nid = db.Column(db.Text)
                relation_uuid = db.Column(db.String)
                relation_name = db.Column(db.Text)
                start_time = db.Column(db.DateTime)
                start_type = db.Column(db.Text)
                end_time = db.Column(db.DateTime)
                end_type = db.Column(db.Text)
                source_entity_uuid = db.Column(db.String)
                target_entity_uuid = db.Column(db.String)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkRelationProperty %r>' % self.uuid

            class OfflineDocMarkRelationProperty(Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_relation_property'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                nid = db.Column(db.Text)
                relation_uuid = db.Column(db.String)
                relation_name = db.Column(db.Text)
                start_time = db.Column(db.DateTime)
                start_type = db.Column(db.Text)
                end_time = db.Column(db.DateTime)
                end_type = db.Column(db.Text)
                source_entity_uuid = db.Column(db.String)
                target_entity_uuid = db.Column(db.String)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkRelationProperty %r>' % self.uuid

            doc_mark_relation_property_in_offline = dbsession.query(OfflineDocMarkRelationProperty).filter(
                OfflineDocMarkRelationProperty.valid == 1, or_(OfflineDocMarkRelationProperty.create_time > sync_time,
                                                               OfflineDocMarkRelationProperty.update_time > sync_time)).all()
            # 更新relation_uuid、create_by_uuid、update_by_uuid
            for i in doc_mark_relation_property_in_offline:
                if rc_uuid_dict_trans.get(i.relation_uuid): # 新插入的doc_rc的外键relation_uuid在本次同步数据内
                    i.relation_uuid = rc_uuid_dict_trans.get(i.relation_uuid)
                else:
                    offline_rc_old = dbsession.query(OfflineRelationCategory).filter_by(uuid=i.relation_uuid,
                                                                                           valid=1).first()
                    for index, value in enumerate(offline_rc_old.source_entity_category_uuids):
                        offline_rc_old.source_entity_category_uuids[index] = new_ec_uuid_dict_trans.get(value)
                    for index, value in enumerate(offline_rc_old.target_entity_category_uuids):
                        offline_rc_old.target_entity_category_uuids[index] = new_ec_uuid_dict_trans.get(value)
                    rc_online = target_dbsession.query(RelationCategory).filter(
                        RelationCategory.relation_name == offline_rc_old.relation_name,
                        RelationCategory.source_entity_category_uuids.op('@>')(offline_rc_old.source_entity_category_uuids),
                        RelationCategory.target_entity_category_uuids.op('@>')(offline_rc_old.target_entity_category_uuids),
                        RelationCategory.valid == 1).first()
                    i.relation_uuid = rc_online.uuid

                i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
                i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)

            # 同步offline_doc_mark_relation_property
            fields = ["uuid", "doc_uuid", "nid", "relation_uuid", "relation_name", "start_time", "start_type", "end_time",
                      "end_type", "source_entity_uuid", "target_entity_uuid", "create_by_uuid", "create_time",
                      "update_by_uuid", "update_time", "_source", "valid", "position"]

            insert_num, update_num = insert_and_update_records(OfflineDocMarkRelationProperty, DocMarkRelationProperty, fields)
            res_records.append(f"标注关系表同步完成！新增{insert_num}条数据，更新{update_num}条数据。")

        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("标注关系表同步失败！")

        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkTimeTag">
        # 定义模型类
        try:
            class DocMarkTimeTag(Target_Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_time_tag'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                word = db.Column(db.Text)
                format_date = db.Column(db.DateTime)
                format_date_end = db.Column(db.DateTime)
                mark_position = db.Column(db.Text)
                time_type = db.Column(db.Integer)
                reserve_fields = db.Column(db.Text)
                valid = db.Column(db.Integer)
                arab_time = db.Column(db.Text)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                appear_index_in_text = db.Column(db.JSON)
                _source = db.Column(db.String)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkTimeTag %r>' % self.uuid

            class OfflineDocMarkTimeTag(Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_time_tag'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                word = db.Column(db.Text)
                format_date = db.Column(db.DateTime)
                format_date_end = db.Column(db.DateTime)
                mark_position = db.Column(db.Text)
                time_type = db.Column(db.Integer)
                reserve_fields = db.Column(db.Text)
                valid = db.Column(db.Integer)
                arab_time = db.Column(db.Text)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                appear_index_in_text = db.Column(db.JSON)
                _source = db.Column(db.String)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkTimeTag %r>' % self.uuid

            doc_mark_time_tag_in_offline = dbsession.query(OfflineDocMarkTimeTag).filter(OfflineDocMarkTimeTag.valid == 1,
                                                                                         or_(
                                                                                             OfflineDocMarkTimeTag.create_time > sync_time,
                                                                                             OfflineDocMarkTimeTag.update_time > sync_time)).all()
            # 更新create_by_uuid、update_by_uuid
            for i in doc_mark_time_tag_in_offline:
                i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
                i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)
            # 同步doc_mark_time_tag_in_offline
            fields = ["uuid", "doc_uuid", "word", "format_date", "format_date_end", "mark_position", "time_type",
                      "reserve_fields", "arab_time", "create_by_uuid", "create_time", "update_by_uuid", "update_time",
                      "appear_index_in_text", "_source", "valid", "position"]

            insert_num, update_num = insert_and_update_records(OfflineDocMarkTimeTag, DocMarkTimeTag, fields)
            res_records.append(f"标注时间表同步完成！新增{insert_num}条数据，更新{update_num}条数据。")

        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("标注时间表同步失败！")

        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkMind">
        # 定义模型类
        try:
            class DocMarkMind(Target_Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_mind'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                parent_uuid = db.Column(db.String)
                doc_uuid = db.Column(db.String)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkMind %r>' % self.uuid

            class OfflineDocMarkMind(Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_mind'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                parent_uuid = db.Column(db.String)
                doc_uuid = db.Column(db.String)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkMind %r>' % self.uuid

            doc_mark_mind_in_offline = dbsession.query(OfflineDocMarkMind).filter(OfflineDocMarkMind.valid == 1,
                                                                                         or_(
                                                                                             OfflineDocMarkMind.create_time > sync_time,
                                                                                             OfflineDocMarkMind.update_time > sync_time)).all()
            # 同步doc_mark_mind_in_offline
            fields = ["uuid", "name", "parent_uuid", "doc_uuid", "create_time", "update_time", "_source", "valid", "position"]

            insert_num, update_num = insert_and_update_records(OfflineDocMarkMind, DocMarkMind, fields)
            res_records.append(f"标注导图表同步完成！新增{insert_num}条数据，更新{update_num}条数据。")

        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("标注导图表同步失败！")

        # print("doc_mark_mind success")
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkAdvise">
        # 定义模型类
        try:
            class DocMarkAdvise(Target_Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_advise'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                mark_uuid = db.Column(db.String)
                type = db.Column(db.Integer)
                content = db.Column(db.Text)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)

                def __repr__(self):
                    return '<DocMarkAdvise %r>' % self.uuid

            class OfflineDocMarkAdvise(Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_advise'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                mark_uuid = db.Column(db.String)
                type = db.Column(db.Integer)
                content = db.Column(db.Text)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)

                def __repr__(self):
                    return '<DocMarkAdvise %r>' % self.uuid

            doc_mark_advise_in_offline = dbsession.query(OfflineDocMarkAdvise).filter(OfflineDocMarkAdvise.valid == 1,
                                                                                  or_(
                                                                                      OfflineDocMarkAdvise.create_time > sync_time,
                                                                                      OfflineDocMarkAdvise.update_time > sync_time)).all()
            uuids_in_offline = [i.uuid for i in doc_mark_advise_in_offline]
            uuids_in_online = target_dbsession.query(DocMarkAdvise).with_entities(DocMarkAdvise.uuid).filter_by(valid=1).all()
            uuids_in_online = [i[0] for i in uuids_in_online]
            # 更新create_by_uuid、update_by_uuid
            for i in doc_mark_advise_in_offline:
                i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid) if i.create_by_uuid else None
                i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid) if i.update_by_uuid else None

            # offline-online：计算是否有要插入的数据
            doc_mark_advise_to_insert = list(set(uuids_in_offline).difference(set(uuids_in_online)))
            # offline-online：计算是否有要更新的数据
            doc_mark_advise_to_update = list(set(uuids_in_offline).intersection(set(uuids_in_online)))

            # 同步doc_mark_advise_in_offline
            if doc_mark_advise_to_insert:
                doc_mark_advise_to_insert = dbsession.query(OfflineDocMarkAdvise).filter(OfflineDocMarkAdvise.uuid.in_(doc_mark_advise_to_insert)).all()
                sync_doc_mark_advises = [
                    DocMarkAdvise(uuid=i.uuid, doc_uuid=i.doc_uuid, mark_uuid=i.mark_uuid, type=i.type, content=i.content,
                                  create_by_uuid=i.create_by_uuid, create_time=i.create_time, update_by_uuid=i.update_by_uuid,
                                  update_time=i.update_time, _source=i._source, valid=i.valid) for i in
                    doc_mark_advise_to_insert]
                target_dbsession.add_all(sync_doc_mark_advises)
                target_dbsession.commit()

            if doc_mark_advise_to_update:
                for dma_uuid_offline in doc_mark_advise_to_update:
                    doc_mark_advise = target_dbsession.query(DocMarkAdvise).filter_by(uuid=dma_uuid_offline, valid=1).first()
                    dma_offline = dbsession.query(OfflineDocMarkAdvise).filter_by(uuid=dma_uuid_offline, valid=1).first()
                    doc_mark_advise.doc_uuid = dma_offline.doc_uuid
                    doc_mark_advise.mark_uuid = dma_offline.mark_uuid
                    doc_mark_advise.type = dma_offline.type
                    doc_mark_advise.content = dma_offline.content
                    doc_mark_advise.create_by_uuid = dma_offline.create_by_uuid
                    doc_mark_advise.create_time = dma_offline.create_time
                    doc_mark_advise.update_by_uuid = dma_offline.update_by_uuid
                    doc_mark_advise.update_time = dma_offline.update_time
                    doc_mark_advise.valid = dma_offline.valid
                    doc_mark_advise._source = dma_offline._source
                target_dbsession.commit()
            res_records.append(
                f"标注建议表同步完成！新增{len(doc_mark_advise_to_insert)}条数据，更新{len(doc_mark_advise_to_update)}条数据。")
        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("标注建议表同步失败！")

        # print("doc_mark_advise success")
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocumentRecords">
        # 定义模型类
        try:
            class DocumentRecords(Target_Base):  # 自动加载表结构
                __tablename__ = 'document_records'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                operate_type = db.Column(db.Integer)
                _source = db.Column(db.String)

                def __repr__(self):
                    return '<DocumentRecords %r>' % self.uuid

            class OfflineDocumentRecords(Base):  # 自动加载表结构
                __tablename__ = 'document_records'
                uuid = db.Column(db.String, primary_key=True)
                doc_uuid = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                operate_type = db.Column(db.Integer)
                _source = db.Column(db.String)

                def __repr__(self):
                    return '<DocumentRecords %r>' % self.uuid

            # 更新create_by_uuid、update_by_uuid
            document_records_in_offline = dbsession.query(OfflineDocumentRecords).filter(
                OfflineDocumentRecords.create_time > sync_time).all()
            # 更新create_by_uuid
            for i in document_records_in_offline:
                i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)

            # 同步document_records_in_offline
            sync_document_records = [DocumentRecords(uuid=i.uuid, doc_uuid=i.doc_uuid, create_by_uuid=i.create_by_uuid,
                                                     create_time=i.create_time, operate_type=i.operate_type,
                                                     _source=i._source) for i in document_records_in_offline]
            target_dbsession.add_all(sync_document_records)
            target_dbsession.commit()
            res_records.append(
                f"文档记录表同步完成！新增{len(sync_document_records)}条数据。")
        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("文档记录表同步失败！")
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkEvent">
        # 定义模型类
        try:
            class DocMarkEvent(Target_Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_event'
                uuid = db.Column(db.String, primary_key=True)
                event_id = db.Column(db.String)
                event_desc = db.Column(db.String)
                event_subject = db.Column(db.JSON)
                event_predicate = db.Column(db.String)
                event_object = db.Column(db.JSON)
                event_time = db.Column(db.JSON)
                event_address = db.Column(db.JSON)
                event_why = db.Column(db.String)
                event_result = db.Column(db.String)
                event_conduct = db.Column(db.String)
                event_talk = db.Column(db.String)
                event_how = db.Column(db.String)
                doc_uuid = db.Column(db.String)
                customer_uuid = db.Column(db.String)
                parent_uuid = db.Column(db.String)
                title = db.Column(db.String)
                event_class_uuid = db.Column(db.String)
                event_type_uuid = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                add_time = db.Column(db.TIMESTAMP)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkEvent %r>' % self.uuid

            class OfflineDocMarkEvent(Base):  # 自动加载表结构
                __tablename__ = 'doc_mark_event'
                uuid = db.Column(db.String, primary_key=True)
                event_id = db.Column(db.String)
                event_desc = db.Column(db.String)
                event_subject = db.Column(db.JSON)
                event_predicate = db.Column(db.String)
                event_object = db.Column(db.JSON)
                event_time = db.Column(db.JSON)
                event_address = db.Column(db.JSON)
                event_why = db.Column(db.String)
                event_result = db.Column(db.String)
                event_conduct = db.Column(db.String)
                event_talk = db.Column(db.String)
                event_how = db.Column(db.String)
                doc_uuid = db.Column(db.String)
                customer_uuid = db.Column(db.String)
                parent_uuid = db.Column(db.String)
                title = db.Column(db.String)
                event_class_uuid = db.Column(db.String)
                event_type_uuid = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                add_time = db.Column(db.TIMESTAMP)
                valid = db.Column(db.Integer)
                _source = db.Column(db.String)
                position = db.Column(JSONB)

                def __repr__(self):
                    return '<DocMarkEvent %r>' % self.uuid

            doc_mark_event_in_offline = dbsession.query(OfflineDocMarkEvent).filter(OfflineDocMarkEvent.valid == 1,
                                                                                      or_(
                                                                                          OfflineDocMarkEvent.create_time > sync_time,
                                                                                          OfflineDocMarkEvent.update_time > sync_time)).all()

            # 更新customer_uuid、event_class_uuid、event_type_uuid、create_by_uuid、update_by_uuid
            for i in doc_mark_event_in_offline:
                i.customer_uuid = customer_uuid_dict_trans.get(i.customer_uuid)
                i.event_class_uuid = event_class_uuid_dict_trans.get(i.event_class_uuid)
                i.event_type_uuid = event_cate_uuid_dict_trans.get(i.event_type_uuid)
                i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid) if i.create_by_uuid else None
                i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid) if i.update_by_uuid else None

            # 同步doc_mark_events_in_offline
            fields = ["uuid", "event_id", "event_desc", "event_subject", "event_predicate", "event_object", "event_time",
                      "event_address", "event_why", "event_result", "event_conduct", "event_talk", "event_how",
                      "doc_uuid", "customer_uuid", "parent_uuid", "title", "event_class_uuid", "event_type_uuid",
                      "create_by_uuid", "create_time", "update_by_uuid", "update_time", "add_time", "_source",
                      "valid", "position"]

            insert_num, update_num = insert_and_update_records(OfflineDocMarkEvent, DocMarkEvent, fields)
            res_records.append(f"标注事件表同步完成！新增{insert_num}条数据，更新{update_num}条数据。")

        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("标注事件表同步失败！")
        # </editor-fold>

        # <editor-fold desc="sync_offline of Catalog">
        # 定义文档目录类
        try:
            class Catalog(Target_Base):  # 自动加载表结构
                __tablename__ = 'catalog'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                parent_uuid = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                tagging_tabs = db.Column(db.JSON)
                _source = db.Column(db.String)
                sort = db.Column(db.Integer)

                def __repr__(self):
                    return '<Catalog %r>' % self.name

            class OfflineCalalog(Base):  # 自动加载表结构
                __tablename__ = 'catalog'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                parent_uuid = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                tagging_tabs = db.Column(db.JSON)
                _source = db.Column(db.String)
                sort = db.Column(db.Integer)

                def __repr__(self):
                    return '<Catalog %r>' % self.name

            online_catalog_uuids = []
            offline_catalog_uuids = []
            online_catalog_path = []
            offline_catalog_path = []
            offline_catalog_path_dict = {}
            online_catalog_path_dict = {}
            offline_online_catalog_dict = {}
            sync_catalog_uuid_list = []
            # 存储根目录
            catalogs = target_dbsession.query(Catalog).filter_by(parent_uuid=None).all()
            for catalog in catalogs:
                online_catalog_uuids.append(catalog.uuid)
                online_catalog_path.append([catalog.name, 1])
                if 1 not in online_catalog_path_dict.keys():
                    online_catalog_path_dict[1] = [catalog.name]
                else:
                    online_catalog_path_dict[1].append(catalog.name)
            offline_catalogs = dbsession.query(OfflineCalalog).filter_by(parent_uuid=None).all()
            for offline_catelog in offline_catalogs:
                offline_catalog_uuids.append(offline_catelog.uuid)
                offline_catalog_path.append([offline_catelog.name, 1])
                if 1 not in offline_catalog_path_dict.keys():
                    offline_catalog_path_dict[1] = [offline_catelog.name]
                else:
                    offline_catalog_path_dict[1].append(offline_catelog.name)

            # 存储路径
            def get_catalog_online_path(uuid):
                catalog = target_dbsession.query(Catalog).filter_by(uuid=uuid).first()
                res = [catalog.name]
                while catalog.parent_uuid:
                    catalog = target_dbsession.query(Catalog).filter_by(uuid=catalog.parent_uuid).first()
                    res.append(catalog.name)
                res.reverse()
                path = "/".join(res)
                catalog_level = path.count("/") + 1
                if catalog_level not in online_catalog_path_dict.keys():
                    online_catalog_path_dict[catalog_level] = [path]
                else:
                    online_catalog_path_dict[catalog_level].append(path)
                return [path, catalog_level]

            def get_catalog_offline_path(uuid):
                catalog = dbsession.query(OfflineCalalog).filter_by(uuid=uuid).first()
                res = [catalog.name]
                while catalog.parent_uuid:
                    catalog = dbsession.query(OfflineCalalog).filter_by(uuid=catalog.parent_uuid).first()
                    res.append(catalog.name)
                res.reverse()
                path = "/".join(res)
                catalog_level = path.count("/") + 1
                if catalog_level not in offline_catalog_path_dict.keys():
                    offline_catalog_path_dict[catalog_level] = [path]
                else:
                    offline_catalog_path_dict[catalog_level].append(path)
                return [path, catalog_level]

            # 层级遍历所有目录
            for uuid in online_catalog_uuids:
                tmp_catalogs = target_dbsession.query(Catalog).filter_by(parent_uuid=uuid).all()
                for tmp_catalog in tmp_catalogs:
                    online_catalog_uuids.append(tmp_catalog.uuid)
                    online_catalog_path.append(get_catalog_online_path(tmp_catalog.uuid))
            for uuid in offline_catalog_uuids:
                tmp_catalogs = dbsession.query(OfflineCalalog).filter_by(parent_uuid=uuid).all()
                for tmp_catalog in tmp_catalogs:
                    offline_catalog_uuids.append(tmp_catalog.uuid)
                    offline_catalog_path.append(get_catalog_offline_path(tmp_catalog.uuid))
            # 改变离线版目录的父节点和填充offline_online_catalog_dict字典
            for offline_item in offline_catalog_path:
                offline_index = offline_catalog_path.index(offline_item)
                tmp_offline_catalog = dbsession.query(OfflineCalalog).filter_by(
                    uuid=offline_catalog_uuids[offline_index]).first()
                if offline_item[1] in online_catalog_path_dict.keys() and offline_item[0] in online_catalog_path_dict[
                    offline_item[1]]:  # 同级,同名
                    online_index = online_catalog_path.index(offline_item)
                    offline_online_catalog_dict[offline_catalog_uuids[offline_index]] = online_catalog_uuids[
                        online_index]  # 存进字典
                    tmp_online_catalog = target_dbsession.query(Catalog).filter_by(uuid=online_catalog_uuids[online_index]).first()
                    tmp_offline_catalog.parent_uuid = tmp_online_catalog.parent_uuid  # 改目录的父节点
                else:
                    sync_catalog_uuid_list.append(tmp_offline_catalog.uuid)
                    offline_online_catalog_dict[tmp_offline_catalog.uuid] = tmp_offline_catalog.uuid  # 存进字典，uuid不变
                    tmp_offline_catalog.parent_uuid = offline_online_catalog_dict.get(tmp_offline_catalog.parent_uuid)
            # 如果有要插入的数据
            if sync_catalog_uuid_list:
                offline_catalog = dbsession.query(OfflineCalalog).filter(
                    OfflineCalalog.uuid.in_(sync_catalog_uuid_list)).all()
                sync_catalog = [Catalog(uuid=offline_online_catalog_dict.get(i.uuid),
                                        name=i.name,
                                        tagging_tabs=i.tagging_tabs,
                                        parent_uuid=i.parent_uuid,
                                        create_by_uuid=customer_uuid_dict_trans.get(i.create_by_uuid),
                                        update_by_uuid=customer_uuid_dict_trans.get(i.update_by_uuid),
                                        sort=i.sort,
                                        _source=i._source,
                                        create_time=i.create_time,
                                        update_time=i.update_time) for i in offline_catalog]
                target_dbsession.add_all(sync_catalog)
                target_dbsession.commit()
            res_records.append(f"目录表同步完成！新增{len(sync_catalog_uuid_list)}条数据。")

        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("目录表同步失败！")

        # </editor-fold>

        # <editor-fold desc="sync_offline of Document">
        # 定义文档类
        try:
            class Document(Target_Base):
                __tablename__ = 'document'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                category = db.Column(db.Text)
                savepath = db.Column(db.Text)
                content = db.Column(db.JSON)
                catalog_uuid = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                permission_id = db.Column(db.Integer)
                status = db.Column(db.Integer)
                keywords = db.Column(db.JSON)
                md5 = db.Column(db.String)
                is_favorite = db.Column(db.Integer)
                _source = db.Column(db.String)
                html_path = db.Column(db.String)
                valid = db.Column(db.Integer)

            def __repr__(self):
                return '<Document %r>' % self.name

            class OfflineDocument(Base):
                __tablename__ = 'document'
                uuid = db.Column(db.String, primary_key=True)
                name = db.Column(db.Text)
                category = db.Column(db.Text)
                savepath = db.Column(db.Text)
                content = db.Column(db.JSON)
                catalog_uuid = db.Column(db.String)
                create_by_uuid = db.Column(db.String)
                create_time = db.Column(db.TIMESTAMP)
                update_by_uuid = db.Column(db.String)
                update_time = db.Column(db.TIMESTAMP)
                permission_id = db.Column(db.Integer)
                status = db.Column(db.Integer)
                keywords = db.Column(db.JSON)
                md5 = db.Column(db.String)
                is_favorite = db.Column(db.Integer)
                _source = db.Column(db.String)
                html_path = db.Column(db.String)
                valid = db.Column(db.Integer)

            def __repr__(self):
                return '<Document %r>' % self.name

            offline_document = dbsession.query(OfflineDocument).filter(OfflineDocument.valid == 1,or_(
                OfflineDocument.create_time > sync_time,
                OfflineDocument.update_time > sync_time)).all()
            print (sync_time)
            sync_document = [Document(uuid=i.uuid,
                                      name=i.name,
                                      category=i.category,
                                      savepath=i.savepath,
                                      content=i.content,
                                      create_time=i.create_time,
                                      status=i.status,
                                      keywords=i.keywords,
                                      md5=i.md5,
                                      is_favorite=i.is_favorite,
                                      _source=i._source,
                                      create_by_uuid=customer_uuid_dict_trans.get(i.create_by_uuid),
                                      update_by_uuid=customer_uuid_dict_trans.get(i.update_by_uuid),
                                      catalog_uuid=offline_online_catalog_dict.get(i.catalog_uuid),
                                      html_path=i.html_path,
                                      valid=1,
                                      update_time=i.update_time) for i in offline_document]
            target_dbsession.add_all(sync_document)
            target_dbsession.commit()
            res_records.append(f"文档表同步完成！新增{len(sync_document)}条数据。")

        except Exception as e:
            print(str(e))
            target_dbsession.rollback()
            res_records.append("文档表同步失败！")
        # </editor-fold>

        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = "http://{}:{}/api/get_file_from_source".format(SOURCE_PG_DB_SERVER_IP, LOCAL_PORT)
        body = {"source_ip": SOURCE_PG_DB_SERVER_IP}
        data = json.dumps(body)
        url_list = requests.post(url=url, data=data, headers=header)

        header = {"Content-Type": "application/json; charset=UTF-8"}
        url_list = json.loads(url_list.text)
        body_url = {"file_paths": url_list}
        data_url = json.dumps(body_url)
        url = "http://{}:{}/api/save_file_to_target".format(TARGET_PG_DB_SERVER_IP, LOCAL_PORT)
        result = requests.post(url=url, data=data_url, headers=header)

        print(res_records)
        res = success_res(data=res_records)

    except Exception as e:
        print(str(e))
        if dbsession:
            dbsession.close()
        res = fail_res()

    return jsonify(res)

# 保存到目标主机
@blue_print.route('/save_file_to_target', methods=['POST'])
def save_file_to_target():
    file_paths = request.json.get('file_paths', [])
    for url in file_paths:
        filename = url.split("/")
        file_path = os.path.join(os.getcwd(), 'static', 'upload', filename[-1])
        save_path = os.path.join(os.getcwd(), 'static', 'upload')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        try:
            urllib.request.urlretrieve(url, filename=file_path)

        except Exception as e:
            print("数据传输错误")
            print(e)

    res = success_res()
    return jsonify(res)


# 从源主机获取url
@blue_print.route('/get_file_from_source', methods=['POST'])
def get_file_from_source():
    url_list = []
    source_ip = request.json.get('source_ip', "")
    file_dir = os.path.join(os.getcwd(), 'static', 'upload')
    for files in os.walk(file_dir):
        for file in files:
            url = "http://{0}:{1}/api/static/upload/{2}".format(source_ip, LOCAL_PORT, file)
            url_list.append(url)
    return json.dumps(url_list)
