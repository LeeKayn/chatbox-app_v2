import os
from flask import make_response,Flask, render_template, flash, request, jsonify, redirect, url_for, session, render_template_string
import pickle
import networkx as nx
from pyvis.network import Network
import requests
import openai
from neo4j import GraphDatabase
from build_graph import build_new_graph,undo_knowledge_graph,merge_new_graph
from Query import prettyCypherChain

app = Flask(__name__)
openai.api_key = os.getenv("API_GPT_YEU")
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")  # Required for session management
users = {
    "admin": "admin123",  # username: password
    "user": "user123"
}

NEO4J_URI = 'neo4j+s://1630ec5e.databases.neo4j.io'
NEO4J_USERNAME = 'neo4j'
NEO4J_PASSWORD = 'xcXJQxaIyPazmgU0tpFCypLrS0lg-_W0M6Qil33QJlM'
NEO4J_DATABASE = 'neo4j'

# Create a Neo4j graph object
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

@app.route('/cypher', methods=['POST'])
def execute_cypher_query():
    query = request.form['query']
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query)
            response = '\n'.join([str(record) for record in result])
        print(response)
        return response
    except Exception as e:
        return f"Error executing Cypher query: {str(e)}", 500

# Home page that displays login options
@app.route('/')
def index():
    return render_template('login.html')


# Handle login logic
@app.route('/login', methods=['POST'])
def login():
    # Check if user selected 'Login as Guest' button
    login_as_guest = request.form.get('guest_login', False)

    if login_as_guest:
        session['user_role'] = 'guest'
        return redirect(url_for('chat_user'))  # Redirect to chat_user.html for guest login

    # For normal login (you can replace this logic with real authentication)
    username = request.form['username']
    password = request.form['password']

    if username == "admin" and password == "password":  # Example admin credentials
        session['user_role'] = 'admin'
        return redirect(url_for('chat'))  # Redirect to chat.html for admin login

    if username == "user" and password == "password":  # Example user credentials
        session['user_role'] = 'user'
        return redirect(url_for('chat'))  # Redirect to chat.html for user login

    # If login fails, flash an error message and redirect back to login page
    flash('Invalid username or password. Please try again.', 'error')
    return redirect(url_for('index'))  # Redirect back to the login page


# Chat page for authenticated users and admins
@app.route('/chat')
def chat():
    if 'user_role' not in session or session['user_role'] == 'guest':
        return redirect(url_for('index'))  # Ensure only logged-in users can access

    return render_template('chat.html')


# Chat page for guest users
@app.route('/chat_user')
def chat_user():
    if 'user_role' not in session or session['user_role'] != 'guest':
        return redirect(url_for('index'))  # Ensure only guests can access

    return render_template('chat_user.html')


# Handle the chat request
@app.route('/get', methods=['GET', 'POST'])
def chat_response():
    msg = request.form["msg"]
    response_text = get_Chat_response(msg)
    return response_text

@app.route('/merge', methods=['POST'])
def merge_action():
    merge_new_graph()
    # Load the updated knowledge graph data
    file_path = 'knowledge_graph.pkl'
    with open(file_path, 'rb') as file:
        data = pickle.load(file)

    entities = data.entities
    relationships = data.relationships

    # Create a directed graph with NetworkX
    G = nx.DiGraph()

    # Add nodes (entities) with only the name as tooltip
    for entity in entities:
        tooltip_text = f"Name: {entity.name}"
        G.add_node(entity.name, title=tooltip_text, label=entity.label)

    # Add edges (relationships) between entities
    for relationship in relationships:
        G.add_edge(relationship.startEntity.name, relationship.endEntity.name, label=relationship.name)

    # Display the graph using Pyvis
    net = Network(notebook=True, width="100%", height="750px", directed=True)

    # Import nodes and edges from the NetworkX graph into Pyvis
    net.from_nx(G)

    # Set options for the graph layout and interactions
    options = """
    {
        "physics": {
            "enabled": true,
            "repulsion": {
                "distance": 100,
                "multiplier": 1
            },
            "hierarchicalRepulsion": {
                "nodeDistance": 350
            },
            "solver": "repulsion",
            "stabilization": {
                "enabled": false
            }
        },
        "manipulation": {
            "enabled": true,
            "addNode": false,
            "addEdge": false,
            "deleteNode": false,
            "deleteEdge": false,
            "editNode": {
                "label": true,
                "size": true
            },
            "editEdge": {
                "label": true,
                "length": true
            }
        }
    }
    """

    net.set_options(options)

    # Generate HTML content as a string
    html_content = net.generate_html()

    # Return the generated HTML directly
    return jsonify({"message": "Merge action completed successfully!", "graph_html": html_content})

