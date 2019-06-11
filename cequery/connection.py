import requests

from cequery import query


def submit_query(querystr: str):
    q = {"query": querystr}
    r = requests.post("http://localhost:4000", json=q)
    r.raise_for_status()
    return r.json()


def get_person_by_source(source):
    querystr = query.query_person_by_source(source)
    resp = submit_query(querystr)
    return resp["data"]["Person"]


def get_music_composition_by_source(source):
    querystr = query.query_music_composition_by_source(source)
    resp = submit_query(querystr)
    return resp["data"]["MusicComposition"]
