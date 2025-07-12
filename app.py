from flask import Flask, render_template, request, Response, json
import time
import traceback
import twitter_analyzer
import analyze_ideology
import config

app = Flask(__name__)

# A simple in-memory store for request data. 
# In a production app, use a more robust solution like Redis or a database.
request_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # Generate a unique ID for this request and store the form data
    request_id = str(time.time())
    request_data[request_id] = {
        'twitter_user': request.form['twitter_user'],
        'twitter_pass': request.form['twitter_pass'],
        'target_user': request.form['target_user'],
        'tweet_limit': int(request.form['tweet_limit'])
    }
    # Immediately render the report page, which will connect to the stream.
    return render_template('report.html', request_id=request_id)

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
            for message in twitter_analyzer.run_analysis(config):
                yield format_sse({'message': message}, event='log')

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
                    report_html = render_template('report_content.html', 
                                                  results=final_results['analysis_results'], 
                                                  non_political=final_results['non_political_tweets'])
                yield format_sse({'html': report_html}, event='report')
            else:
                 yield format_sse({'message': 'Could not generate the final report.'}, event='log')

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