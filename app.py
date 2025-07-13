from flask import Flask, render_template, request, Response, json, jsonify
from flask_cors import CORS
import time
import traceback
import twitter_analyzer
import analyze_ideology
import config

app = Flask(__name__)
CORS(app)

# A simple in-memory store for request data. 
# In a production app, use a more robust solution like Redis or a database.
request_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if request.is_json:
            data = request.get_json()
            target_user = data.get('target_user')
            tweet_limit = int(data.get('tweet_limit', 100))
        else:
            data = request.form
            target_user = data.get('target_user')
            tweet_limit = int(data.get('tweet_limit', 100))

        if not target_user:
            return jsonify({'error': 'Target user is required.'}), 400

        # Set up the configuration for the analysis
        config.TWITTER_USER = data.get('user_name')
        config.TWITTER_PASS = data.get('user_password')
        config.TARGET_USER = target_user
        config.TWEET_LIMIT = tweet_limit

        # Run the Twitter scraper
        scraper_generator = twitter_analyzer.run_analysis(config)
        for message in scraper_generator:
            print(f"Scraper log: {message}")
            if "Scraping failed" in message:
                return jsonify({'error': message}), 500

        # Run the analysis and capture the final results
        final_results = None
        analysis_generator = analyze_ideology.run_analysis(config)
        for result in analysis_generator:
            if isinstance(result, str):
                print(f"Analysis log: {result}")
                if "An error occurred" in result:
                    return jsonify({'error': result}), 500
            else:
                final_results = result

        if final_results:
            response_data = {
                'target_user': config.TARGET_USER,
                'ideology_classification': final_results.get('analysis_results'),
                'non_political_tweets': final_results.get('non_political_tweets')
            }
            return jsonify(response_data)
        else:
            return jsonify({'error': 'Could not generate the final report. Please check the logs for more details.'}), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'An unexpected error occurred: {e}'}), 500

@app.route('/stream/<request_id>')
def stream(request_id):
    def generate():
        # Helper to format data as a Server-Sent Event (SSE).
        def format_sse(data, event=None):
            message = f"data: {json.dumps(data)}\n\n"
            if event:
                message = f"event: {event}\n{message}"
            return message

        try:
            data = request_data.get(request_id)
            if not data:
                yield format_sse({'message': 'Error: Could not find request data.'}, event='error')
                return

            # Set up the config for the analysis scripts
            config.TWITTER_USER = data['twitter_user']
            config.TWITTER_PASS = data['twitter_pass']
            config.TARGET_USER = data['target_user']
            config.TWEET_LIMIT = data['tweet_limit']

            # Stream logs from the twitter analyzer
            scraper_generator = twitter_analyzer.run_analysis(config)
            for message in scraper_generator:
                yield format_sse({'message': message}, event='log')
                if "Scraping failed" in message:
                    yield format_sse({'message': 'Error: Scraping failed.'}, event='error')
                    return

            # Stream logs and get results from the ideology analyzer
            analysis_generator = analyze_ideology.run_analysis(config)
            final_results = None
            for result in analysis_generator:
                if isinstance(result, str):
                    yield format_sse({'message': result}, event='log')
                else:
                    final_results = result
            
            # Stream the final report HTML
            if final_results:
                with app.app_context():
                    report_html = render_template('report_content.html', \
                                                  results=final_results['analysis_results'], \
                                                  non_political=final_results['non_political_tweets'])
                yield format_sse({'html': report_html}, event='report')
            else:
                 yield format_sse({'message': 'Could not generate the final report. Please check the logs for more details.'}, event='log')

        except Exception as e:
            # Log the full error to the server console for debugging
            traceback.print_exc()
            # Send a user-friendly error to the client
            yield format_sse({'message': f'An unexpected error occurred: {e}'}, event='error')
        finally:
            # Signal the client to close the connection
            yield format_sse({}, event='close')
            # Clean up the stored data
            if request_id in request_data:
                del request_data[request_id]

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)