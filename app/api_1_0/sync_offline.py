# -*- coding: UTF-8 -*-
import os
import time
from flask import jsonify, request
from sqlalchemy.dialects.postgresql import JSONB

from . import api_sync_offline as blue_print
from ..models import Customer, db, EntityCategory, RelationCategory, SyncRecords, Entity, EventClass, EventCategory, \
    DocMarkComment, DocMarkEntity, DocMarkPlace, DocMarkRelationProperty, DocMarkTimeTag, DocMarkMind, DocMarkAdvise, \
    DocumentRecords, DocMarkEvent,Catalog, Document
from .utils import success_res, fail_res
from sqlalchemy import create_engine, MetaData, Table, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from ..conf import PG_USER_NAME,PG_USER_PASSWORD,PG_DB_SERVER_IP,PG_DB_PORT,PG_DB_NAME


@blue_print.route('/show_target_database_information', methods=['GET'])
def show_target_database_information():
    data = {"online_pg_db_server_ip":PG_DB_SERVER_IP,"online_pg_db_port":PG_DB_PORT,"online_pg_user_name":PG_USER_NAME,
            "online_pg_user_password":PG_USER_PASSWORD,"online_pg_db_name":PG_DB_NAME}
    return data


@blue_print.route('/conn_pg', methods=['GET'])
def conn_pgs():
    conn = request.args
    PG_IP = conn.get('offline_pg_db_server_ip')
    PG_PORT = conn.get('offline_pg_db_port')
    PG_USER_NAME = conn.get('offline_pg_user_name')
    PG_PWD = conn.get('offline_pg_user_password')
    PG_DB_NAME = conn.get('offline_pg_db_name')
    if not all([PG_IP, PG_PORT, PG_USER_NAME, PG_PWD,PG_DB_NAME]):
        return jsonify(fail_res())
    try:
        offline_postgres = 'postgresql://%s:%s@%s:%s/%s' % (
            PG_USER_NAME, PG_PWD, PG_IP,
            PG_PORT,
            PG_DB_NAME)
        engine = create_engine(offline_postgres)
        available_tables = engine.execute('SELECT datname FROM pg_database').fetchall()
        database_name = []
        for dataname in available_tables:
            database_name.append(dataname[0])
        def is_template(str):
            return not str.startswith('template')
        database_names = list(filter(is_template,database_name))
        res = success_res(msg="连接成功")
    except:
        res = fail_res(msg="连接失败")
    return jsonify(res)


