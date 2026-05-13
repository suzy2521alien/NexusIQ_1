from neo4j import GraphDatabase

# Neo4j Aura credentials
URI = "neo4j+s://f75563b8.databases.neo4j.io"
USER = "f75563b8"
PASSWORD = "Yp5vFpFIbZJyCvV-SIWfjzEr0wE3_LQ_v3yHsaS-y7M"
DATABASE = "f75563b8"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def get_session():
    """Get a new Neo4j session"""
    return driver.session(database=DATABASE)

def close_driver():
    """Close the driver connection"""
    driver.close()
