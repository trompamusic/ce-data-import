import requests


def submit_query(query: str):
    q = {"query": query}
    r = requests.post("http://localhost:4000", json=q)
    print(r.json())
