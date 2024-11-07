from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from itext2kg.documents_distiller import DocumentsDistiller, Article
from pydantic import BaseModel, Field
from typing import List, Tuple, Optional
from itext2kg import iText2KG
import pickle
import json
import os
import sys
from io import StringIO
import io
openai_api_key = os.getenv("API_GPT_YEU")

openai_llm_model = llm = ChatOpenAI(
    api_key = openai_api_key,
    model="gpt-4o",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

openai_embeddings_model = OpenAIEmbeddings(
    api_key = openai_api_key ,
    model="text-embedding-3-large",
)


class VisaBaseModel(BaseModel):
    specific_streams: Optional[str] = Field(None, description="Specific streams or categories under the visa subclass. May specify if stream are allowed 'inside_Australia' or 'outside_Australia' then format: Tourist stream (inside_Australia)")
    visa_name: str = Field(..., description="The official name of the visa type and subclass, contains only name of visa and subclass , e.g., 'Electronic Travel Authority (subclass 600)'")

    description: Optional[str] = Field(None, description="General description of the visa, its purpose, and target audience")
    
    eligibility: Optional[List[str]] = Field(None, description="Eligibility requirements or restrictions for this visa type")
    benefits: Optional[List[str]] = Field(None, description="Benefits and permissions granted to visa holders, such as travel and study rights")
    obligations: Optional[List[str]] = Field(None, description="Obligations that visa holders must follow")
    cost: Optional[List[str]] = Field(None, description="Cost to apply for the visa, if any, and details of additional fees")
    
    processing_times: Optional[List[str]] = Field(None, description="Expected processing times for the application")
    apply_from: Optional[List[str]] = Field(None, description="Locations or conditions for applying (must be inside or outside Australia)")
    apply_in_australia: Optional[List[str]] = Field(None, description="Details on how to apply for the visa while in Australia")
    apply_outside_australia: Optional[List[str]] = Field(None, description="Details on how to apply for the visa from outside Australia")
    
    family_inclusion: Optional[List[str]] = Field(None, description="Conditions under which family members can be included")
    travel_rights: Optional[List[str]] = Field(None, description="Details on the number of entries and travel permissions")
    stay_duration: Optional[List[str]] = Field(None, description="Allowed length of stay in Australia for each entry")
    
    health_requirements: Optional[List[str]] = Field(None, description="Any health requirements for the visa, particularly for certain occupations")
    health_insurance: Optional[str] = Field(None, description="Recommendations or requirements for health insurance coverage")
    
    visa_label: Optional[str] = Field(None, description="Information about digital visa labels and passport linking")
    sponsorship_info: Optional[str] = Field(None, description="Details regarding sponsorship if applicable")
    
    additional_info: Optional[str] = Field(None, description="Any additional information relevant to the visa subclass")
    
    valid_for_new_zealanders: Optional[str] = Field(None, description="Information regarding eligibility for New Zealand citizens")
    includes_children: Optional[str] = Field(None, description="Information on including children in the visa application")
    
    processing_requirements: Optional[List[str]] = Field(None, description="Requirements for processing the visa application")
    questions_and_answers: Optional[List[str]] = Field(None, description="Commonly asked questions and their answers related to the visa")


# Sample input data as a list of triplets
# It is structured in this manner : (document's path, page_numbers_to_exclude, blueprint, document_type)


def upload_and_distill(documents_information: List[Tuple[str, List[int], BaseModel, str]]):
    distilled_docs = []
    stderr_capture = io.StringIO()
    sys.stderr = stderr_capture

    try:
        print("Uploading documents...", flush=True, file=sys.stderr)

        for path_, exclude_pages, blueprint, document_type in documents_information:
            if path_.endswith('.pdf'):
                loader = PyPDFLoader(path_)
                pages = loader.load_and_split()
                pages = [page for page in pages if page.metadata["page"] + 1 not in exclude_pages]
                documents = [page.page_content.replace("{", '[').replace("}", "]") for page in pages]
            elif path_.endswith('.txt'):
                with open(path_, 'r', encoding='utf-8') as file:
                    documents = ''.join([line.replace("{", '[').replace("}", "]") for line in file.readlines()])
                    documents = [documents]

            print(f"Processing document type: {document_type}", file=sys.stderr)
            print(documents, file=sys.stderr)
            document_distiller = DocumentsDistiller(llm_model=llm)
            print("Done embedding", file=sys.stderr)

            IE_query = '''
                # DIRECTIVES :
                - Act like an experienced information extractor.
                - Pay special attention to the subclass of the visa.
                - Extract all relevant information, especially focusing on subclass, including type of visa, duration, service charge, notification details, application advice, and any conditions.
                - If you do not find the right information, keep its place empty.
                '''

            print(IE_query, file=sys.stderr)
            print("Step 1: Starting distillation...", file=sys.stderr)
            distilled_doc = document_distiller.distill(
                documents=documents,
                IE_query=IE_query,
                output_data_structure=blueprint
            )
            print("Step 2: Distillation complete", file=sys.stderr)

            distilled_docs.append([
                f"{document_type}'s {key} - {value}".replace("{", "[").replace("}", "]")
                for key, value in distilled_doc.items()
                if value and value != []
            ])
    finally:
        sys.stderr = sys.__stderr__

    log_content = stderr_capture.getvalue()
    return distilled_docs, log_content

def build_new_graph():
    item_path="data/input.txt"
    documents_information = [(item_path, [], VisaBaseModel, 'visa information'),]

    distilled_docs,log_content = upload_and_distill(documents_information=documents_information)
    itext2kg = iText2KG(llm_model = openai_llm_model, embeddings_model = openai_embeddings_model)
    with open("data/output.txt", 'w', encoding='utf-8') as file:
        file.write(log_content)
    kg = itext2kg.build_graph(sections=distilled_docs, ent_threshold=0.9, rel_threshold=0.7,entity_name_weight=0.7, entity_label_weight= 0.3,max_tries_isolated_entities=3)
    with open('knowledge_graph_user.pkl', 'wb') as file:
            pickle.dump(kg, file)

    with open('distilled_docs.json', 'w', encoding='utf-8') as f:
        json.dump(distilled_docs, f, ensure_ascii=False, indent=4)
def merge_new_graph():
    with open('distilled_docs.json', 'r', encoding='utf-8') as f:
        distilled_docs = json.load(f)
    itext2kg = iText2KG(llm_model = openai_llm_model, embeddings_model = openai_embeddings_model)
    file_path = 'knowledge_graph.pkl'  # Change this to your actual file path
    
    # Load the knowledge graph from the file
    with open(file_path, 'rb') as file:
        kg_loaded = pickle.load(file)
    with open('knowledge_graph_undo.pkl', 'wb') as file:
            pickle.dump(kg_loaded, file)


    kg = itext2kg.build_graph(sections=distilled_docs,existing_knowledge_graph=kg_loaded, ent_threshold=0.9, rel_threshold=0.7,entity_name_weight=0.7, entity_label_weight= 0.3,max_tries_isolated_entities=3)
    with open('knowledge_graph.pkl', 'wb') as file:
            pickle.dump(kg, file)

    with open('distilled_docs.json', 'w', encoding='utf-8') as f:
        json.dump(distilled_docs, f, ensure_ascii=False, indent=4)
def undo_knowledge_graph():
    with open('knowledge_graph_undo.pkl', 'rb') as file:
        kg_undo = pickle.load(file)
    with open('knowledge_graph.pkl', 'wb') as file:
        pickle.dump(kg_undo, file)
    
    