from cequery import make_parameters

MUTATION = '''
mutation {{
  {mutation}
}}
'''

# We say that 2 different scores of the same thing are a broad match
ADD_DIGITAL_DOCUMENT_BROAD_MATCH = '''
AddDigitalDocumentBroadMatch(
  from: {{identifier: "{from_document_id}" }}
  to: {{identifier: "{to_document_id}" }}
) {{
  from {{
    identifier
  }}
  to {{
    identifier
  }}
}}
'''

REMOVE_DIGITAL_DOCUMENT_BROAD_MATCH = '''
RemoveDigitalDocumentBroadMatch(
  from: {{identifier: "{from_document_id}" }}
  to: {{identifier: "{to_document_id}" }}
) {{
  from {{
    identifier
  }}
  to {{
    identifier
  }}
}}
'''

ADD_DIGITAL_DOCUMENT_WORK_EXAMPLE_COMPOSITION = '''
AddThingInterfaceCreativeWorkInterface(
    from: {{identifier: "{document_id}" type:DigitalDocument}}
    to: {{identifier: "{composition_id}" type:MusicComposition}}
    field: exampleOfWork
) {{
    from {{
      __typename
    }}
    to {{
      __typename
    }}
}}
'''

REMOVE_DIGITAL_DOCUMENT_WORK_EXAMPLE_COMPOSITION = '''
RemoveThingInterfaceCreativeWorkInterface(
    from: {{identifier: "{document_id}" type:DigitalDocument}}
    to: {{identifier: "{composition_id}" type:MusicComposition}}
    field: exampleOfWork
) {{
    from {{
      __typename
    }}
    to {{
      __typename
    }}
}}
'''

CREATE_DIGITAL_DOCUMENT = '''
CreateDigitalDocument(
  {parameters}
) {{
  identifier
  relation
}}
'''

UPDATE_DIGITAL_DOCUMENT = '''
UpdateDigitalDocument(
  {parameters}
) {{
  identifier
  relation
}}
'''


def get_query_add_document_broad_match(from_document_id, to_document_id):
    query = ADD_DIGITAL_DOCUMENT_BROAD_MATCH.format(from_document_id=from_document_id, to_document_id=to_document_id)
    return MUTATION.format(mutation=query)


def get_query_remove_document_broad_match(from_document_id, to_document_id):
    query = REMOVE_DIGITAL_DOCUMENT_BROAD_MATCH.format(from_document_id=from_document_id, to_document_id=to_document_id)
    return MUTATION.format(mutation=query)


def get_query_add_document_composition(composition_id, document_id):
    query = ADD_DIGITAL_DOCUMENT_WORK_EXAMPLE_COMPOSITION.format(document_id=document_id, composition_id=composition_id)
    return MUTATION.format(mutation=query)


def get_query_remove_document_composition(composition_id, document_id):
    query = REMOVE_DIGITAL_DOCUMENT_WORK_EXAMPLE_COMPOSITION.format(document_id=document_id, composition_id=composition_id)
    return MUTATION.format(mutation=query)


def transform_data_create_document(document_args):
    create_digital_document = CREATE_DIGITAL_DOCUMENT.format(parameters=make_parameters(**document_args))
    return MUTATION.format(mutation=create_digital_document)


def transform_data_update_document(document_args):
    update_digital_document = UPDATE_DIGITAL_DOCUMENT.format(parameters=make_parameters(**document_args))
    return MUTATION.format(mutation=update_digital_document)
