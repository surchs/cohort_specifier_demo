import json

import requests
from requests.auth import HTTPBasicAuth


DEFAULT_CONTEXT = '''
PREFIX afni: <http://purl.org/nidash/afni#>
PREFIX ants: <http://stnava.github.io/ANTs/>
PREFIX bids: <http://bids.neuroimaging.io/>
PREFIX birnlex: <http://bioontology.org/projects/ontologies/birnlex/>
PREFIX crypto: <http://id.loc.gov/vocabulary/preservation/cryptographicHashFunctions#>
PREFIX datalad: <http://datasets.datalad.org/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX dctypes: <http://purl.org/dc/dcmitype/>
PREFIX dicom: <http://neurolex.org/wiki/Category:DICOM_term/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX freesurfer: <https://surfer.nmr.mgh.harvard.edu/>
PREFIX fsl: <http://purl.org/nidash/fsl#>
PREFIX ilx: <http://uri.interlex.org/base/>
PREFIX ncicb: <http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#>
PREFIX ncit: <http://ncitt.ncit.nih.gov/>
PREFIX ndar: <https://ndar.nih.gov/api/datadictionary/v2/dataelement/>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
PREFIX nidm: <http://purl.org/nidash/nidm#>
PREFIX niiri: <http://iri.nidash.org/>
PREFIX nlx: <http://uri.neuinfo.org/nif/nifstd/>
PREFIX obo: <http://purl.obolibrary.org/obo/>
PREFIX onli: <http://neurolog.unice.fr/ontoneurolog/v3.0/instrument.owl#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX pato: <http://purl.obolibrary.org/obo/pato#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX scr: <http://scicrunch.org/resolver/>
PREFIX sio: <http://semanticscience.org/ontology/sio.owl#>
PREFIX spm: <http://purl.org/nidash/spm#>
PREFIX vc: <http://www.w3.org/2006/vcard/ns#>
PREFIX xml: <http://www.w3.org/XML/1998/namespace>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
'''

DOG_ROOT = 'http://star.braindog.net'
DOG_DB = 'demo_integration'
DOG_PORT = 5820
QUERY_URL = f'{DOG_ROOT}:{DOG_PORT}/{DOG_DB}/query'
QUERY_HEADER = {'Content-Type': 'application/sparql-query', 'Accept': 'application/sparql-results+json'}
QUERY_AUTH = HTTPBasicAuth('admin', 'admin')

AGE_VAR = 'age'
AGE_REL = 'nidm:hasAge'
GENDER_VAR = 'gender'
GENDER_REL = 'nidm:hasGender'
DIAGNOSIS_VAR = 'diagnosis'
DIAGNOSIS_REL = 'nidm:hasDiagnosis'
IMAGE_VAR = 'image'
IMAGE_REL = 'nidm:hadImageContrastType'
TOOL_VAR = 'tool'
TOOL_REL = ''
PROJECT_VAR = 'project'
PROJECT_REL = 'nidm:isPartOfProject'


def create_query(age: tuple = (None, None),
                 gender: str = None,
                 image: str = None,
                 diagnosis: str= None,
                 tool: str = None) -> str:
    """

    Parameters
    ----------
    age :
    gender :
    image :
    diagnosis :
    tool :

    Returns
    -------

    """
    # select_str = ''
    q_body = ''
    filter_body = ''
    if age is not None and not age == (None, None):
        # select_str += f' ?{AGE_VAR}'
        filter_body += '\n' + f'FILTER (?{AGE_VAR} > {age[0]} && ?{AGE_VAR} < {age[1]}).'
    q_body += '\n' + f'OPTIONAL {{?siri {AGE_REL} ?{AGE_VAR} }}'

    if gender is not None:
        # select_str += f' ?{GENDER_VAR}'
        filter_body += '\n' + f'FILTER (?{GENDER_VAR} = "{gender}").'
    q_body += '\n' + f'OPTIONAL {{?siri {GENDER_REL} ?{GENDER_VAR} }}'

    if image is not None:
        # select_str += f' ?{IMAGE_VAR}'
        filter_body += '\n' + f'FILTER (?{IMAGE_VAR} = {image}).'
    q_body += '\n' + f'OPTIONAL {{?siri {IMAGE_REL} ?{IMAGE_VAR} }}'

    if diagnosis is not None:

        # select_str += ' ?diagnosis'
        filter_body += '\n' + f'FILTER (?{DIAGNOSIS_VAR} = <{diagnosis}>).'
    q_body += '\n' + f'OPTIONAL {{?siri {DIAGNOSIS_REL} ?{DIAGNOSIS_VAR} }}'

    if tool is not None:
        pass

    # Temporary override
    select_str = '?age ?gender ?image ?diagnosis'

    q_preamble = DEFAULT_CONTEXT + f'''
    SELECT DISTINCT ?open_neuro_id ?siri {select_str} 
    WHERE {{
        ?siri a prov:Person.
        ?siri {PROJECT_REL} ?{PROJECT_VAR}.
        
        ?{PROJECT_VAR} a nidm:Project;
            dctypes:title ?projectname;
            prov:Location ?project_location .
        BIND( strafter(?project_location,"openneuro/") AS ?open_neuro_id ) .
    '''
    query = '\n'.join([q_preamble, q_body, filter_body, '}'])

    return query


def process_query(query_str: str) -> str:
    """

    Parameters
    ----------
    query_str :

    Returns
    -------

    """
    response = requests.post(url=QUERY_URL, data=query_str, headers=QUERY_HEADER, auth=QUERY_AUTH)
    if not response.ok:
        raise Exception(f"Query request unsuccesful ({response.status_code}): {response.content.decode('utf-8')}")

    _results = json.loads(response.content.decode('utf-8'))
    return [{k: v['value'] for k, v in res.items()} for res in _results['results']['bindings']]