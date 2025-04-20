"""
Command-line interface for the PubMed Pharma Papers package.
"""

import argparse
import logging
import os
import sys
from typing import List, Optional

from pubmed_pharma_papers.api import PubMedAPI
from pubmed_pharma_papers.parser import parse_paper
from pubmed_pharma_papers.utils import save_to_csv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Fetch research papers from PubMed with pharmaceutical/biotech company affiliations"
    )
    
    parser.add_argument(
        "query",
        help="PubMed search query"
    )
    
    parser.add_argument(
        "-f", "--file",
        help="Filename to save results (if not provided, print to console)",
        type=str
    )
    
    parser.add_argument(
        "-d", "--debug",
        help="Enable debug logging",
        action="store_true"
    )
    
    parser.add_argument(
        "-m", "--max-results",
        help="Maximum number of results to return (default: 100)",
        type=int,
        default=100
    )
    
    parser.add_argument(
        "-k", "--api-key",
        help="PubMed API key (can also be set via PUBMED_API_KEY environment variable)",
        type=str
    )
    
    return parser.parse_args()

def main() -> None:
    """
    Main entry point for the command-line interface.
    """
    # Parse arguments
    args = parse_args()
    
    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    try:
        # Get API key from args or environment
        api_key = args.api_key or os.environ.get("PUBMED_API_KEY")
        
        # Initialize API client
        api = PubMedAPI(api_key=api_key, debug=args.debug)
        
        # Search for papers
        logger.info(f"Searching PubMed for: {args.query}")
        pmids = api.search_papers(args.query, max_results=args.max_results)
        
        if not pmids:
            logger.info("No papers found matching the query")
            return
        
        logger.info(f"Found {len(pmids)} papers matching the query")
        
        # Fetch paper details
        papers_data = api.fetch_papers_batch(pmids)
        
        # Parse papers and filter for those with pharmaceutical/biotech affiliations
        parsed_papers = []
        all_affiliations = []  
        for paper in papers_data:
            # Add these debug lines
            if args.debug:
                article_data = paper.get("MedlineCitation", {}).get("Article", {})
                authors = article_data.get("AuthorList", [])
                logger.debug(f"Processing paper: {article_data.get('ArticleTitle', 'Unknown')}")
                
                for author in authors:
                    affiliations = author.get("AffiliationInfo", [])
                    for affiliation_info in affiliations:
                        affiliation = affiliation_info.get("Affiliation", "")
                        if affiliation:
                            all_affiliations.append(affiliation)
                            logger.debug(f"Found affiliation: {affiliation}")
            
            parsed_paper = parse_paper(paper)
            
            # Only include papers with non-academic authors
            if parsed_paper.get("Non-academic Author(s)"):
                parsed_papers.append(parsed_paper)
        # If no papers with company affiliations were found, include all papers as a fallback
        if not parsed_papers and papers_data:
            logger.warning("No papers with pharmaceutical/biotech affiliations found. Including all papers as fallback.")
            for paper in papers_data:
                parsed_paper = parse_paper(paper)
                parsed_papers.append(parsed_paper)
        if args.debug and not parsed_papers:
            logger.debug("No papers with company affiliations found. Sample of affiliations:")
            for i, affiliation in enumerate(all_affiliations[:10]):  # Show first 10
                logger.debug(f"  {i+1}. {affiliation}")
        
        logger.info(f"Found {len(parsed_papers)} papers with pharmaceutical/biotech affiliations")
        
        # Save results
        save_to_csv(parsed_papers, args.file)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()