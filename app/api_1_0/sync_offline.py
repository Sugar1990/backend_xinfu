# -*- coding: UTF-8 -*-
import os
import time
from flask import jsonify, request
from sqlalchemy.dialects.postgresql import JSONB

from . import api_sync_offline as blue_print
from ..models import db
from .utils import success_res, fail_res
from sqlalchemy import create_engine, MetaData, Table, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from ..conf import PG_USER_NAME, PG_USER_PASSWORD, PG_DB_SERVER_IP, PG_DB_PORT, PG_DB_NAME


@blue_print.route('/show_target_database_information', methods=['GET'])
def show_target_database_information():
    data = {"target_pg_db_server_ip": PG_DB_SERVER_IP, "target_pg_db_port": PG_DB_PORT,
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


@blue_print.route('/sync_offline', methods=['POST'])
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
        db.session.commit()

        # <editor-fold desc="sync_source of Customer">
        # 定义模型类
        class SourceCustomer(Base):  # 自动加载表结构
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

        class TargetCustomer(Target_Base):  # 自动加载表结构
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

        # source所有uuid/troop_number，唯一性（去重）判断
        uuids_and_troop_in_source = dbsession.query(SourceCustomer).with_entities(SourceCustomer.uuid,
                                                                                  SourceCustomer.troop_number).filter(
            SourceCustomer.valid == 1,
            or_(SourceCustomer.create_time > sync_time, SourceCustomer.update_time > sync_time)).all()
        troop_numbers_in_source = [i[1] for i in uuids_and_troop_in_source]

        # target所有uuid/troop_number，唯一性（去重）判断
        uuids_and_troop_in_target = target_dbsession.query(TargetCustomer).with_entities(TargetCustomer.uuid,
                                                                                         TargetCustomer.troop_number).filter(
            TargetCustomer.valid == 1).all()
        troop_numbers_in_target = [i[1] for i in uuids_and_troop_in_target]

        # 记录uuid变化----customer_uuid_dict_trans
        target_dict_trans = {}
        customer_uuid_dict_trans = {}

        for i in uuids_and_troop_in_target:
            if i[1] not in target_dict_trans.keys():
                target_dict_trans[i[1]] = i[0]  # [{"troop_number": "uuid"}]

        # 遍历source所有数据，不做时间筛选，构造dict
        uuids_and_troop_in_source_for_dict = dbsession.query(SourceCustomer).with_entities(SourceCustomer.uuid,
                                                                                           SourceCustomer.troop_number).filter_by(
            valid=1).all()

        for source_customer in uuids_and_troop_in_source_for_dict:
            # offtroop存在, {"offuuid": "onuuid"}, offtroop不存在, {"offuuid": "offuuid"}
            customer_uuid_dict_trans[source_customer[0]] = target_dict_trans[
                source_customer[1]] if target_dict_trans.get(source_customer[1], "") else source_customer[0]

        # source-target：计算是否有要插入的数据
        source_troop_numbers_to_insert = list(set(troop_numbers_in_source).difference(set(troop_numbers_in_target)))
        # source-target：计算是否有要更新的数据
        source_troop_numbers_to_update = list(set(troop_numbers_in_source).intersection(set(troop_numbers_in_target)))

        # 如果有要插入的数据
        if source_troop_numbers_to_insert:
            source_customers = dbsession.query(SourceCustomer).filter(
                SourceCustomer.troop_number.in_(source_troop_numbers_to_insert)).all()
            sync_customers = [TargetCustomer(uuid=i.uuid,
                                             username=i.username,
                                             pwd=i.pwd,
                                             permission_id=i.permission_id,
                                             valid=i.valid,
                                             token=i.token,
                                             _source=i._source,
                                             power_score=i.power_score,
                                             troop_number=i.troop_number,
                                             create_time=i.create_time,
                                             update_time=i.update_time) for i in source_customers]
            db.session.add_all(sync_customers)
            db.session.commit()

            # 如果有要更新的数据  即_source相同，off_uuid=on_uuid
            if source_troop_numbers_to_update:
                source_customers = dbsession.query(SourceCustomer).filter(
                    SourceCustomer.troop_number.in_(source_troop_numbers_to_update)).all()
                for source_customer in source_customers:
                    target_customer = target_dbsession.query(TargetCustomer).filter_by(uuid=source_customer.uuid,
                                                                                       _source=source_customer._source,
                                                                                       valid=1).first()
                    if target_customer:
                        target_customer.username = source_customer.username
                        target_customer.pwd = source_customer.pwd
                        target_customer.power_score = source_customer.power_score
                        target_customer.update_time = source_customer.update_time
            db.session.commit()

        # print("customer_uuid_dict_trans:", customer_uuid_dict_trans)
        # </editor-fold>

        # <editor-fold desc="sync_source of EntityCategory">
        # # 定义模型类
        class SourceEntityCategory(Base):  # 自动加载表结构
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

        class TargetEntityCategory(Target_Base):  # 自动加载表结构
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

        # source所有name，唯一性（去重）判断
        uuids_and_names_in_source_ec = dbsession.query(SourceEntityCategory).with_entities(SourceEntityCategory.uuid,
                                                                                           SourceEntityCategory.name).filter(
            SourceEntityCategory.valid == 1,
            or_(SourceEntityCategory.create_time > sync_time, SourceEntityCategory.update_time > sync_time)).all()
        uuids_in_source = [i[0] for i in uuids_and_names_in_source_ec]
        names_in_source = [i[1] for i in uuids_and_names_in_source_ec]

        # target所有name，唯一性（去重）判断
        uuids_and_names_in_target_ec = target_dbsession.query(TargetEntityCategory).query.with_entities(
            TargetEntityCategory.uuid,
            TargetEntityCategory.name).filter(
            TargetEntityCategory.valid == 1).all()
        uuids_in_target = [i[0] for i in uuids_and_names_in_target_ec]
        names_in_target = [i[1] for i in uuids_and_names_in_target_ec]

        # 记录uuid变化----ec_uuid_dict_trans
        target_dict_trans = {}
        ec_uuid_dict_trans = {}

        for i in uuids_and_names_in_target_ec:
            if i[1] not in target_dict_trans.keys():
                target_dict_trans[i[1]] = i[0]  # {"onname": "onuuid"}

        # 遍历source所有数据，不做时间筛选，构造dict
        uuids_and_names_in_source_ec_for_dict = dbsession.query(SourceEntityCategory).with_entities(
            SourceEntityCategory.uuid,
            SourceEntityCategory.name).filter(
            SourceEntityCategory.valid == 1).all()

        for source_ec in uuids_and_names_in_source_ec_for_dict:
            # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
            ec_uuid_dict_trans[source_ec[0]] = target_dict_trans[
                source_ec[1]] if target_dict_trans.get(source_ec[1], "") else source_ec[0]

        # source-target：计算是否有要插入的数据
        source_names_to_insert = list(set(names_in_source).difference(set(names_in_target)))

        # source-target：计算是否有要更新的数据
        source_uuids_to_update = list(set(uuids_in_source).intersection(set(uuids_in_target)))

        # 如果有要插入的数据
        if source_names_to_insert:
            source_entity_cateogories = dbsession.query(SourceEntityCategory).filter(
                SourceEntityCategory.name.in_(source_names_to_insert)).all()
            sync_entity_categories = [TargetEntityCategory(uuid=i.uuid,
                                                           name=i.name,
                                                           valid=i.valid,
                                                           type=i.type,
                                                           _source=i._source,
                                                           create_time=i.create_time,
                                                           update_time=i.update_time) for i in
                                      source_entity_cateogories]
            db.session.add_all(sync_entity_categories)
            db.session.commit()

        # 如果有要更新的数据
        if source_uuids_to_update:
            source_entity_cateogories = dbsession.query(SourceEntityCategory).filter(
                SourceEntityCategory.uuid.in_(source_uuids_to_update)).all()
            for source_ec in source_entity_cateogories:
                target_ec = target_dbsession.query(TargetEntityCategory).filter_by(uuid=source_ec.uuid,
                                                                                   _source=source_ec._source,
                                                                                   valid=1).first()
                if target_ec:
                    target_ec.name = source_ec.name
                    target_ec.type = source_ec.type
                    target_ec.update_time = source_ec.update_time
            db.session.commit()

        # print("ec_uuid_dict_trans:", ec_uuid_dict_trans)

        # </editor-fold>

        # <editor-fold desc="sync_source of RelationCategory">
        # 定义模型类
        class SourceRelationCategory(Base):  # 自动加载表结构
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

        class TargetRelationCategory(Target_Base):  # 自动加载表结构
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
        relation_categories_in_source = dbsession.query(SourceRelationCategory).filter(
            SourceRelationCategory.valid == 1,
            or_(SourceRelationCategory.create_time > sync_time, SourceRelationCategory.update_time > sync_time)).all()
        # 更新ec_uuid_dict_trans
        new_ec_uuid_dict_trans = {}
        for key, value in ec_uuid_dict_trans.items():
            print(key, value)
            new_ec_uuid_dict_trans[str(key)] = str(ec_uuid_dict_trans.get(key))
        # print(new_ec_uuid_dict_trans)

        rc_uuid_dict_trans = {}
        # 根据name、source/targer_entity_category_ids判重，选择新增还是更新相同来源的数据
        for source_rc in relation_categories_in_source:
            # 更新source/target_entity_category_uuids
            for index, value in enumerate(source_rc.source_entity_category_uuids):
                source_rc.source_entity_category_uuids[index] = new_ec_uuid_dict_trans.get(value)
            for index, value in enumerate(source_rc.target_entity_category_uuids):
                source_rc.target_entity_category_uuids[index] = new_ec_uuid_dict_trans.get(value)

            input_source_ids_set = set(source_rc.source_entity_category_uuids)
            input_target_ids_set = set(source_rc.target_entity_category_uuids)

            # 查找相同关系名称的数据
            relation_same = target_dbsession.query(TargetRelationCategory).filter_by(
                relation_name=source_rc.relation_name, valid=1).all()
            if relation_same:
                for item in relation_same:
                    source_ids_db = set(item.source_entity_category_uuids)
                    target_ids_db = set(item.target_entity_category_uuids)

                    # 已存在--source新数据数据与库里已有数据相等或是库里数据的子集
                    if input_source_ids_set.issubset(
                            source_ids_db) and input_target_ids_set.issubset(target_ids_db):
                        # 来源相同，则更新数据
                        if item._source == source_rc._source:
                            item.source_entity_category_uuids = source_rc.source_entity_category_uuids
                            item.target_entity_category_uuids = source_rc.target_entity_category_uuids
                            rc_uuid_dict_trans[source_rc.uuid] = item.uuid
                            break
                        # 来源不同，保留主库
                        else:
                            rc_uuid_dict_trans[source_rc.uuid] = item.uuid
                            break

                    # update--源ids相等 and 目标ids不相等  update目标ids  取并集
                    elif (input_source_ids_set == source_ids_db) and input_target_ids_set != target_ids_db:
                        target_ids_result = list(input_target_ids_set.union(target_ids_db))
                        # 来源相同，则更新数据
                        if item._source == source_rc._source:
                            item.target_entity_category_uuids = target_ids_result
                            rc_uuid_dict_trans[source_rc.uuid] = item.uuid
                            break
                        # 来源不同，保留主库
                        else:
                            rc_uuid_dict_trans[source_rc.uuid] = item.uuid
                            break

                    # update--目标ids相等 and 源ids不相等  update源ids  取并集
                    elif (input_source_ids_set != source_ids_db) and input_target_ids_set == target_ids_db:
                        source_ids_result = list(input_source_ids_set.union(source_ids_db))
                        # 来源相同，则更新数据
                        if item._source == source_rc._source:
                            item.source_entity_category_uuids = source_ids_result
                            rc_uuid_dict_trans[source_rc.uuid] = item.uuid
                            break
                        # 来源不同，保留主库
                        else:
                            rc_uuid_dict_trans[source_rc.uuid] = item.uuid
                            break

                    # update--库里已有数据是输入数据的子集
                    elif source_ids_db.issubset(
                            input_source_ids_set) and target_ids_db.issubset(input_target_ids_set):
                        # 来源相同，则更新数据
                        if item._source == source_rc._source:
                            item.source_entity_category_uuids = source_rc.source_entity_category_uuids
                            item.target_entity_category_uuids = source_rc.target_entity_category_uuids
                            rc_uuid_dict_trans[source_rc.uuid] = item.uuid
                            break
                        # 来源不同，保留主库
                        else:
                            rc_uuid_dict_trans[source_rc.uuid] = item.uuid
                            break
                    # insert--相同关系名，但源、目标实体类型不同
                    else:
                        rc = TargetRelationCategory(uuid=source_rc.uuid,
                                                    source_entity_category_uuids=source_rc.source_entity_category_uuids,
                                                    target_entity_category_uuids=source_rc.target_entity_category_uuids,
                                                    relation_name=source_rc.relation_name,
                                                    _source=source_rc._source,
                                                    valid=1)
                        db.session.add(rc)
                        db.session.commit()
                        rc_uuid_dict_trans[source_rc.uuid] = source_rc.uuid
                        break
            else:
                rc = TargetRelationCategory(uuid=source_rc.uuid,
                                            source_entity_category_uuids=source_rc.source_entity_category_uuids,
                                            target_entity_category_uuids=source_rc.target_entity_category_uuids,
                                            relation_name=source_rc.relation_name,
                                            valid=1)
                db.session.add(rc)
                db.session.commit()
                rc_uuid_dict_trans[source_rc.uuid] = source_rc.uuid

        # target所有relation_name，构造外键dict-----如何构造dict,以什么为key..现在的方法会导致把以前同步rc当作外键的话，可能会找不到新的uuid
        # uuids_and_names_in_target_rc = RelationCategory.query.with_entities(RelationCategory.uuid,
        #                                                                     RelationCategory.relation_name).filter(
        #     RelationCategory.valid == 1).all()
        #
        # # 记录uuid变化----rc_uuid_dict_trans
        # target_dict_trans = {}
        # rc_uuid_dict_trans = {}
        #
        # for i in uuids_and_names_in_target_rc:
        #     if i[1] not in target_dict_trans.keys():
        #         target_dict_trans[i[1]] = i[0]  # {"onname": "onuuid"}
        #
        # # 遍历source所有数据，不做时间筛选，构造dict
        # uuids_and_names_in_source_rc_for_dict = dbsession.query(sourceRelationCategory).with_entities(
        #     sourceRelationCategory.uuid, sourceRelationCategory.relation_name).filter(
        #     sourceRelationCategory.valid == 1).all()
        #
        # for source_rc in uuids_and_names_in_source_rc_for_dict:
        #     # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
        #     rc_uuid_dict_trans[source_rc[0]] = target_dict_trans[
        #         source_rc[1]] if target_dict_trans.get(source_rc[1], "") else source_rc[0]
        # print("rc_uuid_dict_trans", rc_uuid_dict_trans)

        # </editor-fold>

        # <editor-fold desc="sync_source of Entity">
        # 定义模型类
        class SourceEntity(Base):  # 自动加载表结构
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

        class TargetEntity(Target_Base):  # 自动加载表结构
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
        entities_in_source = dbsession.query(SourceEntity).filter(SourceEntity.valid == 1,
                                                                  or_(SourceEntity.create_time > sync_time,
                                                                      SourceEntity.update_time > sync_time)).all()
        for i in entities_in_source:
            i.category_uuid = ec_uuid_dict_trans.get(i.category_uuid)
            print(i.category_uuid)

        # source所有name+category_uuid，唯一性（去重）判断
        names_and_cate_uuids_in_source = dbsession.query(SourceEntity).with_entities(SourceEntity.name,
                                                                                     SourceEntity.category_uuid,
                                                                                     SourceEntity.uuid).filter(
            SourceEntity.valid == 1,
            or_(SourceEntity.create_time > sync_time, SourceEntity.update_time > sync_time)).all()
        diff_sign_in_source = [i[0] + str(i[1]) for i in names_and_cate_uuids_in_source]

        # target所有name+category_uuid，唯一性（去重）判断
        names_and_cate_uuids_in_target = target_dbsession.query(TargetEntity).with_entities(TargetEntity.name,
                                                                                            TargetEntity.category_uuid,
                                                                                            TargetEntity.uuid).filter(
            TargetEntity.valid == 1,
            TargetEntity.category_uuid != None).all()
        diff_sign_in_target = [i[0] + str(i[1]) for i in names_and_cate_uuids_in_target]

        # 记录uuid变化----entity_uuid_dict_trans
        target_dict_trans_entity = {}
        entity_uuid_dict_trans = {}

        for i in names_and_cate_uuids_in_target:
            if i[0] + str(i[1]) not in target_dict_trans_entity.keys():
                target_dict_trans_entity[i[0] + str(i[1])] = i[2]  # {"onname+oncate_uuid": "onuuid"}
        # print("entity:", target_dict_trans)
        for source_entity in names_and_cate_uuids_in_source:
            # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
            entity_uuid_dict_trans[source_entity[2]] = target_dict_trans_entity[
                source_entity[0] + str(source_entity[1])] if target_dict_trans_entity.get(
                source_entity[0] + str(source_entity[1]),
                "") else source_entity[2]

        # source-target：计算是否有要插入的数据
        source_diff = list(set(diff_sign_in_source).difference(set(diff_sign_in_target)))
        source_name_diff = [i[0:-36] for i in source_diff]
        print(source_name_diff)
        source_cate_uuid_diff = [i[-36:] for i in source_diff]
        print(source_cate_uuid_diff)

        # source-target: 取交集，需要更新synonyms和props
        source_inter = list(set(diff_sign_in_source).intersection(set(diff_sign_in_target)))
        source_name_inter = [i[0:-36] for i in source_inter]
        source_cate_uuid_inter = [i[-36:] for i in source_inter]

        # 如果有要更新的数据----更新synonyms和props
        if source_inter:
            target_entities_update = target_dbsession.query(TargetEntity).filter(
                TargetEntity.name.in_(source_name_inter),
                TargetEntity.category_uuid.in_(source_cate_uuid_inter)).all()
            for target_entity in target_entities_update:
                source_entity = dbsession.query(SourceEntity).filter_by(name=target_entity.name,
                                                                        category_uuid=target_entity.category_uuid).first()
                target_entity.synonyms = list(set(target_entity.synonyms.append(source_entity.synonyms)))
                source_entity.props.update(target_entity.props)  # 相同属性保留target的值
                target_entity.props = source_entity.props
                target_entity.summary = target_entity.summary  # 不更新summary
                # target_entity.summary = target_entity.summary + ' ' + source_entity.summary + "——来自" + source_entity._source

            db.session.commit()

        # 如果有要插入的数据
        if source_diff:
            source_entities = dbsession.query(SourceEntity).filter(
                SourceEntity.name.in_(source_name_diff),
                SourceEntity.category_uuid.in_(source_cate_uuid_diff)).all()
            sync_entities = [TargetEntity(uuid=i.uuid, name=i.name, synonyms=i.synonyms, props=i.props,
                                          category_uuid=i.category_uuid, summary=i.summary, valid=i.valid,
                                          longitude=i.longitude, latitude=i.latitude, _source=i._source,
                                          create_time=i.create_time,
                                          update_time=i.update_time) for i in source_entities]
            db.session.add_all(sync_entities)
            db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_source of EventClass">
        # 定义模型类
        class SourceEventClass(Base):  # 自动加载表结构
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

        class TargetEventClass(Target_Base):  # 自动加载表结构
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

        # source所有name，唯一性（去重）判断
        uuids_and_names_in_source_evcl = dbsession.query(SourceEventClass).with_entities(SourceEventClass.uuid,
                                                                                         SourceEventClass.name).filter(
            SourceEventClass.valid == 1,
            or_(SourceEventClass.create_time > sync_time, SourceEventClass.update_time > sync_time)).all()
        uuids_in_source = [i[0] for i in uuids_and_names_in_source_evcl]
        names_in_source = [i[1] for i in uuids_and_names_in_source_evcl]

        # target所有name，唯一性（去重）判断
        uuids_and_names_in_target_evcl = target_dbsession.query(TargetEventClass).with_entities(TargetEventClass.uuid,
                                                                                                TargetEventClass.name).filter(
            TargetEventClass.valid == 1).all()
        uuids_in_target = [i[0] for i in uuids_and_names_in_target_evcl]
        names_in_target = [i[1] for i in uuids_and_names_in_target_evcl]

        # 记录uuid变化----event_class_uuid_dict_trans
        target_dict_trans = {}
        event_class_uuid_dict_trans = {}

        for i in uuids_and_names_in_target_evcl:
            if i[1] not in target_dict_trans.keys():
                target_dict_trans[i[1]] = i[0]  # {"onname": "onuuid"}

        # source所有name，构造dict
        uuids_and_names_in_source_evcl_for_dict = dbsession.query(SourceEventClass).with_entities(
            SourceEventClass.uuid,
            SourceEventClass.name).filter(SourceEventClass.valid == 1).all()

        for source_ec in uuids_and_names_in_source_evcl_for_dict:
            # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
            event_class_uuid_dict_trans[source_ec[0]] = target_dict_trans[
                source_ec[1]] if target_dict_trans.get(source_ec[1], "") else source_ec[0]

        # source-target：计算是否有要插入的数据
        source_names_to_insert = list(set(names_in_source).difference(set(names_in_target)))
        # source-target：计算是否有要更新的数据,以uuid为判重标准
        source_uuids_to_update = list(set(uuids_in_source).intersection(set(uuids_in_target)))

        # 如果有要插入的数据
        if source_names_to_insert:
            source_event_classes = dbsession.query(SourceEventClass).filter(
                SourceEventClass.name.in_(source_names_to_insert)).all()
            sync_event_classes = [TargetEventClass(uuid=i.uuid,
                                                   name=i.name,
                                                   valid=i.valid,
                                                   _source=i._source,
                                                   create_time=i.create_time,
                                                   update_time=i.update_time) for i in source_event_classes]
            db.session.add_all(sync_event_classes)
            db.session.commit()

        # 如果有要更新的数据,更新的数据是前几次同步时由该离线系统插入的数据，uuid未改变
        if source_uuids_to_update:
            source_event_classes = dbsession.query(SourceEventClass).filter(
                SourceEventClass.uuid.in_(source_uuids_to_update)).all()
            for source_evcl in source_event_classes:
                target_evcl = target_dbsession.query(TargetEventClass).filter_by(uuid=source_evcl.uuid,
                                                                                 _source=source_evcl._source,
                                                                                 valid=1).first()
                target_evcl.name = source_evcl.name
                target_evcl.update_time = source_evcl.update_time
            db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_source of EventCategory">
        # 定义模型类
        class SourceEventCategory(Base):  # 自动加载表结构
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

        class TargetEventCategory(Target_Base):  # 自动加载表结构
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
        event_categories_in_source = dbsession.query(SourceEventCategory).filter(SourceEventCategory.valid == 1, or_(
            SourceEventCategory.create_time > sync_time, SourceEventCategory.update_time > sync_time)).all()
        for i in event_categories_in_source:
            i.event_class_uuid = event_class_uuid_dict_trans.get(i.event_class_uuid)

        # source所有name, 唯一性（去重）判断
        names_and_class_uuids_in_source = dbsession.query(SourceEventCategory).with_entities(
            SourceEventCategory.name, SourceEventCategory.uuid).filter(SourceEventCategory.valid == 1, or_(
            SourceEventCategory.create_time > sync_time, SourceEventCategory.update_time > sync_time)).all()
        diff_sign_in_source = [i[0] for i in names_and_class_uuids_in_source]
        uuids_in_source = [i[1] for i in names_and_class_uuids_in_source]

        # target所有name, 唯一性（去重）判断
        names_and_class_uuids_in_target = target_dbsession.query(TargetEventCategory).with_entities(
            TargetEventCategory.name,
            TargetEventCategory.uuid).filter(
            TargetEventCategory.valid == 1).all()
        diff_sign_in_target = [i[0] for i in names_and_class_uuids_in_target]
        uuids_in_target = [i[1] for i in names_and_class_uuids_in_target]

        # 记录uuid变化----event_cate_uuid_dict_trans
        target_dict_trans = {}
        event_cate_uuid_dict_trans = {}

        for i in names_and_class_uuids_in_target:
            if i[0] not in target_dict_trans.keys():
                target_dict_trans[i[0]] = i[1]  # {"target_name": "onuuid"}

        # source所有name, 构造dict
        names_and_class_uuids_in_source_for_dict = dbsession.query(SourceEventCategory).with_entities(
            SourceEventCategory.name, SourceEventCategory.uuid).filter(SourceEventCategory.valid == 1).all()

        for source_event_category in names_and_class_uuids_in_source_for_dict:
            # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
            event_cate_uuid_dict_trans[source_event_category[1]] = target_dict_trans[
                source_event_category[0]] if target_dict_trans.get(
                source_event_category[0], "") else source_event_category[1]

        # source-target：计算是否有要插入的数据
        source_diff_to_insert = list(set(diff_sign_in_source).difference(set(diff_sign_in_target)))
        # source-target：计算是否有要更新的数据
        source_uuids_to_update = list(set(uuids_in_source).intersection(set(uuids_in_target)))

        # 如果有要插入的数据
        if source_diff_to_insert:
            source_event_categories = dbsession.query(SourceEventCategory).filter(
                SourceEventCategory.name.in_(source_diff_to_insert)).all()
            sync_event_categories = [TargetEventCategory(uuid=i.uuid, name=i.name,
                                                         event_class_uuid=i.event_class_uuid, valid=i.valid,
                                                         _source=i._source, create_time=i.create_time,
                                                         update_time=i.update_time) for i in source_event_categories]
            db.session.add_all(sync_event_categories)
            db.session.commit()

        # 如果有要更新的数据
        if source_uuids_to_update:
            source_event_categories = dbsession.query(SourceEventCategory).filter(
                SourceEventCategory.uuid.in_(source_uuids_to_update)).all()
            for source_event_cate in source_event_categories:
                target_event_cate = target_dbsession.query(TargetEventCategory).filter_by(uuid=source_event_cate.uuid,
                                                                                          _source=source_event_cate._source,
                                                                                          valid=1).first()
                if target_event_cate:
                    target_event_cate.name = source_event_cate.name
                    target_event_cate.event_class_uuid = source_event_cate.event_class_uuid
                    target_event_cate.update_time = source_event_cate.update_time
            db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_source of DocMarkComment">
        # 定义模型类
        class SourceDocMarkComment(Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkComment %r>' % self.uuid

        class TargetDocMarkComment(Target_Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkComment %r>' % self.uuid

        doc_mark_comment_in_source = dbsession.query(SourceDocMarkComment).filter(SourceDocMarkComment.valid == 1,
                                                                                  or_(
                                                                                      SourceDocMarkComment.create_time > sync_time,
                                                                                      SourceDocMarkComment.update_time > sync_time)).all()
        doc_mark_comment_uuids_in_source = [i.uuid for i in doc_mark_comment_in_source]
        doc_mark_comment_uuids_in_target = target_dbsession.query(TargetDocMarkComment).with_entities(
            TargetDocMarkComment.uuid).filter_by(
            valid=1).all()

        # 更新create_by_uuid、update_by_uuid
        for i in doc_mark_comment_in_source:
            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)

        # source-target：计算是否有要插入的数据
        source_dmm_to_insert = list(
            set(doc_mark_comment_uuids_in_source).difference(set(doc_mark_comment_uuids_in_target)))
        # source-target：计算是否有要更新的数据
        source_dmm_to_update = list(
            set(doc_mark_comment_uuids_in_source).intersection(set(doc_mark_comment_uuids_in_target)))

        # 同步source_doc_mark_comment
        if source_dmm_to_insert:
            source_dmm_to_insert = dbsession.query(SourceDocMarkComment).filter(
                SourceDocMarkComment.uuid.in_(source_dmm_to_insert)).all()
            sync_doc_mark_comments = [
                TargetDocMarkComment(uuid=i.uuid, doc_uuid=i.doc_uuid, name=i.name, position=i.position,
                                     comment=i.comment, create_by_uuid=i.create_by_uuid,
                                     create_time=i.create_time,
                                     update_by_uuid=i.update_by_uuid, update_time=i.update_time,
                                     _source=i._source,
                                     valid=i.valid) for i in source_dmm_to_insert]
            db.session.add_all(sync_doc_mark_comments)
            db.session.commit()
        if source_dmm_to_update:
            for dmm_uuid_source in source_dmm_to_update:
                dmm_target = target_dbsession.query(TargetDocMarkComment).filter_by(uuid=dmm_uuid_source,
                                                                                    valid=1).first()
                dmm_source = dbsession.query(SourceDocMarkComment).filter_by(uuid=dmm_uuid_source, valid=1).first()
                dmm_target.doc_uuid = dmm_source.doc_uuid
                dmm_target.name = dmm_source.name
                dmm_target.position = dmm_source.position
                dmm_target.comment = dmm_source.comment
                dmm_target.create_by_uuid = dmm_source.create_by_uuid
                dmm_target.create_time = dmm_source.create_time
                dmm_target.update_by_uuid = dmm_source.update_by_uuid
                dmm_target.update_time = dmm_source.update_time
                dmm_target.valid = dmm_source.valid
                dmm_target._source = dmm_source._source
            db.session.commit()

        # print("doc_mark_comment success")

        # </editor-fold>

        # <editor-fold desc="sync_source of DocMarkEntity">
        # 定义模型类
        class SourceDocMarkEntity(Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkEntity %r>' % self.uuid

        class TargetDocMarkEntity(Target_Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkEntity %r>' % self.uuid

        doc_mark_entity_in_source = dbsession.query(SourceDocMarkEntity).filter(
            SourceDocMarkEntity.valid == 1,
            or_(
                SourceDocMarkEntity.create_time > sync_time,
                SourceDocMarkEntity.update_time > sync_time)).all()

        # 将doc_mark_entity的entity_uuid更新到dict里
        entity_uuid_in_dme = dbsession.query(SourceDocMarkEntity).with_entities(
            SourceDocMarkEntity.entity_uuid).filter_by(valid=1).distinct().all()
        for entity_uuid in entity_uuid_in_dme:
            if entity_uuid not in entity_uuid_dict_trans.keys():
                entity_sign_in_source = dbsession.query(SourceEntity).with_entities(SourceEntity.name,
                                                                                    SourceEntity.category_uuid,
                                                                                    SourceEntity.uuid).filter_by(
                    valid=1, uuid=entity_uuid).first()
                entity_sign_in_source = entity_sign_in_source[0] + str(
                    ec_uuid_dict_trans.get(entity_sign_in_source[1]))
                entity_uuid_dict_trans[entity_uuid] = target_dict_trans_entity.get(entity_sign_in_source)

        # 更新create_by_uuid、update_by_uuid、entity_uuid
        for i in doc_mark_entity_in_source:
            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)
            i.entity_uuid = entity_uuid_dict_trans.get(i.entity_uuid)
        # 同步source_doc_mark_entity
        sync_doc_mark_entities = [
            TargetDocMarkEntity(uuid=i.uuid, doc_uuid=i.doc_uuid, word=i.word, entity_uuid=i.entity_uuid,
                                source=i.source,
                                create_by_uuid=i.create_by_uuid, create_time=i.create_time,
                                update_by_uuid=i.update_by_uuid, update_time=i.update_time,
                                appear_index_in_text=i.appear_index_in_text, _source=i._source, valid=i.valid) for i in
            doc_mark_entity_in_source]
        db.session.add_all(sync_doc_mark_entities)
        db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_source of DocMarkPlace">
        # 定义模型类
        class SourceDocMarkPlace(Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkPlace %r>' % self.uuid

        class TargetDocMarkPlace(Target_Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkPlace %r>' % self.uuid

        doc_mark_place_in_source = dbsession.query(SourceDocMarkPlace).filter(
            SourceDocMarkPlace.valid == 1,
            or_(
                SourceDocMarkPlace.create_time > sync_time,
                SourceDocMarkPlace.update_time > sync_time)).all()

        # 将doc_mark_place的place_uuid更新到dict里
        place_uuid_in_dmp = dbsession.query(SourceDocMarkPlace).with_entities(
            SourceDocMarkPlace.place_uuid).filter_by(valid=1).distinct().all()
        for place_uuid in place_uuid_in_dmp:
            if place_uuid not in entity_uuid_dict_trans.keys():
                entity_sign_in_source = dbsession.query(SourceEntity).with_entities(SourceEntity.name,
                                                                                    SourceEntity.category_uuid,
                                                                                    SourceEntity.uuid).filter_by(
                    valid=1, uuid=place_uuid).first()
                entity_sign_in_source = entity_sign_in_source[0] + str(ec_uuid_dict_trans.get(entity_sign_in_source[1]))
                entity_uuid_dict_trans[place_uuid] = target_dict_trans_entity.get(entity_sign_in_source)

        # 更新create_by_uuid、update_by_uuid、place_uuid
        for i in doc_mark_place_in_source:
            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)
            i.place_uuid = entity_uuid_dict_trans.get(i.place_uuid)
        # 同步source_doc_mark_place
        sync_doc_mark_places = [
            TargetDocMarkPlace(uuid=i.uuid, doc_uuid=i.doc_uuid, word=i.word, type=i.type, place_uuid=i.place_uuid,
                               direction=i.direction, place_lon=i.place_lon, place_lat=i.place_lat, height=i.height,
                               unit=i.unit, dms=i.dms, distance=i.distance, relation=i.relation,
                               create_by_uuid=i.create_by_uuid, create_time=i.create_time,
                               update_by_uuid=i.update_by_uuid,
                               update_time=i.update_time, entity_or_sys=i.entity_or_sys,
                               appear_index_in_text=i.appear_index_in_text, _source=i._source, valid=i.valid) for i in
            doc_mark_place_in_source]
        db.session.add_all(sync_doc_mark_places)
        db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_source of DocMarkRelationProperty">
        # 定义模型类
        class SourceDocMarkRelationProperty(Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkRelationProperty %r>' % self.uuid

        class TargetDocMarkRelationProperty(Target_Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkRelationProperty %r>' % self.uuid

        doc_mark_relation_property_in_source = dbsession.query(SourceDocMarkRelationProperty).filter(
            SourceDocMarkRelationProperty.valid == 1, or_(SourceDocMarkRelationProperty.create_time > sync_time,
                                                          SourceDocMarkRelationProperty.update_time > sync_time)).all()
        # 更新relation_uuid、create_by_uuid、update_by_uuid
        for i in doc_mark_relation_property_in_source:
            if rc_uuid_dict_trans.get(i.relation_uuid):  # 新插入的doc_rc的外键relation_uuid在本次同步数据内
                i.relation_uuid = rc_uuid_dict_trans.get(i.relation_uuid)
            else:
                source_rc_old = dbsession.query(SourceRelationCategory).filter_by(uuid=i.relation_uuid,
                                                                                  valid=1).first()
                for index, value in enumerate(source_rc_old.source_entity_category_uuids):
                    source_rc_old.source_entity_category_uuids[index] = new_ec_uuid_dict_trans.get(value)
                for index, value in enumerate(source_rc_old.target_entity_category_uuids):
                    source_rc_old.target_entity_category_uuids[index] = new_ec_uuid_dict_trans.get(value)
                rc_target = target_dbsession.query(TargetRelationCategory).filter(
                    TargetRelationCategory.relation_name == source_rc_old.relation_name,
                    TargetRelationCategory.source_entity_category_uuids.op('@>')(
                        source_rc_old.source_entity_category_uuids),
                    TargetRelationCategory.target_entity_category_uuids.op('@>')(
                        source_rc_old.target_entity_category_uuids),
                    TargetRelationCategory.valid == 1).first()
                i.relation_uuid = rc_target.uuid

            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)

        # 同步source_doc_mark_relation_property
        sync_doc_mark_relation_property = [
            TargetDocMarkRelationProperty(uuid=i.uuid, doc_uuid=i.doc_uuid, nid=i.nid, relation_uuid=i.relation_uuid,
                                          relation_name=i.relation_name, start_time=i.start_time,
                                          start_type=i.start_type,
                                          end_time=i.end_time, end_type=i.end_type,
                                          source_entity_uuid=i.source_entity_uuid,
                                          target_entity_uuid=i.target_entity_uuid, create_by_uuid=i.create_by_uuid,
                                          create_time=i.create_time, update_by_uuid=i.update_by_uuid,
                                          update_time=i.update_time, _source=i._source,
                                          valid=i.valid) for i in doc_mark_relation_property_in_source]
        db.session.add_all(sync_doc_mark_relation_property)
        db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_source of DocMarkTimeTag">
        # 定义模型类
        class SourceDocMarkTimeTag(Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkTimeTag %r>' % self.uuid

        class TargetDocMarkTimeTag(Target_Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkTimeTag %r>' % self.uuid

        doc_mark_time_tag_in_source = dbsession.query(SourceDocMarkTimeTag).filter(SourceDocMarkTimeTag.valid == 1,
                                                                                   or_(
                                                                                       SourceDocMarkTimeTag.create_time > sync_time,
                                                                                       SourceDocMarkTimeTag.update_time > sync_time)).all()
        # 更新create_by_uuid、update_by_uuid
        for i in doc_mark_time_tag_in_source:
            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)
        # 同步doc_mark_time_tag_in_source
        sync_doc_mark_time_tags = [
            TargetDocMarkTimeTag(uuid=i.uuid, doc_uuid=i.doc_uuid, word=i.word, format_date=i.format_date,
                                 format_date_end=i.format_date_end, mark_position=i.mark_position,
                                 time_type=i.time_type, reserve_fields=i.reserve_fields,
                                 arab_time=i.arab_time, create_by_uuid=i.create_by_uuid,
                                 create_time=i.create_time, update_by_uuid=i.update_by_uuid,
                                 update_time=i.update_time, appear_index_in_text=i.appear_index_in_text,
                                 _source=i._source, valid=i.valid) for i in doc_mark_time_tag_in_source]
        db.session.add_all(sync_doc_mark_time_tags)
        db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_source of DocMarkMind">
        # 定义模型类
        class SourceDocMarkMind(Base):  # 自动加载表结构
            __tablename__ = 'doc_mark_mind'
            uuid = db.Column(db.String, primary_key=True)
            name = db.Column(db.Text)
            parent_uuid = db.Column(db.String)
            doc_uuid = db.Column(db.String)
            valid = db.Column(db.Integer)
            _source = db.Column(db.String)
            create_time = db.Column(db.TIMESTAMP)
            update_time = db.Column(db.TIMESTAMP)

            def __repr__(self):
                return '<DocMarkMind %r>' % self.uuid

        class TargetDocMarkMind(Target_Base):  # 自动加载表结构
            __tablename__ = 'doc_mark_mind'
            uuid = db.Column(db.String, primary_key=True)
            name = db.Column(db.Text)
            parent_uuid = db.Column(db.String)
            doc_uuid = db.Column(db.String)
            valid = db.Column(db.Integer)
            _source = db.Column(db.String)
            create_time = db.Column(db.TIMESTAMP)
            update_time = db.Column(db.TIMESTAMP)

            def __repr__(self):
                return '<DocMarkMind %r>' % self.uuid

        doc_mark_mind_in_source = dbsession.query(SourceDocMarkMind).filter(SourceDocMarkMind.valid == 1,
                                                                            or_(
                                                                                SourceDocMarkMind.create_time > sync_time,
                                                                                SourceDocMarkMind.update_time > sync_time)).all()
        # 同步doc_mark_mind_in_source
        sync_doc_mark_minds = [
            TargetDocMarkMind(uuid=i.uuid, name=i.name, parent_uuid=i.parent_uuid, doc_uuid=i.doc_uuid,
                              create_time=i.create_time, update_time=i.update_time, _source=i._source,
                              valid=i.valid) for i in doc_mark_mind_in_source]
        db.session.add_all(sync_doc_mark_minds)
        db.session.commit()

        # print("doc_mark_mind success")
        # </editor-fold>

        # <editor-fold desc="sync_source of DocMarkAdvise">
        # 定义模型类
        class SourceDocMarkAdvise(Base):  # 自动加载表结构
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

        class TargetDocMarkAdvise(Target_Base):  # 自动加载表结构
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

        doc_mark_advise_in_source = dbsession.query(SourceDocMarkAdvise).filter(SourceDocMarkAdvise.valid == 1,
                                                                                or_(
                                                                                    SourceDocMarkAdvise.create_time > sync_time,
                                                                                    SourceDocMarkAdvise.update_time > sync_time)).all()
        uuids_in_source = [i.uuid for i in doc_mark_advise_in_source]
        uuids_in_target = target_dbsession.query(TargetDocMarkAdvise).with_entities(TargetDocMarkAdvise.uuid).filter_by(
            valid=1).all()
        uuids_in_target = [i[0] for i in uuids_in_target]
        # 更新create_by_uuid、update_by_uuid
        for i in doc_mark_advise_in_source:
            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid) if i.create_by_uuid else None
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid) if i.update_by_uuid else None

        # source-target：计算是否有要插入的数据
        doc_mark_advise_to_insert = list(set(uuids_in_source).difference(set(uuids_in_target)))
        # source-target：计算是否有要更新的数据
        doc_mark_advise_to_update = list(set(uuids_in_source).intersection(set(uuids_in_target)))

        # 同步doc_mark_advise_in_source
        if doc_mark_advise_to_insert:
            doc_mark_advise_to_insert = dbsession.query(SourceDocMarkAdvise).filter(
                SourceDocMarkAdvise.uuid.in_(doc_mark_advise_to_insert)).all()
            sync_doc_mark_advises = [
                TargetDocMarkAdvise(uuid=i.uuid, doc_uuid=i.doc_uuid, mark_uuid=i.mark_uuid, type=i.type,
                                    content=i.content,
                                    create_by_uuid=i.create_by_uuid, create_time=i.create_time,
                                    update_by_uuid=i.update_by_uuid,
                                    update_time=i.update_time, _source=i._source, valid=i.valid) for i in
                doc_mark_advise_to_insert]
            db.session.add_all(sync_doc_mark_advises)
            db.session.commit()

        if doc_mark_advise_to_update:
            for dma_uuid_source in doc_mark_advise_to_update:
                doc_mark_advise = TargetDocMarkAdvise.query.filter_by(uuid=dma_uuid_source, valid=1).first()
                dma_source = dbsession.query(SourceDocMarkAdvise).filter_by(uuid=dma_uuid_source, valid=1).first()
                doc_mark_advise.doc_uuid = dma_source.doc_uuid
                doc_mark_advise.mark_uuid = dma_source.mark_uuid
                doc_mark_advise.type = dma_source.type
                doc_mark_advise.content = dma_source.content
                doc_mark_advise.create_by_uuid = dma_source.create_by_uuid
                doc_mark_advise.create_time = dma_source.create_time
                doc_mark_advise.update_by_uuid = dma_source.update_by_uuid
                doc_mark_advise.update_time = dma_source.update_time
                doc_mark_advise.valid = dma_source.valid
                doc_mark_advise._source = dma_source._source
            db.session.commit()

        # print("doc_mark_advise success")
        # </editor-fold>

        # <editor-fold desc="sync_source of DocumentRecords">
        # 定义模型类
        class SourceDocumentRecords(Base):  # 自动加载表结构
            __tablename__ = 'document_records'
            uuid = db.Column(db.String, primary_key=True)
            doc_uuid = db.Column(db.String)
            create_by_uuid = db.Column(db.String)
            create_time = db.Column(db.TIMESTAMP)
            operate_type = db.Column(db.Integer)
            _source = db.Column(db.String)

            def __repr__(self):
                return '<DocumentRecords %r>' % self.uuid

        class TargetDocumentRecords(Target_Base):  # 自动加载表结构
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
        document_records_in_source = dbsession.query(SourceDocumentRecords).filter(
            SourceDocumentRecords.create_time > sync_time).all()
        # 更新create_by_uuid
        for i in document_records_in_source:
            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)

        # 同步document_records_in_source
        sync_document_records = [
            TargetDocumentRecords(uuid=i.uuid, doc_uuid=i.doc_uuid, create_by_uuid=i.create_by_uuid,
                                  create_time=i.create_time, operate_type=i.operate_type,
                                  _source=i._source) for i in document_records_in_source]
        db.session.add_all(sync_document_records)
        db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_source of DocMarkEvent">
        # 定义模型类
        class SourceDocMarkEvent(Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkEvent %r>' % self.uuid

        class TargetDocMarkEvent(Target_Base):  # 自动加载表结构
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

            def __repr__(self):
                return '<DocMarkEvent %r>' % self.uuid

        doc_mark_event_in_source = dbsession.query(SourceDocMarkEvent).filter(SourceDocMarkEvent.valid == 1,
                                                                              or_(
                                                                                  SourceDocMarkEvent.create_time > sync_time,
                                                                                  SourceDocMarkEvent.update_time > sync_time)).all()

        # 更新customer_uuid、event_class_uuid、event_type_uuid、create_by_uuid、update_by_uuid
        for i in doc_mark_event_in_source:
            i.customer_uuid = customer_uuid_dict_trans.get(i.customer_uuid)
            i.event_class_uuid = event_class_uuid_dict_trans.get(i.event_class_uuid)
            i.event_type_uuid = event_cate_uuid_dict_trans.get(i.event_type_uuid)
            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid) if i.create_by_uuid else None
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid) if i.update_by_uuid else None

        # 同步doc_mark_events_in_source
        sync_doc_mark_events = [
            TargetDocMarkEvent(uuid=i.uuid, event_id=i.event_id, event_desc=i.event_desc, event_subject=i.event_subject,
                               event_predicate=i.event_predicate, event_object=i.event_object, event_time=i.event_time,
                               event_address=i.event_address, event_why=i.event_why, event_result=i.event_result,
                               event_conduct=i.event_conduct, event_talk=i.event_talk, event_how=i.event_how,
                               doc_uuid=i.doc_uuid, customer_uuid=i.customer_uuid, parent_uuid=i.parent_uuid,
                               title=i.title, event_class_uuid=i.event_class_uuid, event_type_uuid=i.event_type_uuid,
                               create_by_uuid=i.create_by_uuid, create_time=i.create_time,
                               update_by_uuid=i.update_by_uuid,
                               update_time=i.update_time, add_time=i.add_time, _source=i._source,
                               valid=i.valid) for i in doc_mark_event_in_source]
        db.session.add_all(sync_doc_mark_events)
        db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_source of Catalog">
        # 定义文档目录类
        class SourceCatalog(Base):  # 自动加载表结构
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

        class TargetCatalog(Target_Base):  # 自动加载表结构
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

        target_catalog_uuids = []
        source_catalog_uuids = []
        target_catalog_path = []
        source_catalog_path = []
        source_catalog_path_dict = {}
        target_catalog_path_dict = {}
        source_target_catalog_dict = {}
        sync_catalog_uuid_list = []
        # 存储根目录
        catalogs = target_dbsession.query(TargetCatalog).filter_by(parent_uuid=None).all()
        for catalog in catalogs:
            target_catalog_uuids.append(catalog.uuid)
            target_catalog_path.append([catalog.name, 1])
            if 1 not in target_catalog_path_dict.keys():
                target_catalog_path_dict[1] = [catalog.name]
            else:
                target_catalog_path_dict[1].append(catalog.name)
        source_catalogs = dbsession.query(SourceCatalog).filter_by(parent_uuid=None).all()
        for source_catelog in source_catalogs:
            source_catalog_uuids.append(source_catelog.uuid)
            source_catalog_path.append([source_catelog.name, 1])
            if 1 not in source_catalog_path_dict.keys():
                source_catalog_path_dict[1] = [source_catelog.name]
            else:
                source_catalog_path_dict[1].append(source_catelog.name)

        # 存储路径
        def get_catalog_target_path(uuid):
            catalog = target_dbsession.query(TargetCatalog).filter_by(uuid=uuid).first()
            res = [catalog.name]
            while catalog.parent_uuid:
                catalog = target_dbsession.query(TargetCatalog).filter_by(uuid=catalog.parent_uuid).first()
                res.append(catalog.name)
            res.reverse()
            path = "/".join(res)
            catalog_level = path.count("/") + 1
            if catalog_level not in target_catalog_path_dict.keys():
                target_catalog_path_dict[catalog_level] = [path]
            else:
                target_catalog_path_dict[catalog_level].append(path)
            return [path, catalog_level]

        def get_catalog_source_path(uuid):
            catalog = dbsession.query(SourceCatalog).filter_by(uuid=uuid).first()
            res = [catalog.name]
            while catalog.parent_uuid:
                catalog = dbsession.query(SourceCatalog).filter_by(uuid=catalog.parent_uuid).first()
                res.append(catalog.name)
            res.reverse()
            path = "/".join(res)
            catalog_level = path.count("/") + 1
            if catalog_level not in source_catalog_path_dict.keys():
                source_catalog_path_dict[catalog_level] = [path]
            else:
                source_catalog_path_dict[catalog_level].append(path)
            return [path, catalog_level]

        # 层级遍历所有目录
        for uuid in target_catalog_uuids:
            tmp_catalogs = dbsession.query(SourceCatalog).filter_by(parent_uuid=uuid).all()
            for tmp_catalog in tmp_catalogs:
                target_catalog_uuids.append(tmp_catalog.uuid)
                target_catalog_path.append(get_catalog_target_path(tmp_catalog.uuid))
        for uuid in source_catalog_uuids:
            tmp_catalogs = dbsession.query(SourceCatalog).filter_by(parent_uuid=uuid).all()
            for tmp_catalog in tmp_catalogs:
                source_catalog_uuids.append(tmp_catalog.uuid)
                source_catalog_path.append(get_catalog_source_path(tmp_catalog.uuid))
        # 改变离线版目录的父节点和填充source_target_catalog_dict字典
        for source_item in source_catalog_path:
            source_index = source_catalog_path.index(source_item)
            tmp_source_catalog = dbsession.query(SourceCatalog).filter_by(
                uuid=source_catalog_uuids[source_index]).first()
            if source_item[1] in target_catalog_path_dict.keys() and source_item[0] in target_catalog_path_dict[
                source_item[1]]:  # 同级,同名
                target_index = target_catalog_path.index(source_item)
                source_target_catalog_dict[source_catalog_uuids[source_index]] = target_catalog_uuids[
                    target_index]  # 存进字典
                tmp_target_catalog = target_dbsession.query(TargetCatalog).filter_by(
                    uuid=target_catalog_uuids[target_index]).first()
                tmp_source_catalog.parent_uuid = tmp_target_catalog.parent_uuid  # 改目录的父节点
            else:
                sync_catalog_uuid_list.append(tmp_source_catalog.uuid)
                source_target_catalog_dict[tmp_source_catalog.uuid] = tmp_source_catalog.uuid  # 存进字典，uuid不变
                tmp_source_catalog.parent_uuid = source_target_catalog_dict.get(tmp_source_catalog.parent_uuid)
        # 如果有要插入的数据
        if sync_catalog_uuid_list:
            source_catalog = dbsession.query(SourceCatalog).filter(
                SourceCatalog.uuid.in_(sync_catalog_uuid_list)).all()
            sync_catalog = [TargetCatalog(uuid=source_target_catalog_dict.get(i.uuid),
                                          name=i.name,
                                          tagging_tabs=i.tagging_tabs,
                                          parent_uuid=i.parent_uuid,
                                          create_by_uuid=customer_uuid_dict_trans.get(i.create_by_uuid),
                                          update_by_uuid=customer_uuid_dict_trans.get(i.update_by_uuid),
                                          sort=i.sort,
                                          _source=i._source,
                                          create_time=i.create_time,
                                          update_time=i.update_time) for i in source_catalog]
            db.session.add_all(sync_catalog)
            db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_source of Document">
        # 定义文档类
        class SourceDocument(Base):
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

        class TargetDocument(Target_Base):
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

        source_document = dbsession.query(SourceDocument).filter(SourceDocument.valid == 1, or_(
            SourceDocument.create_time > sync_time,
            SourceDocument.update_time > sync_time)).all()
        print(sync_time)
        sync_document = [TargetDocument(uuid=i.uuid,
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
                                        catalog_uuid=source_target_catalog_dict.get(i.catalog_uuid),
                                        html_path=i.html_path,
                                        valid=1,
                                        update_time=i.update_time) for i in source_document]
        db.session.add_all(sync_document)
        db.session.commit()
        # </editor-fold>
        res = success_res()

    except Exception as e:
        print(str(e))
        if dbsession:
            dbsession.close()
        res = fail_res()

    return jsonify(res)
