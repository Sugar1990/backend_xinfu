get_base_names_dict = {
    "tags": [
        {
            "name": "event"
        }
    ],
    "parameters": [],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Getting all base_names"
        }
    }
}
search_documents_dict = {
    "tags": [
        {
            "name": "event"
        }
    ],
    "parameters": [{
        "name": "search",
        "in": "query",
        "type": "string",
        "required": "true"
    },
    {
        "name": "start_date",
        "in": "query",
        "type": "string",
        "required": "true"
    },
    {
        "name": "end_date",
        "in": "query",
        "type": "string",
        "required": "true"
    }],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Getting searched documents"
        }
    }
}
find_event_dict = {
    "tags": [
        {
            "name": "event"
        }
    ],
    "parameters": [{
        "name": "object",
        "in": "query",
        "type": "string",
        "required": "true"
    },
    {
        "name": "event",
        "in": "query",
        "type": "string",
        "required": "true"
    },
        {
            "name": "start_date",
            "in": "query",
            "type": "string",
            "required": "true"
        },
        {
            "name": "end_date",
            "in": "query",
            "type": "string",
            "required": "true"
        },
        {
            "name": "location",
            "in": "query",
            "type": "string",
            "required": "true"
        }],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Getting events"
        }
    }
}
get_doc_events_dict = {
    "tags": [
        {
            "name": "event"
        }
    ],
    "parameters":[
        {
            "name": "docId",
            "in": "query",
            "type": "integer",
            "required": "true",
            "description": "docId of event"
        }],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Getting doc events by docID"}
        }
}
get_during_events_dict = {
    "tags": [
        {
            "name": "event"
        }
    ],
    "parameters": [{
            "name": "start_date",
            "in": "query",
            "type": "string",
            "required": "true"
        },
        {
            "name": "end_date",
            "in": "query",
            "type": "string",
            "required": "true"
        }],
    "responses":{
        "500":{"description": "Error !"},
        "200":{
            "description": "Getting all events"
        }
    }
}


