"""
Module for interacting with the PubMed API to fetch research papers.
"""

import logging
import os
from typing import Dict, List, Optional, Any

from Bio import Entrez

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PubMedAPI:
    """Class for interacting with the PubMed API."""
    
    def __init__(self, 
                 email: str = "jampanasaipraveen@gmail.com", 
                 tool: str = "pubmed-pharma-papers", 
                 api_key: Optional[str] = "bc837ea845b252dd3a95621ac873aa4a2f08",
                 debug: bool = False):
        """
        Initialize the PubMed API client.
        
        Args:
            email: Email to identify yourself to NCBI
            tool: Name of the tool
            api_key: NCBI API key (optional)
            debug: Whether to enable debug logging
        """
        self.email = email
        self.tool = tool
        self.api_key = api_key or os.environ.get("PUBMED_API_KEY")
        
        # Set up Entrez
        Entrez.email = email
        Entrez.tool = tool
        if self.api_key:
            Entrez.api_key = self.api_key
            logger.debug("Using PubMed API key")
        
        # Configure logging
        if debug:
            logger.setLevel(logging.DEBUG)
    
    def search_papers(self, query: str, max_results: int = 100) -> List[str]:
        """
        Search for papers matching the query.
        
        Args:
            query: PubMed search query
            max_results: Maximum number of results to return
            
        Returns:
            List of PubMed IDs matching the query
        """
        logger.debug(f"Searching PubMed with query: {query}")
        
        try:
            # Search PubMed
            handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=max_results,
                sort="relevance"
            )
            record = Entrez.read(handle)
            handle.close()
            
            # Extract IDs
            id_list = record["IdList"]
            logger.debug(f"Found {len(id_list)} papers matching the query")
            
            return id_list
        
        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            raise
    
    def fetch_paper_details(self, pmid: str) -> Dict[str, Any]:
        """
        Fetch detailed information for a paper by its PubMed ID.
        
        Args:
            pmid: PubMed ID of the paper
            
        Returns:
            Dictionary containing paper details
        """
        logger.debug(f"Fetching details for paper with ID: {pmid}")
        
        try:
            # Fetch paper details
            handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml")
            records = Entrez.read(handle)
            handle.close()
            
            if not records["PubmedArticle"]:
                logger.warning(f"No details found for paper with ID: {pmid}")
                return {}
            
            article = records["PubmedArticle"][0]
            return article
        
        except Exception as e:
            logger.error(f"Error fetching paper details: {e}")
            raise
    
    def fetch_papers_batch(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch details for multiple papers in a batch.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of dictionaries containing paper details
        """
        logger.debug(f"Fetching details for {len(pmids)} papers in batch")
        
        if not pmids:
            return []
        
        try:
            # Fetch papers in batch
            handle = Entrez.efetch(db="pubmed", id=",".join(pmids), retmode="xml")
            records = Entrez.read(handle)
            handle.close()
            
            papers = []
            for article in records.get("PubmedArticle", []):
                papers.append(article)
            
            logger.debug(f"Successfully fetched details for {len(papers)} papers")
            return papers
        
        except Exception as e:
            logger.error(f"Error fetching papers in batch: {e}")
            raise