@blue_print.route('/sync_offline', methods=['POST'])
def sync_offline():
    try:
        OFFLINE_PG_USER_NAME = request.json.get('offline_pg_user_name', 'postgres')
        OFFLINE_PG_USER_PASSWORD = request.json.get('offline_pg_user_password', 'postgres')
        OFFLINE_PG_DB_SERVER_IP = request.json.get('offline_pg_db_server_ip', '192.168.2.159')
        OFFLINE_PG_DB_PORT = request.json.get('offline_pg_db_port', '5432')
        OFFLINE_PG_DB_NAME = request.json.get('offline_pg_db_name','offline_tagging_system_for_sync')

        # 建立动态数据库的链接
        offline_postgres = 'postgresql://%s:%s@%s:%s/%s' % (
            OFFLINE_PG_USER_NAME, OFFLINE_PG_USER_PASSWORD, OFFLINE_PG_DB_SERVER_IP,
            OFFLINE_PG_DB_PORT,
            OFFLINE_PG_DB_NAME)
        engine = create_engine(offline_postgres)
        # 定义模型类继承父类及数据连接会话
        DBsession = sessionmaker(bind=engine)  # 类似于游标
        dbsession = scoped_session(DBsession)
        Base = declarative_base()  # 定义一个给其他类继承的父类

        # md = MetaData(bind=engine)  # 元数据: 主要是指数据库表结构、关联等信息

        # 获取上次同步时间
        sync_record = SyncRecords.query.filter_by(system_name=OFFLINE_PG_DB_SERVER_IP).first()
        sync_time = sync_record.sync_time

        # 更新同步时间
        sync_record.sync_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        db.session.commit()

        # <editor-fold desc="sync_offline of Customer">
        # 定义模型类
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
        uuids_and_troop_in_online = Customer.query.with_entities(Customer.uuid, Customer.troop_number).filter(
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

        # for offline_customer in uuids_and_troop_in_offline:
        #     # offtroop存在, {"offuuid": "onuuid"}, offtroop不存在, {"offuuid": "offuuid"}
        #     customer_uuid_dict_trans[offline_customer[0]] = online_dict_trans[
        #         offline_customer[1]] if online_dict_trans.get(offline_customer[1], "") else offline_customer[0]

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
            db.session.add_all(sync_customers)
            db.session.commit()

            # 如果有要更新的数据  即_source相同，off_uuid=on_uuid
            if offline_troop_numbers_to_update:
                offline_customers = dbsession.query(OfflineCustomer).filter(
                    OfflineCustomer.troop_number.in_(offline_troop_numbers_to_update)).all()
                for offline_customer in offline_customers:
                    online_customer = Customer.query.filter_by(uuid=offline_customer.uuid,
                                                               _source=offline_customer._source, valid=1).first()
                    if online_customer:
                        online_customer.username = offline_customer.username
                        online_customer.pwd = offline_customer.pwd
                        online_customer.power_score = offline_customer.power_score
                        online_customer.update_time = offline_customer.update_time
            db.session.commit()
        # print("customer_uuid_dict_trans:", customer_uuid_dict_trans)
        # </editor-fold>

        # <editor-fold desc="sync_offline of EntityCategory">
        # # 定义模型类
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
        uuids_and_names_in_online_ec = EntityCategory.query.with_entities(EntityCategory.uuid,
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
            db.session.add_all(sync_entity_categories)
            db.session.commit()

        # 如果有要更新的数据
        if offline_uuids_to_update:
            offline_entity_cateogories = dbsession.query(OfflineEntityCategory).filter(
                OfflineEntityCategory.uuid.in_(offline_uuids_to_update)).all()
            for offline_ec in offline_entity_cateogories:
                online_ec = EntityCategory.query.filter_by(uuid=offline_ec.uuid, _source=offline_ec._source, valid=1).first()
                if online_ec:
                    online_ec.name = offline_ec.name
                    online_ec.type = offline_ec.type
                    online_ec.update_time = offline_ec.update_time
            db.session.commit()
        # print("ec_uuid_dict_trans:", ec_uuid_dict_trans)

        # </editor-fold>

        # <editor-fold desc="sync_offline of RelationCategory">
        # 定义模型类
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
            relation_same = RelationCategory.query.filter_by(relation_name=offline_rc.relation_name, valid=1).all()
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
                        db.session.add(rc)
                        db.session.commit()
                        rc_uuid_dict_trans[offline_rc.uuid] = offline_rc.uuid
                        break
            else:
                rc = RelationCategory(uuid=offline_rc.uuid, source_entity_category_uuids=offline_rc.source_entity_category_uuids,
                                      target_entity_category_uuids=offline_rc.target_entity_category_uuids, relation_name=offline_rc.relation_name,
                                      valid=1)
                db.session.add(rc)
                db.session.commit()
                rc_uuid_dict_trans[offline_rc.uuid] = offline_rc.uuid

        # online所有relation_name，构造外键dict-----如何构造dict,以什么为key..现在的方法会导致把以前同步rc当作外键的话，可能会找不到新的uuid
        # uuids_and_names_in_online_rc = RelationCategory.query.with_entities(RelationCategory.uuid,
        #                                                                     RelationCategory.relation_name).filter(
        #     RelationCategory.valid == 1).all()
        #
        # # 记录uuid变化----rc_uuid_dict_trans
        # online_dict_trans = {}
        # rc_uuid_dict_trans = {}
        #
        # for i in uuids_and_names_in_online_rc:
        #     if i[1] not in online_dict_trans.keys():
        #         online_dict_trans[i[1]] = i[0]  # {"onname": "onuuid"}
        #
        # # 遍历offline所有数据，不做时间筛选，构造dict
        # uuids_and_names_in_offline_rc_for_dict = dbsession.query(OfflineRelationCategory).with_entities(
        #     OfflineRelationCategory.uuid, OfflineRelationCategory.relation_name).filter(
        #     OfflineRelationCategory.valid == 1).all()
        #
        # for offline_rc in uuids_and_names_in_offline_rc_for_dict:
        #     # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
        #     rc_uuid_dict_trans[offline_rc[0]] = online_dict_trans[
        #         offline_rc[1]] if online_dict_trans.get(offline_rc[1], "") else offline_rc[0]
        # print("rc_uuid_dict_trans", rc_uuid_dict_trans)

        # </editor-fold>

        # <editor-fold desc="sync_offline of Entity">
        # 定义模型类
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
        names_and_cate_uuids_in_online = Entity.query.with_entities(Entity.name, Entity.category_uuid,
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

        # offline-online: 取交集，需要更新synonyms和props
        offline_inter = list(set(diff_sign_in_offline).intersection(set(diff_sign_in_online)))
        offline_name_inter = [i[0:-36] for i in offline_inter]
        offline_cate_uuid_inter = [i[-36:] for i in offline_inter]

        # 如果有要更新的数据----更新synonyms和props
        if offline_inter:
            online_entities_update = Entity.query().filter(Entity.name.in_(offline_name_inter),
                                                           Entity.category_uuid.in_(offline_cate_uuid_inter)).all()
            for online_entity in online_entities_update:
                offline_entity = dbsession.query(OfflineEntity).filter_by(name=online_entity.name,
                                                                          category_uuid=online_entity.category_uuid).first()
                online_entity.synonyms = list(set(online_entity.synonyms.append(offline_entity.synonyms)))
                offline_entity.props.update(online_entity.props)  # 相同属性保留online的值
                online_entity.props = offline_entity.props
                online_entity.summary = online_entity.summary  # 不更新summary
                # online_entity.summary = online_entity.summary + ' ' + offline_entity.summary + "——来自" + offline_entity._source

            db.session.commit()

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
            db.session.add_all(sync_entities)
            db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_offline of EventClass">
        # 定义模型类
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
        uuids_and_names_in_online_evcl = EventClass.query.with_entities(EventClass.uuid, EventClass.name).filter(
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
            db.session.add_all(sync_event_classes)
            db.session.commit()

        # 如果有要更新的数据,更新的数据是前几次同步时由该离线系统插入的数据，uuid未改变
        if offline_uuids_to_update:
            offline_event_classes = dbsession.query(OfflineEventClass).filter(
                OfflineEventClass.uuid.in_(offline_uuids_to_update)).all()
            for offline_evcl in offline_event_classes:
                online_evcl = EventClass.query.filter_by(uuid=offline_evcl.uuid, _source=offline_evcl._source, valid=1).first()
                online_evcl.name = offline_evcl.name
                online_evcl.update_time = offline_evcl.update_time
            db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_offline of EventCategory">
        # 定义模型类
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
        names_and_class_uuids_in_online = EventCategory.query.with_entities(EventCategory.name,
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
            db.session.add_all(sync_event_categories)
            db.session.commit()

        # 如果有要更新的数据
        if offline_uuids_to_update:
            offline_event_categories = dbsession.query(OfflineEventCategory).filter(
                OfflineEventCategory.uuid.in_(offline_uuids_to_update)).all()
            for offline_event_cate in offline_event_categories:
                online_event_cate = EventCategory.query.filter_by(uuid=offline_event_cate.uuid,
                                                                  _source=offline_event_cate._source, valid=1).first()
                if online_event_cate:
                    online_event_cate.name = offline_event_cate.name
                    online_event_cate.event_class_uuid = offline_event_cate.event_class_uuid
                    online_event_cate.update_time = offline_event_cate.update_time
            db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkComment">
        # 定义模型类
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

            def __repr__(self):
                return '<DocMarkComment %r>' % self.uuid


        doc_mark_comment_in_offline = dbsession.query(OfflineDocMarkComment).filter(OfflineDocMarkComment.valid == 1,
                                                                                    or_(
                                                                                        OfflineDocMarkComment.create_time > sync_time,
                                                                                        OfflineDocMarkComment.update_time > sync_time)).all()
        # 更新create_by_uuid、update_by_uuid
        for i in doc_mark_comment_in_offline:
            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)
        # 同步offline_doc_mark_comment
        sync_doc_mark_comments = [DocMarkComment(uuid=i.uuid, doc_uuid=i.doc_uuid, name=i.name, position=i.position,
                                                comment=i.comment, create_by_uuid=i.create_by_uuid,
                                                create_time=i.create_time,
                                                update_by_uuid=i.update_by_uuid, update_time=i.update_time,
                                                _source=i._source,
                                                valid=i.valid) for i in doc_mark_comment_in_offline]
        db.session.add_all(sync_doc_mark_comments)
        db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkEntity">
        # 定义模型类
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
            appear_index_in_text = db.Column(db.JSON)
            valid = db.Column(db.Integer)
            _source = db.Column(db.String)

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
        # 同步offline_doc_mark_entity
        sync_doc_mark_entities = [
            DocMarkEntity(uuid=i.uuid, doc_uuid=i.doc_uuid, word=i.word, entity_uuid=i.entity_uuid, source=i.source,
                          create_by_uuid=i.create_by_uuid, create_time=i.create_time,
                          update_by_uuid=i.update_by_uuid, update_time=i.update_time,
                          appear_index_in_text=i.appear_index_in_text, _source=i._source, valid=i.valid) for i in
            doc_mark_entity_in_offline]
        db.session.add_all(sync_doc_mark_entities)
        db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkPlace">
        # 定义模型类
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
        sync_doc_mark_places = [
            DocMarkPlace(uuid=i.uuid, doc_uuid=i.doc_uuid, word=i.word, type=i.type, place_uuid=i.place_uuid,
                         direction=i.direction, place_lon=i.place_lon, place_lat=i.place_lat, height=i.height,
                         unit=i.unit, dms=i.dms, distance=i.distance, relation=i.relation,
                         create_by_uuid=i.create_by_uuid, create_time=i.create_time, update_by_uuid=i.update_by_uuid,
                         update_time=i.update_time, entity_or_sys=i.entity_or_sys,
                         appear_index_in_text=i.appear_index_in_text, _source=i._source, valid=i.valid) for i in
            doc_mark_place_in_offline]
        db.session.add_all(sync_doc_mark_places)
        db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkRelationProperty">
        # 定义模型类
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
                rc_online = RelationCategory.query.filter(
                    RelationCategory.relation_name == offline_rc_old.relation_name,
                    RelationCategory.source_entity_category_uuids.op('@>')(offline_rc_old.source_entity_category_uuids),
                    RelationCategory.target_entity_category_uuids.op('@>')(offline_rc_old.target_entity_category_uuids),
                    RelationCategory.valid == 1).first()
                i.relation_uuid = rc_online.uuid

            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)

        # 同步offline_doc_mark_relation_property
        sync_doc_mark_relation_property = [
            DocMarkRelationProperty(uuid=i.uuid, doc_uuid=i.doc_uuid, nid=i.nid, relation_uuid=i.relation_uuid,
                                    relation_name=i.relation_name, start_time=i.start_time, start_type=i.start_type,
                                    end_time=i.end_time, end_type=i.end_type, source_entity_uuid=i.source_entity_uuid,
                                    target_entity_uuid=i.target_entity_uuid, create_by_uuid=i.create_by_uuid,
                                    create_time=i.create_time, update_by_uuid=i.update_by_uuid,
                                    update_time=i.update_time, _source=i._source,
                                    valid=i.valid) for i in doc_mark_relation_property_in_offline]
        db.session.add_all(sync_doc_mark_relation_property)
        db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkTimeTag">
        # 定义模型类
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
        sync_doc_mark_time_tags = [DocMarkTimeTag(uuid=i.uuid, doc_uuid=i.doc_uuid, word=i.word, format_date=i.format_date,
                                                  format_date_end=i.format_date_end, mark_position=i.mark_position,
                                                  time_type=i.time_type, reserve_fields=i.reserve_fields,
                                                  arab_time=i.arab_time, create_by_uuid=i.create_by_uuid,
                                                 create_time=i.create_time, update_by_uuid=i.update_by_uuid,
                                                  update_time=i.update_time, appear_index_in_text=i.appear_index_in_text,
                                                  _source=i._source, valid=i.valid) for i in doc_mark_time_tag_in_offline]
        db.session.add_all(sync_doc_mark_time_tags)
        db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkMind">
        # 定义模型类
        class OfflineDocMarkMind(Base):  # 自动加载表结构
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

        doc_mark_mind_in_offline = dbsession.query(OfflineDocMarkMind).filter(OfflineDocMarkMind.valid == 1,
                                                                                     or_(
                                                                                         OfflineDocMarkMind.create_time > sync_time,
                                                                                         OfflineDocMarkMind.update_time > sync_time)).all()
        # 同步doc_mark_mind_in_offline
        sync_doc_mark_minds = [DocMarkMind(uuid=i.uuid, name=i.name, parent_uuid=i.parent_uuid, doc_uuid=i.doc_uuid,
                                           create_time=i.create_time, update_time=i.update_time, _source=i._source,
                                           valid=i.valid) for i in doc_mark_mind_in_offline]
        db.session.add_all(sync_doc_mark_minds)
        db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkAdvise">
        # 定义模型类
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
        # 更新create_by_uuid、update_by_uuid
        for i in doc_mark_advise_in_offline:
            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)

        # 同步doc_mark_advise_in_offline
        sync_doc_mark_advises = [
            DocMarkAdvise(uuid=i.uuid, doc_uuid=i.doc_uuid, mark_uuid=i.mark_uuid, type=i.type, content=i.content,
                          create_by_uuid=i.create_by_uuid, create_time=i.create_time, update_by_uuid=i.update_by_uuid,
                          update_time=i.update_time, _source=i._source, valid=i.valid) for i in
            doc_mark_advise_in_offline]
        db.session.add_all(sync_doc_mark_advises)
        db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocumentRecords">
        # 定义模型类
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
        db.session.add_all(sync_document_records)
        db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of DocMarkEvent">
        # 定义模型类
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
            i.create_by_uuid = customer_uuid_dict_trans.get(i.create_by_uuid)
            i.update_by_uuid = customer_uuid_dict_trans.get(i.update_by_uuid)

        # 同步doc_mark_events_in_offline
        sync_doc_mark_events = [
            DocMarkEvent(uuid=i.uuid, event_id=i.event_id, event_desc=i.event_desc, event_subject=i.event_subject,
                         event_predicate=i.event_predicate, event_object=i.event_object, event_time=i.event_time,
                         event_address=i.event_address, event_why=i.event_why, event_result=i.event_result,
                         event_conduct=i.event_conduct, event_talk=i.event_talk, event_how=i.event_how,
                         doc_uuid=i.doc_uuid, customer_uuid=i.customer_uuid, parent_uuid=i.parent_uuid,
                         title=i.title, event_class_uuid=i.event_class_uuid, event_type_uuid=i.event_type_uuid,
                         create_by_uuid=i.create_by_uuid, create_time=i.create_time, update_by_uuid=i.update_by_uuid,
                         update_time=i.update_time, add_time=i.add_time, _source=i._source,
                         valid=i.valid) for i in doc_mark_event_in_offline]
        db.session.add_all(sync_doc_mark_events)
        db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of Catalog">
        # 定义文档目录类
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
        catalogs = Catalog.query.filter_by(parent_uuid=None).all()
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
            catalog = Catalog.query.filter_by(uuid=uuid).first()
            res = [catalog.name]
            while catalog.parent_uuid:
                catalog = Catalog.query.filter_by(uuid=catalog.parent_uuid).first()
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
            tmp_catalogs = Catalog.query.filter_by(parent_uuid=uuid).all()
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
                tmp_online_catalog = Catalog.query.filter_by(uuid=online_catalog_uuids[online_index]).first()
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
            db.session.add_all(sync_catalog)
            db.session.commit()

        # </editor-fold>

        # <editor-fold desc="sync_offline of Document">
        # 定义文档类
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
        db.session.add_all(sync_document)
        db.session.commit()
        # </editor-fold>

    except Exception as e:
        print(str(e))
        if dbsession:
            dbsession.close()

    return "success"
