import requests
import json

from ..conf import NEO4J_SERVER_IP, NEO4J_SERVER_PORT


def create_node(entity_id, entity_name, category_id):
    try:
        root_url = f'http://{NEO4J_SERVER_IP}:{NEO4J_SERVER_PORT}'
        header = {"Content-Type": "application/json"}
        serve_url = root_url + '/create_node/node'
        data = {
            "label": "Entity",
            "id": str(entity_id),
            "name": entity_name,
            "category_id": str(category_id)
        }
        req = requests.post(url=serve_url, data=json.dumps(data), headers=header)
        if req.status_code != 200:
            print("neo4j create node request except")
        elif not json.loads(req.text).get("code", 0):
            print("neo4j create node request error:", json.loads(req.text))
    except Exception as e:
        print("create_node except:", str(e))


def update_node(entity_id, entity_name, category_id):
    try:
        root_url = f'http://{NEO4J_SERVER_IP}:{NEO4J_SERVER_PORT}'
        header = {"Content-Type": "application/json"}
        serve_url = root_url + '/update/node'
        data = {
            "label": "Entity",
            "id": str(entity_id),
            "properties": {
                "name": entity_name,
                "category_id": str(category_id)
            }
        }
        req = requests.post(url=serve_url, data=json.dumps(data), headers=header)
        if req.status_code != 200:
            print("neo4j update node request except")
        elif not json.loads(req.text).get("code", 0):
            print("neo4j update node request error:", json.loads(req.text))
    except Exception as e:
        print("update_node except:", str(e))


def delete_node(entity_id):
    try:
        root_url = f'http://{NEO4J_SERVER_IP}:{NEO4J_SERVER_PORT}'
        header = {"Content-Type": "application/json"}
        serve_url = root_url + '/delete/node'
        data = {
            "label": "Entity",
            "id": str(entity_id)
        }
        req = requests.post(url=serve_url, data=json.dumps(data), headers=header)
        if req.status_code != 200:
            print("neo4j delete node request except")
        elif not json.loads(req.text).get("code", 0):
            print("neo4j delete node request error:", json.loads(req.text))
    except Exception as e:
        print("delete_node except:", str(e))


def create_edge(source_entity_id, target_entity_id, relation_name):
    try:
        root_url = f'http://{NEO4J_SERVER_IP}:{NEO4J_SERVER_PORT}'
        header = {"Content-Type": "application/json"}
        serve_url = root_url + '/create_edge/edge'
        data = {
            "source_node_id": str(source_entity_id),
            "target_node_id": str(target_entity_id),
            "relation_name": relation_name,
            "edge_type": "0"
        }
        req = requests.post(url=serve_url, data=json.dumps(data), headers=header)
        if req.status_code != 200:
            print("neo4j create edge request except")
        elif not json.loads(req.text).get("code", 0):
            print("neo4j create edge request error:", json.loads(req.text))
    except Exception as e:
        print("create_edge except:", str(e))
