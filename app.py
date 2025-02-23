import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from plagiarism_detector import check_plagiarism_online, check_plagiarism_offline

app = Flask(__name__)

# Dictionary to temporarily store uploaded PDF content
stored_pdfs = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/store_files', methods=['POST'])
def store_files():
    """Stores uploaded PDFs in memory instead of disk."""
    global stored_pdfs
    stored_pdfs.clear()  # Clear previously stored PDFs

    files = request.files.getlist('files')
    if not files:
        return jsonify({'message': 'No files uploaded'})

    for file in files:
        if file.filename.endswith('.pdf'):
            reader = PdfReader(file.stream)
            text = ''.join([page.extract_text() or '' for page in reader.pages])
            stored_pdfs[file.filename] = text  # Store file name and content

    return jsonify({'message': f'{len(stored_pdfs)} PDFs stored successfully for comparison'})

@app.route('/check_offline', methods=['POST'])
def check_offline():
    """Checks the uploaded PDF against temporarily stored PDFs."""
    if not stored_pdfs:
        return jsonify({'message': 'No stored files available for comparison'})

    file = request.files.get('file')

    if not file or not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Invalid or missing file'}), 400

    # Extract text from the uploaded test PDF
    reader = PdfReader(file.stream)
    input_text = ''.join([page.extract_text() or '' for page in reader.pages])

    # Call the plagiarism detection function
    results = check_plagiarism_offline(input_text, stored_pdfs)

    if results['copied']:
        return jsonify({
            'copied': True,
            'overall_copied_percentage': results['percentage_copied'],
            'results': results['sources'],
            'detailed_copied_texts': [{'file': source['file'], 'copied_text': source['copied_text']} for source in results['sources']]
        })

    return jsonify({'copied': False, 'message': "No matching sources found."})

@app.route('/check_online', methods=['POST'])
def check_online():
    """Performs online plagiarism detection."""
    text = request.form.get('text', '')
    upload_file = request.files.get('file')

    # If a file is uploaded, extract text from the PDF
    if upload_file:
        filename = secure_filename(upload_file.filename)
        upload_file.save(filename)  # Save temporarily
        text = extract_text_from_pdf(filename)  # Extract text
        os.remove(filename)  # Remove temporary file

    # Check plagiarism using online sources
    online_results = check_plagiarism_online(text)
    return jsonify(online_results)

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ''.join([page.extract_text() or '' for page in reader.pages])
        return text
    except Exception as e:
        return ''

if __name__ == '__main__':
    app.run(debug=True)
