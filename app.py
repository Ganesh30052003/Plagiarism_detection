# from flask import Flask, request, jsonify, render_template
# import os
# from plagiarism_detector import check_plagiarism_offline, extract_text_from_pdf
import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from plagiarism_detector import check_plagiarism_online, check_plagiarism_offline

app = Flask(__name__)
# Define the upload folder path
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')  # Adjust the path as needed

# Create the uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/store_files', methods=['POST'])
def store_files():
    print("Store files route accessed")  # Debug statement
    files = request.files.getlist('files')
    
    if not os.path.exists('./stored_pdfs'):
        os.makedirs('./stored_pdfs')
    
    for file in files:
        print(f"Storing file: {file.filename}")  # Debug statement for stored file
        file.save(os.path.join('./stored_pdfs', file.filename))
    return jsonify({'message': 'Files stored successfully!'})

@app.route('/check_offline', methods=['POST'])
def check_offline():
    print("Check offline route accessed")  # Debug statement
    if 'file' not in request.files:
        print("No file part in the request")  # Debug statement
        return jsonify({"error": "No file uploaded"}), 400

    testing_file = request.files['file']
    if testing_file.filename == '':
        print("No selected file")  # Debug statement
        return jsonify({"error": "No selected file"}), 400

    testing_text = extract_text_from_pdf(testing_file)
    print(f"Extracted testing text: {testing_text[:100]}...")  # Debug output

    stored_files_path = './stored_pdfs'

    # Call the check_plagiarism_offline function and get results
    results = check_plagiarism_offline(testing_text, os.listdir(stored_files_path))

    print("Results:", results)  # Log results for debugging

    if results['copied']:
        overall_copied_percentage = results['percentage_copied']
        sources = results['sources']
        detailed_copied_texts = [{'file': source['file'], 'copied_text': source['copied_text']} for source in sources]

        return jsonify({
            'copied': True,
            'overall_copied_percentage': overall_copied_percentage,
            'results': sources,
            'detailed_copied_texts': detailed_copied_texts  # Provide detailed copied texts
        })

    return jsonify({'copied': False, 'message': "No matching sources found."})

# Route to check plagiarism online
@app.route('/check_online', methods=['POST'])
def check_online():
    text = request.form.get('text', '')
    upload_file = request.files.get('file')

    # If a file is uploaded, extract text from the PDF
    if upload_file:
        filename = secure_filename(upload_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        upload_file.save(filepath)
        text = extract_text_from_pdf(filepath)  # Use the text from the PDF

    print(f"Checking Online for Text: {text[:100]}...")  # Log the first 100 characters of the text for debugging

    # Check plagiarism using online sources
    online_results = check_plagiarism_online(text)
    print(f"Online Results: {online_results}")  # Log the results for debugging

    return jsonify(online_results)


def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ''
        for page in reader.pages:
            page_text = page.extract_text() or ''
            text += page_text
        print(f"Extracted Text from {file_path}: {text[:100]}...")  # Log the first 100 characters for debug
        return text
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")  # Log any errors
        return ''


if __name__ == '__main__':
    app.run(debug=True)
