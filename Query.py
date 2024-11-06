import os

import textwrap

# Langchain
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI

# Warning control
import warnings
warnings.filterwarnings("ignore")
import os
NEO4J_URI = 'neo4j+s://1630ec5e.databases.neo4j.io'
NEO4J_USERNAME = 'neo4j'
NEO4J_PASSWORD = 'xcXJQxaIyPazmgU0tpFCypLrS0lg-_W0M6Qil33QJlM'
NEO4J_DATABASE = 'neo4j'
OPENAI_API_KEY = os.getenv("API_GPT_YEU")

kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
)
kg.refresh_schema()
CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher statement to 
query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema. Do not use any other relationship types or properties that are not provided.

Schema:
{schema}

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
When querying, use 'CONTAINS' with relevant keywords to find matching nodes and relationships rather than directly querying names or type except Visa.
If additional information (like cost, description, or requirement) is needed, search for related nodes with corresponding types as label and return the required data 
Using `OR` to expand the search across relevant nodes and relationships.
Relationship has a lot of variation, recommend using CONTAINS or query all relation

Examples: Here are a few examples of generated Cypher statements for particular questions:
# How much money is required to apply for an eVisitor visa?
MATCH (v:Visa)-[r]->(c:Cost)
WHERE TOLOWER(v.name) CONTAINS TOLOWER("eVisitor")
AND LOWER(type(r)) CONTAINS LOWER("cost")
RETURN c.name

# list all visa description??
MATCH (v:Visa)-[r]->(d:Description)
WHERE LOWER(type(r))=LOWER("description")
OR LOWER(type(r))=LOWER("has_description")
OR LOWER(type(r))=LOWER("describes")   
OR LOWER(type(r))=LOWER("described_as")
OR LOWER(type(r))=LOWER("described_by")   
RETURN v.name, d.name

or this cypher statements

MATCH (v:Visa)-[r]->(d:Description)
RETURN v.name, d.name

#How long can a Parent visa holder stay in Australia?
MATCH (v:Visa)-[r]->(c)
WHERE LOWER(v.name) CONTAINS LOWER("parent")
AND (LOWER(c.name) CONTAINS LOWER("stay")
OR LOWER(type(r)) CONTAINS LOWER("stay"))
RETURN v.name,type(r),c.name

The question is:
{question}"""
CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)
chat_model_1 = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
chat_model_2 = ChatOpenAI(temperature=0.7, openai_api_key=OPENAI_API_KEY)
cypherChain = GraphCypherQAChain.from_llm(
    cypher_llm = chat_model_1,
    qa_llm = chat_model_2,
    graph=kg,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    allow_dangerous_requests=True
)
def prettyCypherChain(question):
    response = cypherChain.run(question)
    # print(textwrap.fill(response, 60))
    return response
