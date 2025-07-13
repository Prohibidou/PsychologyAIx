import React, { useState } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';

import './App.css';
import Report from './Report';

function App() {
    const [formData, setFormData] = useState({
        user_name: '',
        user_password: '',
        target_user: '',
        tweet_limit: ''
    });
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setReport(null);
        try {
            const response = await axios.post('http://127.0.0.1:5000/analyze', formData);
            setReport(response.data);
        } catch (err) {
            setError('An error occurred while analyzing the profile. Please check the console for more details.');
            console.error(err);
        }
        setLoading(false);
    };

    return (
        <div className="container mt-5">
            <div className="animated-background"></div>
            <div className="row justify-content-center">
                <div className="col-md-8">
                    <div className="card">
                        <div className="card-header text-center">
                            <h1>Psychology AIx</h1>
                            <p className="subtitle text-muted">Ideological Insights into a Twitter Profile</p>
                        </div>
                        <div className="card-body">
                            <div className="text-center mb-4">
                                <svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" fill="currentColor" className="bi bi-twitter-x" viewBox="0 0 16 16">
                                    <path d="M12.6.75h2.454l-5.36 6.142L16 15.25h-4.937l-3.867-5.07-4.425 5.07H.316l5.733-6.57L0 .75h5.063l3.495 4.633L12.6.75zm-.86 13.028h1.36L4.323 2.145H2.865l8.875 11.633z"/>
                                </svg>
                            </div>
                            <form onSubmit={handleSubmit}>
                                <div className="mb-3">
                                    <label className="form-label">Your Twitter Username (Without @)</label>
                                    <input
                                        type="text"
                                        className="form-control"
                                        name="user_name"
                                        value={formData.user_name}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">Your Twitter Password</label>
                                    <input
                                        type="password"
                                        className="form-control"
                                        name="user_password"
                                        value={formData.user_password}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">Username of the Target User To Analyze (Without @)</label>
                                    <input
                                        type="text"
                                        className="form-control"
                                        name="target_user"
                                        value={formData.target_user}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">Tweet Limit</label>
                                    <input
                                        type="number"
                                        className="form-control"
                                        name="tweet_limit"
                                        value={formData.tweet_limit}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                                <div className="d-grid">
                                    <button type="submit" className="btn btn-dark w-100" disabled={loading}>
                                        {loading ? 'Analyzing...' : 'Analyze'}
                                    </button>
                                </div>
                            </form>
                            {error && <div className="alert alert-danger mt-3">{error}</div>}
                        </div>
                    </div>
                    {report && <Report data={report} />}
                </div>
            </div>
        </div>
    );
}
export default App;