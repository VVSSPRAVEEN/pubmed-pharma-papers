"""
Utility functions for the PubMed Pharma Papers package.
"""

import logging
from typing import Dict, List, Optional, Any

import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

def save_to_csv(papers: List[Dict[str, Any]], filename: Optional[str] = None) -> None:
    """
    Save paper data to a CSV file or print to console.
    
    Args:
        papers: List of paper data dictionaries
        filename: Optional filename to save to (if None, print to console)
    """
    if not papers:
        logger.warning("No papers to save")
        return
    
    # Create DataFrame
    df = pd.DataFrame(papers)
    
    # Define columns order
    columns = [
        "PubmedID", "Title", "Publication Date", 
        "Non-academic Author(s)", "Company Affiliation(s)", 
        "Corresponding Author Email"
    ]
    
    # Reorder columns and filter out any that don't exist
    existing_columns = [col for col in columns if col in df.columns]
    df = df[existing_columns]
    
    if filename:
        # Save to file
        df.to_csv(filename, index=False)
        logger.info(f"Results saved to {filename}")
    else:
        # Print to console
        print(df.to_csv(index=False))