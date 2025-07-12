# X-Psychology

X-Psychology is a web application that provides ideological insights into a Twitter (now X) profile by analyzing the user's public tweets and replies. This tool can be particularly useful for recruiters or anyone interested in understanding a user's perspective based on their public activity. By examining the content a user engages with, X-Psychology offers a glimpse into their potential viewpoints and interests.

## How It Works

The application uses Selenium to scrape the public tweets and replies of a target user. It then employs a Hugging Face model to perform sentiment and ideological analysis on the collected data. The results are presented in a clear and concise report, categorizing the user's tweets into different ideological spectrums.

## Installation

To run X-Psychology on your local machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/X-Psychology.git
    cd X-Psychology
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the Flask application:**
    ```bash
    python app.py
    ```

2.  **Open your web browser** and navigate to `http://127.0.0.1:5000`.

3.  **Fill in the required fields:**
    *   **Your Twitter Username (Without @):** Your personal Twitter handle.
    *   **Your Twitter Password:** Your personal Twitter password.
    *   **Username of the Target User To Analyze (Without @):** The Twitter handle of the user you want to analyze.
    *   **Number of Tweets to Analyze:** The maximum number of tweets to analyze.

4.  **Click "Analyze"** and wait for the report to be generated.

## Disclaimer

This tool is intended for informational purposes only. The analysis is based on publicly available data and should not be used as the sole factor in making decisions about individuals. The accuracy of the ideological analysis is dependent on the performance of the underlying machine learning model and the quality of the data collected.