# -*- coding: UTF-8 -*-
import os
from datetime import time

from sqlalchemy.dialects.postgresql import JSONB

from . import api_sync_offline as blue_print
from ..models import Customer, db, EntityCategory, RelationCategory, SyncRecords, Entity

from sqlalchemy import create_engine, MetaData, Table, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session


@blue_print.route('/sync_offline', methods=['GET'])
def sync_offline():
    try:
        # todo 改为request请求
        OFFLINE_PG_USER_NAME = os.getenv('OFFLINE_PG_USER_NAME', 'postgres')
        OFFLINE_PG_USER_PASSWORD = os.getenv('OFFLINE_PG_USER_PASSWORD', 'postgres')
        OFFLINE_PG_DB_SERVER_IP = os.getenv('OFFLINE_PG_DB_SERVER_IP', '192.168.2.159')
        OFFLINE_PG_DB_PORT = os.getenv('OFFLINE_PG_DB_PORT', '5432')
        OFFLINE_PG_DB_NAME = os.getenv('OFFLINE_PG_DB_NAME', 'offline_tagging_system_for_sync')

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
            create_by_uuid = db.Column(db.String)
            create_time = db.Column(db.DateTime)
            update_by_uuid = db.Column(db.String)
            update_time = db.Column(db.DateTime)

            def __repr__(self):
                return '<Customer %r>' % self.username

        # offline所有uuid/troop_number，唯一性（去重）判断
        uuids_and_troop_in_offline = dbsession.query(OfflineCustomer).with_entities(OfflineCustomer.uuid,
                                                                                    OfflineCustomer.troop_number).filter(
            OfflineCustomer.valid == 1, or_(dbsession.func.date(OfflineCustomer.create_time) > sync_time,
                                            dbsession.func.date(OfflineCustomer.update_time) > sync_time)).all()
        troop_numbers_in_offline = [i[1] for i in uuids_and_troop_in_offline]

        # online所有uuid/troop_number，唯一性（去重）判断
        uuids_and_troop_in_online = Customer.query.with_entities(Customer.uuid, Customer.troop_number).filter_by(
            valid=1).all()
        troop_numbers_in_online = [i[1] for i in uuids_and_troop_in_online]

        # 记录uuid变化----customer_uuid_dict_trans
        online_dict_trans = {}
        customer_uuid_dict_trans = {}

        for i in uuids_and_troop_in_online:
            if i[1] not in online_dict_trans.keys():
                online_dict_trans[i[1]] = i[0]  # [{"troop_number": "uuid"}]

        for offline_customer in uuids_and_troop_in_offline:
            # offtroop存在, {"offuuid": "onuuid"}, offtroop不存在, {"offuuid": "offuuid"}
            customer_uuid_dict_trans[offline_customer[0]] = online_dict_trans[
                offline_customer[1]] if online_dict_trans.get(offline_customer[1], "") else offline_customer[0]

        # offline-online：计算是否有要插入的数据
        offline_troop_numbers = list(set(troop_numbers_in_offline).difference(set(troop_numbers_in_online)))

        # 如果有要插入的数据
        if offline_troop_numbers:
            offline_customers = dbsession.query(OfflineCustomer).filter(OfflineCustomer.troop_number.in_(offline_troop_numbers)).all()
            sync_customers = [Customer(uuid=i.uuid,
                                       username=i.username,
                                       pwd=i.pwd,
                                       permission_id=i.permission_id,
                                       valid=i.valid,
                                       token=i.token,
                                       _source=i._source,
                                       power_score=i.power_score,
                                       troop_number=i.troop_number) for i in offline_customers]
            db.session.add_all(sync_customers)
            db.session.commit()
        # </editor-fold>

        # <editor-fold desc="sync_offline of EntityCategory">
        # 定义模型类
        class OfflineEntityCategory(Base):  # 自动加载表结构
            # __table__ = Table('customer', md, autoload=True)
            __tablename__ = 'entity_category'
            uuid = db.Column(db.String, primary_key=True)
            name = db.Column(db.Text)
            valid = db.Column(db.Integer)  # 取值0或1，0表示已删除，1表示正常
            type = db.Column(db.Integer)  # 1：实体（地名、国家、人物...）；2：概念（条约公约、战略、战法...）
            _source = db.Column(db.String)
            create_by_uuid = db.Column(db.String)
            create_time = db.Column(db.DateTime)
            update_by_uuid = db.Column(db.String)
            update_time = db.Column(db.DateTime)

            def __repr__(self):
                return '<EntityCategory %r>' % self.uuid

        # offline所有name，唯一性（去重）判断
        uuids_and_names_in_offline_ec = dbsession.query(OfflineEntityCategory).with_entities(OfflineEntityCategory.uuid,
                                                                                             OfflineEntityCategory.name).filter(
            OfflineEntityCategory.valid==1, or_(dbsession.func.date(OfflineEntityCategory.create_time) > sync_time,
                                            dbsession.func.date(OfflineEntityCategory.update_time) > sync_time)).all()
        names_in_offline = [i[1] for i in uuids_and_names_in_offline_ec]

        # online所有name，唯一性（去重）判断
        uuids_and_names_in_online_ec = EntityCategory.query.with_entities(EntityCategory.uuid,
                                                                          EntityCategory.name).filter_by(valid=1).all()
        names_in_online = [i[1] for i in uuids_and_names_in_online_ec]

        # 记录uuid变化----ec_uuid_dict_trans
        online_dict_trans = {}
        ec_uuid_dict_trans = {}

        for i in uuids_and_names_in_online_ec:
            if i[1] not in online_dict_trans.keys():
                online_dict_trans[i[1]] = i[0]  # {"onname": "onuuid"}

        for offline_ec in uuids_and_names_in_online_ec:
            # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
            ec_uuid_dict_trans[offline_ec[0]] = online_dict_trans[
                offline_ec[1]] if online_dict_trans.get(offline_ec[1], "") else offline_ec[0]

        # offline-online：计算是否有要插入的数据
        offline_names = list(set(names_in_offline).difference(set(names_in_online)))

        # 如果有要插入的数据
        if offline_names:
            offline_entity_cateogories = dbsession.query(OfflineEntityCategory).filter(
                OfflineEntityCategory.name.in_(offline_names)).all()
            sync_entity_categories = [EntityCategory(uuid=i.uuid,
                                       name=i.name,
                                       valid=i.valid,
                                       type=i.type,
                                       _source=i._source) for i in offline_entity_cateogories]
            db.session.add_all(sync_entity_categories)
            db.session.commit()
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
            create_by_uuid = db.Column(db.String)
            create_time = db.Column(db.DateTime)
            update_by_uuid = db.Column(db.String)
            update_time = db.Column(db.DateTime)

            def __repr__(self):
                return '<RelationCategory %r>' % self.uuid

        # 更新source/target_entity_category_uuids
        relation_categories_in_offline = dbsession.query(OfflineRelationCategory).filter_by(valid=1).all()
        for i in relation_categories_in_offline:
            for index, value in enumerate(i.source_entity_category_uuids):
                i.source_entity_category_uuids[index] = customer_uuid_dict_trans.get(value)
            for index, value in enumerate(i.target_entity_category_uuids):
                i.target_entity_category_uuids[index] = customer_uuid_dict_trans.get(value)

        # offline所有relation_name，唯一性（去重）判断
        uuids_and_names_in_offline_rc = dbsession.query(OfflineRelationCategory).with_entities(
            OfflineRelationCategory.uuid, OfflineRelationCategory.relation_name).filter(
            OfflineRelationCategory.valid == 1, or_(dbsession.func.date(OfflineEntityCategory.create_time) > sync_time,
                                                    dbsession.func.date(
                                                        OfflineEntityCategory.update_time) > sync_time)).all()
        names_in_offline = [i[1] for i in uuids_and_names_in_offline_rc]

        # online所有relation_name，唯一性（去重）判断
        uuids_and_names_in_online_rc = RelationCategory.query.with_entities(RelationCategory.uuid,
                                                                            RelationCategory.relation_name).filter_by(
            valid=1).all()
        names_in_online = [i[1] for i in uuids_and_names_in_online_rc]

        # 记录uuid变化----rc_uuid_dict_trans
        online_dict_trans = {}
        rc_uuid_dict_trans = {}

        for i in uuids_and_names_in_online_rc:
            if i[1] not in online_dict_trans.keys():
                online_dict_trans[i[1]] = i[0]  # {"onname": "onuuid"}

        for offline_rc in uuids_and_names_in_online_rc:
            # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
            rc_uuid_dict_trans[offline_rc[0]] = online_dict_trans[
                offline_rc[1]] if online_dict_trans.get(offline_rc[1], "") else offline_rc[0]

        # offline-online：计算是否有要插入的数据
        offline_names = list(set(names_in_offline).difference(set(names_in_online)))

        # 如果有要插入的数据
        if offline_names:
            offline_relation_cateogories = dbsession.query(OfflineRelationCategory).filter(
                OfflineRelationCategory.relation_name.in_(offline_names)).all()
            sync_relation_categories = [RelationCategory(uuid=i.uuid,
                                                         source_entity_category_uuids=i.source_entity_category_uuids,
                                                         target_entity_category_uuids=i.target_entity_category_uuids,
                                                         relation_name=i.relation_name,
                                                         valid=i.valid,
                                                         _source=i._source) for i in offline_relation_cateogories]
            db.session.add_all(sync_relation_categories)
            db.session.commit()
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
            create_by_uuid = db.Column(db.String)
            create_time = db.Column(db.DateTime)
            update_by_uuid = db.Column(db.String)
            update_time = db.Column(db.DateTime)

            def __repr__(self):
                return '<Entity %r>' % self.uuid

        # 更新category_uuids
        entities_in_offline = dbsession.query(OfflineEntity).all()
        for i in entities_in_offline:
            i.category_uuid = ec_uuid_dict_trans.get(i.category_uuid)

        # offline所有name+category_uuid，唯一性（去重）判断
        names_and_cate_uuids_in_offline = dbsession.query(OfflineEntity).with_entities(OfflineEntity.name,
                                                                                       OfflineEntity.category_uuid,
                                                                                       OfflineEntity.uuid).filter(
            OfflineEntity.valid == 1, or_(dbsession.func.date(OfflineEntity.create_time) > sync_time,
                                          dbsession.func.date(OfflineEntity.update_time) > sync_time)).all()
        diff_sign_in_offline = [i[0]+i[1] for i in names_and_cate_uuids_in_offline]

        # online所有name+category_uuid，唯一性（去重）判断
        names_and_cate_uuids_in_online = Entity.query.with_entities(Entity.name, Entity.category_uuid, Entity.uuid).filter_by(
            valid=1).all()
        diff_sign_in_online = [i[0]+i[1] for i in names_and_cate_uuids_in_online]

        # 记录uuid变化----entity_uuid_dict_trans
        online_dict_trans = {}
        entity_uuid_dict_trans = {}

        for i in names_and_cate_uuids_in_online:
            if i[0]+i[1] not in online_dict_trans.keys():
                online_dict_trans[i[0]+i[1]] = i[2]  # {"onname+oncate_uuid": "onuuid"}

        for offline_entity in names_and_cate_uuids_in_offline:
            # offname存在, {"offuuid": "onuuid"}, offname不存在, {"offuuid": "offuuid"}
            entity_uuid_dict_trans[offline_entity[2]] = online_dict_trans[
                offline_entity[0] + offline_entity[1]] if online_dict_trans.get(offline_entity[0] + offline_entity[1],
                                                                                "") else offline_entity[2]

        # offline-online：计算是否有要插入的数据
        offline_diff = list(set(diff_sign_in_offline).difference(set(diff_sign_in_online)))
        offline_name_diff = [i[0:-36] for i in offline_diff]
        offline_cate_uuid_diff = [i[-36:] for i in offline_diff]

        # offline-online: 取交集，需要更新synonyms和props
        offline_inter = list(set(diff_sign_in_offline).intersection(set(diff_sign_in_online)))
        offline_name_inter = [i[0:-36] for i in offline_inter]
        offline_cate_uuid_inter = [i[-36:] for i in offline_inter]

        # 如果有要更新的数据
        if offline_inter:
            online_entities_update = Entity.query().filter(Entity.name.in_(offline_name_inter),
                                                           Entity.category_uuid.in_(offline_cate_uuid_inter)).all()
            for online_entity in online_entities_update:
                offline_entity = dbsession.query(OfflineEntity).filter_by(name=online_entity.name,
                                                                          category_uuid=online_entity.category_uuid).first()
                online_entity.synonyms = list(set(online_entity.synonyms.append(offline_entity.synonyms)))
                offline_entity.props.update(online_entity.props) # 相同属性保留online的值
                online_entity.props = offline_entity.props
                online_entity.summary = online_entity.summary+' '+offline_entity.summary+"——来自"+offline_entity._source

            db.session.commit()

        # 如果有要插入的数据
        if offline_diff:
            offline_entities = dbsession.query(OfflineEntity).filter(
                OfflineEntity.name.in_(offline_name_diff),
                OfflineEntity.category_uuid.in_(offline_cate_uuid_diff)).all()
            sync_entities = [Entity(uuid=i.uuid, name=i.name, synonyms=i.synonyms, props=i.props,
                                    category_uuid=i.category_uuid, summary=i.summary, valid=i.valid,
                                    longitude=i.longitude, latitude=i.latitude, _source=i._source) for i in offline_entities]
            db.session.add_all(sync_entities)
            db.session.commit()
        # </editor-fold>


        # 更新同步时间
        sync_record.sync_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        db.session.commit()

    except Exception as e:
        print(str(e))
        if dbsession:
            dbsession.close()

    return "success"