@app.route('/undo', methods=['POST'])
def undo_action():
    undo_knowledge_graph()
    file_path = 'knowledge_graph_user.pkl'
    with open(file_path, 'rb') as file:
        data = pickle.load(file)

    entities = data.entities
    relationships = data.relationships

    # Create a directed graph with NetworkX
    G = nx.DiGraph()

    # Add nodes (entities) with only the name as tooltip
    for entity in entities:
        tooltip_text = f"Name: {entity.name}"
        G.add_node(entity.name, title=tooltip_text, label=entity.label)

    # Add edges (relationships) between entities
    for relationship in relationships:
        G.add_edge(relationship.startEntity.name, relationship.endEntity.name, label=relationship.name)

    # Display the graph using Pyvis
    net = Network(notebook=True, width="100%", height="750px", directed=True)

    # Import nodes and edges from the NetworkX graph into Pyvis
    net.from_nx(G)

    # Set options for the graph layout and interactions
    options = """
        {
            "physics": {
                "enabled": true,
                "repulsion": {
                    "distance": 100,
                    "multiplier": 1
                },
                "hierarchicalRepulsion": {
                    "nodeDistance": 350
                },
                "solver": "repulsion",
                "stabilization": {
                    "enabled": false
                }
            },
            "manipulation": {
                "enabled": true,
                "addNode": false,
                "addEdge": false,
                "deleteNode": false,
                "deleteEdge": false,
                "editNode": {
                    "label": true,
                    "size": true
                },
                "editEdge": {
                    "label": true,
                    "length": true
                }
            }
        }
        """

    net.set_options(options)

    # Generate HTML content as a string
    html_content = net.generate_html()

    # Return the generated HTML directly
    return jsonify({"message": "Merge action completed successfully!", "graph_html": html_content})


def get_Chat_response(text):
    try:
        # Replace the OpenAI API call with prettylanghcain function
        response = prettyCypherChain(text)

        # If the response is expected to be a string, return it
        if response:
            return response
        else:
            return "Unexpected response format or missing content."

    except Exception as e:
        return f"An error occurred: {e}"



@app.route('/visualize')
def visualize_knowledge_graph():
    # Load the knowledge graph data
    file_path = 'knowledge_graph.pkl'  # Updated file path
    with open(file_path, 'rb') as file:
        data = pickle.load(file)

    entities = data.entities
    relationships = data.relationships

    # Create a directed graph with NetworkX
    G = nx.DiGraph()

    # Add nodes (entities) with only the name as tooltip
    for entity in entities:
        tooltip_text = f"Name: {entity.name}"
        G.add_node(entity.name, title=tooltip_text, label=entity.label)

    # Add edges (relationships) between entities
    for relationship in relationships:
        G.add_edge(relationship.startEntity.name, relationship.endEntity.name, label=relationship.name)

    # Display the graph using Pyvis
    net = Network(notebook=True, width="100%", height="750px", directed=True)

    # Import nodes and edges from the NetworkX graph into Pyvis
    net.from_nx(G)

    # Set options for the graph layout and interactions
    options = """
    {
        "physics": {
            "enabled": true,
            "repulsion": {
                "distance": 100,
                "multiplier": 1
            },
            "hierarchicalRepulsion": {
                "nodeDistance": 350
            },
            "solver": "repulsion",
            "stabilization": {
                "enabled": false
            }
        },
        "manipulation": {
            "enabled": true,
            "addNode": false,
            "addEdge": false,
            "deleteNode": false,
            "deleteEdge": false,
            "editNode": {
                "label": true,
                "size": true
            },
            "editEdge": {
                "label": true,
                "length": true
            }
        }
    }
    """

    net.set_options(options)

    # Generate HTML content as a string
    html_content = net.generate_html()

    # Return the generated HTML directly
    return render_template_string(html_content)


@app.route('/upload_file', methods=['POST'])
def handle_file_upload():
    file = request.files['file']
    content = file.read().decode('utf-8')
    file_path = 'data/input.txt'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    build_new_graph()
    file_path = 'knowledge_graph_user.pkl'
    with open(file_path, 'rb') as file:
        data = pickle.load(file)

    entities = data.entities
    relationships = data.relationships

    # Create a directed graph with NetworkX
    G = nx.DiGraph()

    # Add nodes (entities) with only the name as tooltip
    for entity in entities:
        tooltip_text = f"Name: {entity.name}"
        G.add_node(entity.name, title=tooltip_text, label=entity.label)

    # Add edges (relationships) between entities
    for relationship in relationships:
        G.add_edge(relationship.startEntity.name, relationship.endEntity.name, label=relationship.name)

    # Display the graph using Pyvis
    net_2 = Network(notebook=True, width="100%", height="750px", directed=True)

    # Import nodes and edges from the NetworkX graph into Pyvis
    net_2.from_nx(G)

    # Set options for the graph layout and interactions
    options = """
    {
        "physics": {
            "enabled": true,
            "repulsion": {
                "distance": 100,
                "multiplier": 1
            },
            "hierarchicalRepulsion": {
                "nodeDistance": 350
            },
            "solver": "repulsion",
            "stabilization": {
                "enabled": false
            }
        },
        "manipulation": {
            "enabled": true,
            "addNode": false,
            "addEdge": false,
            "deleteNode": false,
            "deleteEdge": false,
            "editNode": {
                "label": true,
                "size": true
            },
            "editEdge": {
                "label": true,
                "length": true
            }
        }
    }
    """

    net_2.set_options(options)

    # Generate HTML content as a string
    html_content = net_2.generate_html()

    # Return the generated HTML directly
    response = make_response(jsonify({'graph_html': html_content}))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/view_kg_steps', methods=['GET'])
def view_kg_steps():
    try:
        with open('data/output.txt', 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
