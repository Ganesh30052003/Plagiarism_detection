from flask import Flask, request, jsonify, render_template
import os
from plagiarism_detector import check_plagiarism_offline, extract_text_from_pdf

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)
