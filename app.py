from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test():
    return "Hello This Works", 200

@app.route('/process', methods=['POST'])
def process():
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

    # Extract input parameters
    context = data['context']
    category = data['category']
    no_of_matches = data['noOfMatches']
    input_path = data['inputPath']

    # Mock processing logic
    results = []

    # Check if no results found
    if no_of_matches <= 0:
        return jsonify({'status': 'failure', 'message': 'No results found'}), 404

    # Process the data
    for i in range(1, no_of_matches + 1):
        results.append({
            'id': i,
            'score': threshold,
            'path': f'{i}.pdf'
        })

    # Prepare output JSON
    output = {
        'status': 'success',
        'count': no_of_matches,
        'metadata': {
            'confidenceScore': threshold
        },
        'results': results
    }

    return jsonify(output), 200


if __name__ == '__main__':
    app.run(debug=True)
