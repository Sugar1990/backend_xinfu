pg_insert_es_dict = {
"tags": [
        {
            "name": "initial"
        }
    ],
    "parameters":[
        {
            "name": "pg_table",
            "in": "query",
            "type": "string",
            "required": "true",
            "description": "name of pg_table"
        }],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Success !"}
        }
}

delete_index_dict = {
"tags": [
        {
            "name": "initial"
        }
    ],
    "parameters":[
        {
            "name": "es_index",
            "in": "query",
            "type": "string",
            "required": "true",
            "description": "index to be deleted"
        }],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Success !"}
        }
}

update_es_doc_dict = {
"tags": [
        {
            "name": "initial"
        }
    ],
    "parameters":[],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Success !"}
        }
}

