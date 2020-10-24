import requests
import json

from ..conf import NEO4J_SERVER_IP, NEO4J_SERVER_PORT


def create_node(entity_id, entity_name, category_id):
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
