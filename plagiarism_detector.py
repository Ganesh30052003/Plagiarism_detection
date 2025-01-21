import requests
import difflib
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from PyPDF2 import PdfReader
import os
import time  # Import time module for timing functionality

# Online plagiarism checking using Google Custom Search API
def check_plagiarism_online(input_text):
    api_key = 'YOUR_API_KEY'  # Replace with your actual API key
    engine_id = 'YOUR_ENGINE_ID'  # Replace with your actual engine ID

    # Make a request to Google Custom Search API
    search_url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={engine_id}&q={input_text}"
    print(f"Searching for: {input_text[:100]}...")  # Log the search text
    response = requests.get(search_url)

    results = response.json()
    print(f"API Response: {results}")  # Log the full API response

    matches = []
    copied = False
    total_length = 0

    if 'items' in results:
        for item in results['items']:
            copied = True
            snippet = item['snippet']
            matches.append({
                'matching_text': snippet,
                'source': item['link']
            })
            total_length += len(snippet)

    # Calculate percentage of copied content
    percentage_copied = (total_length / len(input_text)) * 100 if len(input_text) > 0 else 0

    return {
        'copied': copied,
        'sources': matches,
        'percentage_copied': min(percentage_copied, 100)  # Ensure it does not exceed 100%
    }

def clean_text(text):
    # Replace multiple spaces and newlines with a single space to clean up text
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def lcs_length(text1, text2, min_length=20):
    """Compute LCS for texts greater than a certain threshold."""
    # Add logic for improved LCS with minimum length filtering
    pass  # Original LCS logic will go here, this is for demonstration

def filtered_lcs_check(file_list, target_file, cosine_threshold=20):

    """Check LCS only for files with cosine similarity above threshold."""
    filtered_files = [file for file in file_list if cosine_similarity(file, target_file) > cosine_threshold]
    # Original LCS checking on filtered_files
def _length(str1, str2):
    m = len(str1)
    n = len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Fill the dp array
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]

from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords

# Ensure you have the stopwords downloaded
import nltk
nltk.download('stopwords')

def cosine_similarity(text1, text2):
    # Get English stopwords from nltk
    stop_words = stopwords.words('english')
    
    # Initialize TfidfVectorizer with stopwords
    tfidf_vectorizer = TfidfVectorizer(stop_words=stop_words)
    
    # Fit and transform the texts
    tfidf_matrix = tfidf_vectorizer.fit_transform([text1, text2])
    
    # Calculate cosine similarity
    cosine_sim = (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]  # Fixed: use toarray()
    
    return cosine_sim * 100  # Convert to percentage


def check_plagiarism_offline(input_text, stored_files):
    best_match_file = None
    best_match_segments = []
    best_match_length = 0
    best_match_percentage = 0  # To track the best match percentage

    input_text_cleaned = clean_text(input_text)  # Clean the input text for consistent comparison
    sources = []

    for file in stored_files:
        pdf_text = extract_text_from_pdf(os.path.join('./stored_pdfs', file))
        pdf_text_cleaned = clean_text(pdf_text)  # Clean the PDF text for consistent comparison

        # Initialize SequenceMatcher
        matcher = difflib.SequenceMatcher(None, input_text_cleaned, pdf_text_cleaned)

        current_match_length = 0
        current_matches = []

        # Measure the time for string matching technique
        start_time_string_match = time.time()  # Start timing for string matching

        # Check if the normalized input text is exactly the same as the stored document
        if input_text_cleaned == pdf_text_cleaned:
            # 100% match if the documents are exactly the same
            string_match_percentage = 100.0
            time_taken_string_match = time.time() - start_time_string_match  # Calculate the time taken for string matching
            sources.append({
                'file': file,
                'matches': [input_text_cleaned],  # Store the entire text as the match
                'string_match': string_match_percentage,
                'time_taken_string_match': time_taken_string_match,  # Store time taken for string matching
                'copied_text': input_text_cleaned  # Add copied text for this perfect match
            })
            best_match_file = file
            best_match_length = len(input_text_cleaned)
            best_match_percentage = string_match_percentage  # Track the best match percentage
            best_match_segments = [input_text_cleaned]  # Store the best match segments
            continue  # Skip further checks since it's a perfect match

        # If not identical, proceed with the usual string matching logic
        for match in matcher.get_matching_blocks():
            if match.size > 1:  # Only consider matches larger than one character
                matching_text = pdf_text[match.b: match.b + match.size]
                cleaned_match = clean_text(matching_text)  # Clean up the matched text
                
                if len(cleaned_match) > 3:  # Only add meaningful matches longer than 3 characters
                    current_matches.append(cleaned_match)  # Store matched segment
                    current_match_length += len(cleaned_match)

        end_time_string_match = time.time()  # End timing for string matching
        time_taken_string_match = end_time_string_match - start_time_string_match  # Calculate the time taken for string matching

        # If any matches found, add to sources
        if current_match_length > 0:
            string_match_percentage = (current_match_length / len(input_text_cleaned)) * 100 if len(input_text_cleaned) > 0 else 0
            sources.append({
                'file': file,
                'matches': current_matches,  # Store all matched segments
                'string_match': string_match_percentage,
                'time_taken_string_match': time_taken_string_match,  # Store time taken for string matching
                'copied_text': "\n".join(list(set(current_matches)))  # Add copied text for this file
            })

            # Compare to find the file with the largest match
            if current_match_length > best_match_length:
                best_match_file = file
                best_match_length = current_match_length
                best_match_percentage = string_match_percentage  # Track the best match percentage
                best_match_segments = current_matches  # Store the current best match segments

    # If no significant matches found, return "No copied text found"
    if not sources or best_match_length == 0:
        return {
            'copied': False,
            'sources': [],
            'message': 'No copied text found'  # Message to be shown when no matches found
        }

    # Calculate LCS and Cosine Similarity for each source
    for source in sources:
        source_text = extract_text_from_pdf(os.path.join('./stored_pdfs', source['file']))
        
        # Measure the time for LCS technique
        start_time_lcs = time.time()  # Start timing for LCS
        lcs_score = lcs_length(input_text_cleaned, source_text) or 0

        end_time_lcs = time.time()  # End timing for LCS
        time_taken_lcs = end_time_lcs - start_time_lcs  # Calculate the time taken for LCS

        # Measure the time for Cosine Similarity technique
        start_time_cosine = time.time()  # Start timing for Cosine Similarity
        cosine_score = cosine_similarity(input_text_cleaned, source_text)
        end_time_cosine = time.time()  # End timing for Cosine Similarity
        time_taken_cosine = end_time_cosine - start_time_cosine  # Calculate the time taken for Cosine Similarity

        source['lcs'] = (lcs_score / len(input_text_cleaned)) * 100 if len(input_text_cleaned) > 0 else 0
        source['cosine_similarity'] = cosine_score
        source['time_taken_lcs'] = time_taken_lcs  # Store time taken for LCS
        source['time_taken_cosine'] = time_taken_cosine  # Store time taken for Cosine Similarity

    # Calculate the overall percentage of copied text
    overall_percentage_copied = (best_match_length / len(input_text_cleaned)) * 100 if len(input_text_cleaned) > 0 else 0

    return {
        'copied': True,
        'sources': sources,  # Return all sources with matched segments
        'percentage_copied': overall_percentage_copied,
        # Display total copied text only from the highest matched source
        'total_copied_text': "\n".join(list(set(best_match_segments)))  # Unchanged
    }

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ''
    for page in reader.pages:
        text += page.extract_text() or ''
    return text