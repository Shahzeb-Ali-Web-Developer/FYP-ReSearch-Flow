from neo4j import GraphDatabase
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jClient:
    """Neo4j database client singleton"""
    
    _instance = None
    _driver = None
    _connected = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self):
        """Connect to Neo4j"""
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                # Test connection
                with self._driver.session() as session:
                    result = session.run("RETURN 1 AS test")
                    result.single()
                
                self._connected = True
                logger.info("[OK] Connected to Neo4j")
            except Exception as e:
                logger.warning(f"[WARN] Neo4j connection failed: {e}")
                logger.warning("Citation mesh will use fallback mode (OpenAlex API)")
                self._driver = None
                self._connected = False
    
    def disconnect(self):
        """Disconnect from Neo4j"""
        if self._driver:
            self._driver.close()
            self._connected = False
            logger.info("[OK] Disconnected from Neo4j")
    
    def get_driver(self):
        """Get Neo4j driver"""
        return self._driver
    
    def is_connected(self):
        """Check if connected to Neo4j"""
        return self._connected
    
    def execute_query(self, query: str, parameters: dict = None):
        """
        Execute Cypher query and return results
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result dictionaries
        """
        if not self._driver:
            raise Exception("Neo4j not connected")
        
        with self._driver.session(database=settings.NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def execute_write(self, query: str, parameters: dict = None):
        """
        Execute write transaction
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            Result of the write operation
        """
        if not self._driver:
            raise Exception("Neo4j not connected")
        
        def _write_tx(tx, query, params):
            result = tx.run(query, params)
            return [record.data() for record in result]
        
        with self._driver.session(database=settings.NEO4J_DATABASE) as session:
            return session.execute_write(_write_tx, query, parameters or {})

# Global instance
neo4j_client = Neo4jClient()

