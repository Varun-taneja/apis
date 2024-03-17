from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/search', methods=['POST'])
def search():
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

    # Check if category is valid
    if category not in ['resume', 'job']:
        return jsonify({'status': 'Bad Request', 'message': 'Please check category should be either resume or job!'}), 400

    # Mock processing logic
    results = []

    # Check if no results found
    if no_of_matches <= 0:
        return jsonify({'status': 'failure', 'message': 'No results found'}), 404

    # Process the data
    for i in range(1, no_of_matches + 1):
        if category == 'resume':
            results.append({
                'id': i,
                'score': threshold,
                'path': f'{i}.pdf'
            })
        elif category == 'job':
            results.append({
                'id': i,
                'score': threshold,
                'path': f'{i}job.pdf'  # Adjusting the file path for the 'job' category
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

@app.route('/ping', methods=['GET'])
def ping():
    response = {
        "status": "healthy",
        "dependencies": {
            "modelAPIS": {
                "model1": "online",
                "model2": "offline"
            },
            "database": {
                "connection": "available",
                "responseTime": "12 ms"
            },
            "memory": {
                "usage": "normal"
            },
            "cpu": {
                "usage": ".5"  # Placeholder value, you can replace this with actual CPU usage data
            }
        }
    }
    return jsonify(response), 200
    
if __name__ == '__main__':
    app.run(debug=True)
