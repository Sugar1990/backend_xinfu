# -*- coding:utf-8 -*-
# author: Scandium
# work_location: Bei Jing
import os

PG_USER_NAME = os.getenv('PG_USER_NAME', 'iecas')
PG_USER_PASSWORD = os.getenv('PG_USER_PASSWORD', 'iecas123')
PG_DB_SERVER_IP = os.getenv('PG_DB_SERVER_IP', '192.168.2.16')
PG_DB_PORT = os.getenv('PG_DB_PORT', '5432')
PG_DB_NAME = os.getenv('PG_DB_NAME', 'Tagging System')

MINIO_SERVER_IP = os.getenv('MINIO_SERVER_IP', '192.168.3.212')
MINIO_PORT = os.getenv('MINIO_PORT', '9001')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minio_ak')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minio_sk')

LEXICON_IP = os.getenv('LEXICON_IP', "192.168.2.158")
LEXICON_PORT = os.getenv('LEXICON_PORT', "10003")
SUMMARY_IP = os.getenv('SUMMARY_IP', "192.168.2.158")
SUMMARY_PORT = os.getenv('SUMMARY_PORT', "10004")

ES_SERVER_IP = os.getenv('ES_SERVER_IP', '172.11.0.21')
ES_SERVER_PORT = os.getenv('ES_SERVER_PORT', 6789)

NEO4J_SERVER_IP = os.getenv('NEO4J_SERVER_IP', '192.168.2.159')
NEO4J_SERVER_PORT = os.getenv('NEO4J_SERVER_PORT', '5008')

# 管理员账号
ADMIN_ROLE_POWER = os.getenv('ADMIN_ROLE_POWER', 102)
ADMIN_ROLE_NAME = os.getenv('ADMIN_ROLE_NAME', '管理员')
ADMIN_NAME = os.getenv('ADMIN_ROLE_NAME', 'admin')
ADMIN_PWD = os.getenv('ADMIN_ROLE_PWD', 'admin')

# 系统维护员账号
ASSIS_ROLE_POWER = os.getenv('ASSIS_ROLE_POWER', 101)
ASSIS_ROLE_NAME = os.getenv('ASSIS_ROLE_NAME', '系统维护人员')
ASSIS_NAME = os.getenv('ASSIS_NAME', 'assistant')
ASSIS_PWD = os.getenv('ASSIS_PWD', 'assistant')

# 地名库名称
PLACE_BASE_NAME = os.getenv('PLACE_BASE_NAME', '地名')
PLACE_BASE_SERVER_IP = os.getenv('PLACE_BASE_SERVER_IP', 'http://192.168.6.82:28080/api/v1')
PLACE_BASE_OLD_SERVER_IP = os.getenv('PLACE_BASE_OLD_SERVER_IP', 'http://192.168.6.82:9001/api/v1')
USE_PLACE_SERVER = os.getenv('USE_PLACE_SERVER', 0)

# 雨辰团队接口url, http://192.168.3.75:8096/dev
YC_ROOT_URL = os.getenv('YC_ROOT_URL', "http://192.168.6.82:8096")
YC_ROOT_URL_PYTHON = os.getenv('YC_ROOT_URL_PYTHON', "http://192.168.6.82:8989")
# 雨辰团队标注页面
YC_TAGGING_PAGE_URL = os.getenv('YC_TAGGING_PAGE_URL', "http://192.168.6.82:8098/index")
EVENT_EXTRACTION_URL = os.getenv('EVENT_EXTRACTION_URL', "http://192.168.6.82:8083")

LOCAL_IP = os.getenv('LOCAL_IP', "192.168.6.82")
LOCAL_PG_PORT = os.getenv('PG_OUT_PORT', 10000)
LOCAL_PORT = os.getenv('LOCAL_PORT', 8088)

# 标注tab功能
TAG_TABS = os.getenv('TAG_TABS', "{\"实体标注\":1,\"时间标注\":2,\"地点标注\":3,\"关系标注\":4,\"事件标注\":5,\"批注\":6,\"思维导图\":7,\"实体概念\":8}")
MIN_PRICISE_OF_PERMSSION = 0.0000001

LOCAL_SOURCE = os.getenv('LOCAL_SOURCE', "在线")

LOCAL_SOURCE = os.getenv('LOCAL_SOURCE', "离线")