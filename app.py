import json

import dash
import pandas as pd
from dash import dash_table, html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from query import process_query, create_query

external_stylesheets = [dbc.themes.BOOTSTRAP, "assets/object_properties_style.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# Define table

categories = [
    'Dataset', 'Subject', 'Age', 'Gender', 'Modality', 'Diagnosis'
]
columns = [{'id': c, 'name': c} for c in categories]


# Define Header Layout
header = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.A(
                            html.Img(
                                src=app.get_asset_url("rubber_duck.png"),
                                height="30px",
                            ),
                            href="https://neurodatascience.github.io/",
                        )
                    ),
                    dbc.Col(dbc.NavbarBrand("Cohort Definition Tool")),
                ],
                align="center",
            ),
            dbc.Row(
                dbc.Col(
                    [
                        dbc.NavbarToggler(id="navbar-toggler"),
                        dbc.Collapse(
                            dbc.Nav(
                                [],
                                className="ml-auto",
                                navbar=True,
                            ),
                            id="navbar-collapse",
                            navbar=True,
                        ),
                    ]
                ),
                align="center",
            ),
        ],
        fluid=True,
    ),
    color="dark",
    dark=True,
)

# Query area
# Diagnosis
diagnoses = [{'label': label, 'value': key}
             for label, key in [('Parkinson', 'http://purl.bioontology.org/ontology/SNOMEDCT/49049000'),
                                ('Depression', 'http://purl.bioontology.org/ontology/SNOMEDCT/712823008')]]
diag_drop = dcc.Dropdown(
    id="diag_drop",
    options=diagnoses,
    value=None,
)

# Diagnosis
genders = [{'label': label, 'value': key}
           for label, key in [('Male', 'male'), ('Female', 'female')]]
gender_drop = dcc.Dropdown(
    id="gender_drop",
    options=genders,
    value=None,
)

# Modality
modalities = [{'label': label, 'value': key}
           for label, key in [('Flow weighted MRI', 'nidm:FlowWeighted'),
                              ('T1 weighted MRI', 'nidm:T1Weighted'),
                              ('Diffusion weighted MRI', 'nidm:DiffusionWeighted'),
                              ('T2 weighted MRI', 'nidm:T2Weighted')]]
modality_drop = dcc.Dropdown(
    id="modality_drop",
    options=modalities,
    value=None
)

input_groups = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(dcc.Input(placeholder="min age", type="number", id='min_age', style={"width": "100%"}), md=5),
                dbc.Col(html.P(" - "), md=2),
                dbc.Col(dcc.Input(placeholder="max age", type="number", id='max_age', style={"width": "100%"}), md=5),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(html.P("Modality")),
                dbc.Col(modality_drop, md=9)
            ],
            className="ml-auto",
        ),
        dbc.Row(
            [
                dbc.Col(html.P("Gender")),
                dbc.Col(gender_drop, md=9)
            ],
        ),
        dbc.Row(
            [
                dbc.Col(html.P("Diagnosis")),
                dbc.Col(diag_drop, md=9)
            ],
            className="md-9",
        ),
    ]
)

# Query Card
query_card = dbc.Card(
    [
        dbc.CardHeader(html.H2("Define cohort criteria")),
        dbc.CardBody(
            dbc.Row(
                dbc.Col(input_groups, md=12)
            )
        ),
        dbc.CardFooter(
            dbc.Row(
                [
                    dbc.Col(dbc.Row(
                        [
                            dbc.Col(),
                            dbc.Col(dbc.Button("Run Query", id='query_button', color="primary", className='ml-auto')),
                            dcc.Store(id='query_str'),
                        ]
                    )
                    ),
                ],
                align="center",
            ),
        ),
    ]
)

# Result Card
results_card = dbc.Card(
    [
    dbc.Row([html.P('Results Markdown dump:'), html.Pre(id='results_space')]),
    dbc.Row([html.P('Sparql Query'), html.Pre(id='query_space')])
]
)

# DataTable for results
table_card = dbc.Card(
    [
        dbc.CardHeader(html.H2("Data Table")),
        dbc.CardBody(
            dbc.Row(
                dbc.Col(
                    [
                        dash_table.DataTable(
                            id="table-results",
                            columns=([{'id': 'Index', 'name': 'Index'}] + columns),
                            data=[dict(Index=i, **{category: 0 for category in categories})
                                  for i in range(1, 3)],
                            style_header={
                                "textDecoration": "underline",
                                "textDecorationStyle": "dotted",
                            },
                            tooltip_delay=0,
                            tooltip_duration=None,
                            filter_action="native",
                            column_selectable="multi",
                            selected_columns=['hello'],
                            style_table={"overflowY": "scroll", 'height': '300px'},
                            fixed_rows={"headers": False, "data": 0},
                            style_cell={'overflow': 'hidden', 'textOverflow': 'ellipsis', 'maxWidth': 10},
                            page_size=30,
                        ),
                        html.Div(id="row", hidden=True, children=None),
                    ]
                )
            )
        ),
    ]
)

app.layout = html.Div(
    [
        header,
        dbc.Container(
            [
                dbc.Row([dbc.Col(query_card, md=3), dbc.Col(table_card, md=7)]),
                dbc.Row([dbc.Col(), dbc.Col([results_card], md=7), dbc.Col()])
            ],
            fluid=True,
        ),
    ]
)


@app.callback(
    [Output("query_str", "data"), Output("query_space", "children")],
    [Input("query_button", "n_clicks")],
    [
        State("min_age", "value"),
        State("max_age", "value"),
        State("diag_drop", "value"),
        State("gender_drop", "value"),
        State("modality_drop", "value"),
     ],
)
def parse_query(query_btn, min_age, max_age, diag, gender, modality):
    if query_btn:
        query = create_query((min_age, max_age), gender, modality, diag)
        return query, query


@app.callback(
    [Output("results_space", "children"), Output("table-results", "data")],
    Input("query_str", "data"),
    prevent_initial_call=True,
)
def run_query(query_str):
    remap = {'image': 'Modality',
             'gender': 'Gender',
             'siri': 'Subject',
             'open_neuro_id': 'Dataset',
             'age': 'Age',
             'diagnosis': 'Diagnosis'
    }
    df = pd.DataFrame(process_query(query_str)).rename(columns=remap)
    return (df.head().to_markdown(), df.to_dict("records"))


if __name__ == "__main__":
    app.run_server(debug=True)