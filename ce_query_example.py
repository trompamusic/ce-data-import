import json

import requests
from requests.adapters import HTTPAdapter


# configure requests to retry failed queries
s = requests.Session()
adapter = HTTPAdapter(max_retries=5, pool_connections=100, pool_maxsize=100)
s.mount("https://", adapter)
s.mount("http://", adapter)

# Where we perform our queries to
#GRAPHQL_ENDPOINT = "http://localhost:4000"
GRAPHQL_ENDPOINT = "https://api-test.trompamusic.eu"


# Remove (first: %s) to get all documents instead of just some
QUERY_ALL_DOCUMENTS = """
query {
    DigitalDocument(first: %s) {
    name
    identifier
    relation
    subjectOf {
      ... on MusicComposition {
        identifier
        name
        source
        author {
          ... on Person {
            identifier
            name
            source
          }
        }
      }
    }
  }
}
"""

QUERY_COMPOSITION_BY_URL = """
query {
    MusicComposition(source: %s) {
        identifier
        name
        source
        author {
            ... on Person {
                identifier
                name
                source
          }
        }
    }
}
"""

# This can only be queried with an exact string of the composer name for now,
# you can't query by an internal identifier (for example)
QUERY_COMPOSITION_BY_COMPOSER = """
query {
  MusicComposition(creator: %s) {
    identifier
    name
    author {
      ... on Person {
        identifier
        name
        source
      }
    }
  }
}
"""

QUERY_DOCUMENT_BY_SOURCE = """
query {
    DigitalDocument(source: %s) {
    name
    identifier
    relation
    subjectOf {
      ... on MusicComposition {
        identifier
        name
        source
        author {
          ... on Person {
            identifier
            name
            source
          }
        }
      }
    }
  }
}
"""

QUERY_PERSON_BY_NAME = """
query {
    Person(name: %s) {
        identifier
        name
        source
    }
}"""


def _encode_string(value):
    """Performs json encoding on the given string parameter, including quoting"""
    encoder = json.JSONEncoder()
    value = encoder.encode(value)
    return value


def do_graphql_query(query):
    """Submit a Graphql query to an endpoint
    Arguments:
        query (str): The full graphql query to submit to the endpoint

    Returns:
        The json response from graphql
    Raises:
        requests.exceptions.HTTPError if there was an error returned from the server
    """
    q = {"query": query}
    r = requests.post(GRAPHQL_ENDPOINT, json=q)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        print("error")
        # You should handle the case where this exception will happen, it's especially
        # important if the query was badly formed
        raise
    return r.json()["data"]


def search_title(title):
    pass


def get_all_documents(num_items):
    """Get `num_items` random documents from the database"""
    query = QUERY_ALL_DOCUMENTS % num_items
    response = do_graphql_query(query)
    return response["DigitalDocument"]


def get_composition_by_url(url):
    """Get information about a composition given the information URL of it on a site (e.g. cpdl or imslp)"""
    query = QUERY_COMPOSITION_BY_URL % _encode_string(url)
    response = do_graphql_query(query)
    return response["MusicComposition"]


def get_composition_by_composer(composer_name):
    """Get information about a composition given a string of the composer's name"""
    query = QUERY_COMPOSITION_BY_COMPOSER % _encode_string(composer_name)
    response = do_graphql_query(query)
    return response["MusicComposition"]


def get_document_by_source_url(source_url):
    """Get a Document (score) given its url, and also include information about the composition and author"""
    query = QUERY_DOCUMENT_BY_SOURCE % _encode_string(source_url)
    response = do_graphql_query(query)
    return response["DigitalDocument"]


def main():
    print("Get all documents:")
    documents = get_all_documents(3)
    print(json.dumps(documents, indent=2))
    print("=" * 70)

    print("Query composition by URL")
    compositions = get_composition_by_url("http://www.cpdl.org/wiki/index.php/10_catches_(Henry_Purcell)")
    print(json.dumps(compositions, indent=2))
    print("=" * 70)

    print("Query composition by composer name")
    compositions = get_composition_by_composer("Ralph Vaughan Williams")
    print(json.dumps(compositions, indent=2))
    print("=" * 70)

    print("Document by source")
    documents = get_document_by_source_url("https://www.cpdl.org/wiki/images/b/b2/El_Rossinyol.mxl")
    print(json.dumps(documents, indent=2))
    print("=" * 70)


if __name__ == '__main__':
    main()

