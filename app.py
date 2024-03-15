from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/process', methods=['POST'])
def process():
    if not request.is_json:
        return jsonify({'error': 'Request must be in JSON format'}), 400

    data = request.json

    required_params = ['context', 'category', 'threshold', 'noOfMatches', 'inputPath']
    for param in required_params:
        if param not in data:
            return jsonify({'error': f'Missing parameter: {param}'}), 400

    threshold = data['threshold']
    if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
        return jsonify({'error': 'Threshold must be a float between 0 and 1'}), 400

    result = {
        'context': data['context'],
        'category': data['category'],
        'threshold': threshold,
        'noOfMatches': data['noOfMatches'],
        'inputPath': data['inputPath']
    }

    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True)
