"""
Script to download all required NLTK resources for the Review Scoring System.
Run this once before starting the application to ensure all resources are available.
"""

import nltk
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_nltk_resources():
    """Download all required NLTK resources."""
    resources = [
        'punkt',
        'stopwords',
        'punkt_tab'
    ]
    
    for resource in resources:
        try:
            logger.info(f"Checking for NLTK resource: {resource}")
            nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else f'corpora/{resource}')
            logger.info(f"Resource {resource} already exists.")
        except LookupError:
            logger.info(f"Downloading NLTK resource: {resource}")
            nltk.download(resource)
            logger.info(f"Downloaded {resource} successfully.")

if __name__ == "__main__":
    logger.info("Starting NLTK resource download...")
    download_nltk_resources()
    logger.info("All NLTK resources downloaded successfully!")
    print("\nNLTK resources are ready! You can now start the application.") 