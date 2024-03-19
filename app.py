from flask import Flask, request, jsonify
import logging
from utils.pipeline import runPipelineForJD, runPipelineForResume
from utils.vectorSearch import getResumeBestMatch, getJDBestMatch
from utils.pingService import returnHealth

app = Flask(__name__)

# Configure logging
def setup_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(log_format))
    app.logger.addHandler(handler)

# Setup logging when the app starts
setup_logging()

@app.route('/search', methods=['POST'])
def search():
    app.logger.info('search endpoint accessed: /')
    # Check if request contains JSON data
    if not request.is_json:
        return jsonify({'error': 'Request must be in JSON format'}), 400

    # Parse JSON data
    data = request.json

    # Check if all parameters are present
    required_params = ['context', 'category', 'threshold', 'noOfMatches', 'inputPath']
    for param in required_params:
        if param not in data:
            return jsonify({'error': f'Missing parameter: {param}'}), 400

    # Validate threshold value
    threshold = data['threshold']
    if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
        return jsonify({'error': 'Threshold must be a float between 0 and 1'}), 400

    # if no_of_matches <= 0:
    #     return jsonify({'status': 'success', 'message': 'No results found'}), 200
    # Extract input parameters
    context = data['context']
    category = data['category']
    no_of_matches = data['noOfMatches']
    input_path = data['inputPath']

    # Check if category is valid
    if category not in ['resume', 'job']:
        return jsonify({'status': 'Bad Request', 'message': 'Please check category should be either resume or job!'}), 400
    
    results = None
    if category == "resume":
        runPipelineForResume(input_path)
        results = getResumeBestMatch(context, no_of_matches)
    else:
        runPipelineForJD(input_path)
        results = getJDBestMatch(context, no_of_matches)   
    
    jsonResult = []
    
    loopLength = min(no_of_matches, len(results))
    # Process the data
    j = 1
    for i in range(loopLength):
        path = results[i][0]
        score = float(results[i][1])

        if score >= threshold:
            jsonResult.append({
                'id': j,
                'score': score,
                'path': f'{path}'
            }) 
            j += 1       

    # Prepare output JSON
    output = {
        'status': 'success',
        'count': no_of_matches,
        'metadata': {
            'confidenceScore': threshold
        },
        'results': jsonResult
    }

    return jsonify(output), 200

@app.route('/ping', methods=['GET'])
def ping():
    app.logger.info('ping endpoint accessed: /')
    return jsonify(returnHealth()), 200
    
if __name__ == '__main__':
    app.run(debug=True)
