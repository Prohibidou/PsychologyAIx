import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const Report = ({ data }) => {
    const { ideology_classification, non_political_tweets, target_user } = data;

    const chartData = {
        labels: Object.keys(ideology_classification.counts),
        datasets: [
            {
                label: 'Ideology Classification',
                data: Object.values(ideology_classification.counts),
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
            },
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: `Ideology Classification for @${target_user}`,
            },
        },
    };

    return (
        <div className="card mt-4">
            <div className="card-header text-center">
                <h2>Analysis Report for @{target_user}</h2>
            </div>
            <div className="card-body">
                <div className="mb-4">
                    <h4>Ideology Classification</h4>
                    <Bar data={chartData} options={options} />
                </div>

                <div className="mb-4">
                    <h4>Political Tweet Analysis</h4>
                    <table className="table table-bordered">
                        <thead>
                            <tr>
                                <th>Tweet</th>
                                <th>Ideology</th>
                                <th>Confidence</th>
                            </tr>
                        </thead>
                        <tbody>
                            {ideology_classification.details.map((detail, index) => (
                                <tr key={index}>
                                    <td>{detail[0]}</td>
                                    <td>{detail[1]}</td>
                                    <td>{detail[2].toFixed(4)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div>
                    <h4>Non-Political Tweets</h4>
                    <ul className="list-group">
                        {non_political_tweets.map((tweet, index) => (
                            <li key={index} className="list-group-item">{tweet}</li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default Report;
