import configparser

import requests

from cequery import query

config = configparser.ConfigParser()
config.read('import.ini')


def submit_query(querystr: str):
    q = {"query": querystr}
    server = config["import"]["server"]
    r = requests.post(server, json=q)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        print("error")
        print(r.json())
    return r.json()


def get_person_by_source(source):
    querystr = query.query_person_by_source(source)
    resp = submit_query(querystr)
    return resp["data"]["Person"]


def get_music_composition_by_source(source):
    querystr = query.query_music_composition_by_source(source)
    resp = submit_query(querystr)
    return resp["data"]["MusicComposition"]
