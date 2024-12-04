import React, { useEffect, useState } from 'react';
import axios from 'axios';

function DataComponent() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios.get('http://127.0.0.1:5000/api/data')
            .then(response => {
                if (response.status !== 200) {
                    throw new Error('Network response was not ok');
                }
                console.log("Data fetched from API:", response.data); // Log the entire response data
                setData(response.data);
            })
            .catch(error => {
                console.error("Error fetching data:", error); // Log the error
                setError(error);
            });
    }, []);

    if (error) {
        return <div>API Error: {error.message}</div>;
    }

    if (!data) {
        return <div>Loading...</div>;
    }

    console.log("Data state:", data); // Log the data state

    const monthlySpendingData = data.monthly_spending_data || {};
    const outlierMonths = data.outlier_months || [];
    const summary = data.summary || '';

    console.log("Monthly Spending Data:", monthlySpendingData); // Log monthly spending data

    // Log the keys and values of monthlySpendingData
    console.log("Monthly Spending Data Keys:", Object.keys(monthlySpendingData));
    console.log("Monthly Spending Data Values:", Object.values(monthlySpendingData));

    return (
        <div>
            <h1>Monthly Spending Data</h1>
            {Object.keys(monthlySpendingData).length > 0 ? (
                <table>
                    <thead>
                        <tr>
                            <th>Month</th>
                            {Object.keys(monthlySpendingData[Object.keys(monthlySpendingData)[0]]).map((category, index) => (
                                <th key={index}>{category}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {Object.entries(monthlySpendingData).map(([month, monthData], index) => (
                            <tr key={index}>
                                <td>{month}</td>
                                {Object.values(monthData).map((value, index) => (
                                    <td key={index}>{value !== null ? value : 'N/A'}</td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : (
                <p>No monthly spending data available.</p>
            )}
            <h2>Outlier Months</h2>
            {outlierMonths.length > 0 ? (
                <ul>
                    {outlierMonths.map((outlier, index) => (
                        <li key={index}>{`Month: ${outlier[0]}, Category: ${outlier[1]}`}</li>
                    ))}
                </ul>
            ) : (
                <p>No outlier months available.</p>
            )}
            <h2>Summary</h2>
            <pre>{summary}</pre>
        </div>
    );
}

export default DataComponent;