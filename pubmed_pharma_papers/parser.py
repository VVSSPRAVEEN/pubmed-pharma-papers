"""
Module for parsing PubMed paper data and identifying pharmaceutical/biotech affiliations.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set

# Configure logging
logger = logging.getLogger(__name__)

# Patterns for identifying academic and company affiliations
ACADEMIC_PATTERNS = [
    r"university", r"college", r"school", r"institute", r"academy",
    r"hospital", r"clinic", r"medical center", r"centre", r"laboratory",
    r"national", r"federal", r"ministry", r"department of health"
]

COMPANY_PATTERNS = [
    r"inc\b", r"corp\b", r"llc\b", r"ltd\b", r"limited\b", r"gmbh\b", r"co\b",
    r"pharma", r"biotech", r"therapeutics", r"biosciences", r"pharmaceuticals",
    r"biopharma", r"laboratories", r"diagnostics", r"technologies", r"company",
    r"novartis", r"pfizer", r"merck", r"roche", r"sanofi", r"astrazeneca", 
    r"johnson & johnson", r"abbvie", r"gilead", r"amgen", r"gsk", r"bayer",
    r"bristol-myers", r"lilly", r"boehringer", r"takeda", r"novo nordisk",
    r"biogen", r"celgene", r"regeneron", r"vertex", r"alexion", r"incyte"
]

# Academic email domains
ACADEMIC_EMAIL_DOMAINS = [
    ".edu", ".ac.", "university", "college", "institute", "school", "gov"
]

def extract_publication_date(article: Dict[str, Any]) -> str:
    """
    Extract the publication date from a PubMed article.
    
    Args:
        article: PubMed article data
        
    Returns:
        Publication date as a string (YYYY-MM-DD)
    """
    try:
        article_data = article.get("MedlineCitation", {}).get("Article", {})
        
        # Try to get the publication date
        pub_date = None
        
        # First try ArticleDate
        if "ArticleDate" in article_data and article_data["ArticleDate"]:
            try:
                date_info = article_data["ArticleDate"][0]
                year = date_info.get("Year", "")
                month = date_info.get("Month", "01")
                day = date_info.get("Day", "01")
                
                # Ensure month and day are two digits
                month = month.zfill(2) if isinstance(month, str) else f"{month:02d}"
                day = day.zfill(2) if isinstance(day, str) else f"{day:02d}"
                
                pub_date = f"{year}-{month}-{day}" if year else None
            except (IndexError, KeyError, AttributeError) as e:
                logger.debug(f"Could not extract ArticleDate: {e}")
        
        # Then try PubDate in Journal
        if not pub_date and "Journal" in article_data:
            if "PubDate" in article_data["Journal"]:
                try:
                    date_info = article_data["Journal"]["PubDate"]
                    year = date_info.get("Year", "")
                    
                    # Handle different date formats
                    if "Month" in date_info:
                        month = date_info.get("Month", "01")
                    elif "MedlineDate" in date_info:
                        # Try to extract month from MedlineDate (format varies)
                        medline_date = date_info.get("MedlineDate", "")
                        if medline_date and len(medline_date) >= 4:
                            year = medline_date[:4]
                            month = "01"  # Default to January if can't parse
                            if len(medline_date) > 5 and "-" in medline_date:
                                parts = medline_date.split("-")
                                if len(parts) > 1 and parts[1].isdigit():
                                    month = parts[1].zfill(2)
                    else:
                        month = "01"  # Default to January
                    
                    day = date_info.get("Day", "01")
                    
                    # Ensure month and day are two digits
                    month = month.zfill(2) if isinstance(month, str) else f"{month:02d}"
                    day = day.zfill(2) if isinstance(day, str) else f"{day:02d}"
                    
                    pub_date = f"{year}-{month}-{day}" if year else None
                except (KeyError, AttributeError) as e:
                    logger.debug(f"Could not extract PubDate: {e}")
        
        # Last resort: try to get year from PubMed entry date
        if not pub_date:
            try:
                date_created = article.get("MedlineCitation", {}).get("DateCreated", {})
                if date_created:
                    year = date_created.get("Year", "")
                    month = date_created.get("Month", "01")
                    day = date_created.get("Day", "01")
                    
                    # Ensure month and day are two digits
                    month = month.zfill(2) if isinstance(month, str) else f"{month:02d}"
                    day = day.zfill(2) if isinstance(day, str) else f"{day:02d}"
                    
                    pub_date = f"{year}-{month}-{day}" if year else None
            except (KeyError, AttributeError) as e:
                logger.debug(f"Could not extract DateCreated: {e}")
        
        return pub_date or "Unknown"
    
    except Exception as e:
        logger.error(f"Error extracting publication date: {e}")
        return "Unknown"

def extract_title(article: Dict[str, Any]) -> str:
    """
    Extract the title from a PubMed article.
    
    Args:
        article: PubMed article data
        
    Returns:
        Title of the article
    """
    try:
        return article.get("MedlineCitation", {}).get("Article", {}).get("ArticleTitle", "Unknown")
    except Exception as e:
        logger.error(f"Error extracting title: {e}")
        return "Unknown"

def is_company_affiliation(affiliation: str) -> bool:
    """
    Determine if an affiliation is from a pharmaceutical/biotech company.
    
    Args:
        affiliation: Affiliation text
        
    Returns:
        True if the affiliation is from a company, False otherwise
    """
    # If no affiliation text, return False
    if not affiliation:
        return False
        
    # Convert to lowercase for case-insensitive matching
    affiliation_lower = affiliation.lower()
    
    # Strong indicators of academic institutions (exclusion)
    strong_academic = [
        r"\buniversity\b", r"\bcollege\b", r"\bschool\b", 
        r"\binstitute\b", r"\bacademy\b", r"\bhospital\b"
    ]
    
    for pattern in strong_academic:
        if re.search(pattern, affiliation_lower):
            return False
    
    # Strong indicators of companies
    strong_company = [
        r"\binc\b", r"\bcorp\b", r"\bllc\b", r"\bltd\b", r"\blimited\b", 
        r"\bgmbh\b", r"\bco\b", r"\bcompany\b", r"\bpharma\b", r"\bbiotech\b"
    ]
    
    for pattern in strong_company:
        if re.search(pattern, affiliation_lower):
            return True
    
    # Check for specific company names
    company_names = [
        r"novartis", r"pfizer", r"merck", r"roche", r"sanofi", r"astrazeneca", 
        r"johnson & johnson", r"abbvie", r"gilead", r"amgen", r"gsk", r"bayer",
        r"bristol-myers", r"lilly", r"boehringer", r"takeda", r"novo nordisk",
        r"biogen", r"celgene", r"regeneron", r"vertex", r"alexion", r"incyte",
        r"janssen", r"moderna", r"biontech", r"curevac", r"genentech"
    ]
    
    for company in company_names:
        if company in affiliation_lower:
            return True
    
    # Weaker indicators that might suggest a company
    weak_company = [
        r"therapeutics", r"biosciences", r"pharmaceuticals", r"biopharma", 
        r"laboratories", r"diagnostics", r"technologies", r"research center",
        r"r&d", r"research and development"
    ]
    
    # If we find weak company indicators AND no strong academic indicators
    for pattern in weak_company:
        if re.search(pattern, affiliation_lower):
            return True
    
    return False

def is_academic_email(email: str) -> bool:
    """
    Determine if an email is from an academic institution.
    
    Args:
        email: Email address
        
    Returns:
        True if the email is from an academic institution, False otherwise
    """
    email_lower = email.lower()
    
    for domain in ACADEMIC_EMAIL_DOMAINS:
        if domain in email_lower:
            return True
    
    return False

def extract_authors_info(article: Dict[str, Any]) -> Tuple[List[str], List[str], str]:
    """
    Extract information about non-academic authors from a PubMed article.
    
    Args:
        article: PubMed article data
        
    Returns:
        Tuple containing:
        - List of non-academic author names
        - List of company affiliations
        - Corresponding author email
    """
    non_academic_authors = []
    company_affiliations = set()
    corresponding_email = ""
    
    try:
        authors = article.get("MedlineCitation", {}).get("Article", {}).get("AuthorList", [])
        
        for author in authors:
            # Skip if not a valid author
            if not isinstance(author, dict):
                continue
                
            # Get author name
            last_name = author.get('LastName', '')
            fore_name = author.get('ForeName', '')
            
            if not last_name and not fore_name:
                continue
                
            author_name = f"{last_name}, {fore_name}".strip(", ")
            
            # Check affiliations
            affiliations = author.get("AffiliationInfo", [])
            is_company_author = False
            
            for affiliation_info in affiliations:
                if not isinstance(affiliation_info, dict):
                    continue
                    
                affiliation = affiliation_info.get("Affiliation", "")
                
                if affiliation and is_company_affiliation(affiliation):
                    is_company_author = True
                    company_affiliations.add(affiliation)
            
            # Check if this is a corresponding author
            if "Identifier" in author:
                identifiers = author["Identifier"]
                if not isinstance(identifiers, list):
                    identifiers = [identifiers]
                    
                for identifier in identifiers:
                    # Look for email
                    potential_email = str(identifier)
                    if "@" in potential_email and not is_academic_email(potential_email):
                        corresponding_email = potential_email
                        is_company_author = True
            
            if is_company_author and author_name:
                non_academic_authors.append(author_name)
        
        return non_academic_authors, list(company_affiliations), corresponding_email
    
    except Exception as e:
        logger.error(f"Error extracting author information: {e}")
        return [], [], ""

def parse_paper(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a PubMed article and extract relevant information.
    
    Args:
        article: PubMed article data
        
    Returns:
        Dictionary containing parsed paper information
    """
    try:
        pmid = article.get("MedlineCitation", {}).get("PMID", "Unknown")
        title = extract_title(article)
        publication_date = extract_publication_date(article)
        non_academic_authors, company_affiliations, corresponding_email = extract_authors_info(article)
        
        return {
            "PubmedID": pmid,
            "Title": title,
            "Publication Date": publication_date,
            "Non-academic Author(s)": "; ".join(non_academic_authors),
            "Company Affiliation(s)": "; ".join(company_affiliations),
            "Corresponding Author Email": corresponding_email
        }
    
    except Exception as e:
        logger.error(f"Error parsing paper: {e}")
        return {}