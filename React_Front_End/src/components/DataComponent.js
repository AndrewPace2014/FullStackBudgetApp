import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Table, Container, Row, Col, Alert, Spinner, Tabs, Tab, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { Line, Bar } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip as ChartTooltip,
    Legend,
    registerables
} from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './DataComponent.css'; // Import CSS for additional styling

// Register the necessary components with Chart.js
ChartJS.register(
    ...registerables,
    zoomPlugin
);

function DataComponent() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [key, setKey] = useState('summary');

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
        return <Alert variant="danger">API Error: {error.message}</Alert>;
    }

    if (!data) {
        return <div className="loading"><Spinner animation="border" role="status"><span className="sr-only">Loading...</span></Spinner></div>;
    }

    console.log("Data state:", data); // Log the data state

    const monthlySpendingData = data.monthly_spending_data || {};
    const outlierMonths = data.outlier_months || [];
    const summary = data.summary || '';

    console.log("Monthly Spending Data:", monthlySpendingData); // Log monthly spending data

    // Sort the monthly spending data by date in descending order
    const sortedMonthlySpendingData = Object.entries(monthlySpendingData).sort(([a], [b]) => new Date(b) - new Date(a));

    // Prepare data for the line chart
    const lineChartData = {
        labels: sortedMonthlySpendingData.map(([month]) => month),
        datasets: Object.keys(monthlySpendingData[Object.keys(monthlySpendingData)[0]]).map((category, index) => ({
            label: category,
            data: sortedMonthlySpendingData.map(([, monthData]) => monthData[category] || 0),
            backgroundColor: `rgba(${index * 30}, ${100 + index * 20}, ${150 + index * 10}, 0.6)`,
            borderColor: `rgba(${index * 30}, ${100 + index * 20}, ${150 + index * 10}, 1)`,
            borderWidth: 1,
            fill: false,
        })),
    };

    // Calculate month-over-month changes
    const calculateChange = (current, previous) => {
        if (previous === 0) return 'N/A';
        const change = ((current - previous) / Math.abs(previous)) * 100;
        return change.toFixed(2);
    };

    // Prepare data for the bar chart (month-over-month changes)
    const barChartData = {
        labels: sortedMonthlySpendingData.map(([month]) => month),
        datasets: Object.keys(monthlySpendingData[Object.keys(monthlySpendingData)[0]]).map((category, index) => ({
            label: category,
            data: sortedMonthlySpendingData.map(([, monthData], idx, arr) => {
                const previousMonthData = arr[idx + 1] ? arr[idx + 1][1] : {};
                const current = monthData[category] || 0;
                const previous = previousMonthData[category] || 0;
                return parseFloat(calculateChange(current, previous));
            }),
            backgroundColor: `rgba(${index * 30}, ${100 + index * 20}, ${150 + index * 10}, 0.6)`,
            borderColor: `rgba(${index * 30}, ${100 + index * 20}, ${150 + index * 10}, 1)`,
            borderWidth: 1,
        })),
    };

    // Format currency
    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
    };

    // Zoom and pan options
    const zoomOptions = {
        pan: {
            enabled: true,
            mode: 'x',
        },
        zoom: {
            enabled: true,
            mode: 'x',
        },
    };

    return (
        <Container className="data-component">
            <Tabs id="data-tabs" activeKey={key} onSelect={(k) => setKey(k)} className="mb-3">
                <Tab eventKey="summary" title="Summary">
                    <Row>
                        <Col>
                            <h2 className="text-center">Summary</h2>
                            <pre className="summary">{summary}</pre>
                        </Col>
                    </Row>
                </Tab>
                <Tab eventKey="spendingOverview" title="Spending Overview">
                    <Row>
                        <Col>
                            <h2 className="text-center">Spending Overview</h2>
                            <div className="chart-container">
                                <Line data={lineChartData} options={{ responsive: true, maintainAspectRatio: false, plugins: { zoom: zoomOptions } }} />
                            </div>
                        </Col>
                    </Row>
                </Tab>
                <Tab eventKey="monthOverMonthChanges" title="Month-over-Month Changes">
                    <Row>
                        <Col>
                            <h2 className="text-center">Month-over-Month Changes</h2>
                            <div className="chart-container">
                                <Bar data={barChartData} options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: { zoom: zoomOptions },
                                    scales: {
                                        y: {
                                            ticks: {
                                                callback: function (value) {
                                                    return value + '%';
                                                }
                                            }
                                        }
                                    }
                                }} />
                            </div>
                        </Col>
                    </Row>
                </Tab>
                <Tab eventKey="outlierMonths" title="Outlier Months">
                    <Row>
                        <Col>
                            <h2 className="text-center">Outlier Months</h2>
                            {outlierMonths.length > 0 ? (
                                <Table striped bordered hover className="outlier-table">
                                    <thead>
                                        <tr>
                                            <th>Month</th>
                                            <th>Category</th>
                                            <th>Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {outlierMonths.map((outlier, index) => (
                                            <tr key={index}>
                                                <td>{outlier[0]}</td>
                                                <td>{outlier[1]}</td>
                                                <td>{formatCurrency(outlier[2])}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </Table>
                            ) : (
                                <p>No outlier months available.</p>
                            )}
                        </Col>
                    </Row>
                </Tab>
                <Tab eventKey="monthlySpending" title="Monthly Spending Data">
                    <Row>
                        <Col>
                            <h1 className="text-center">Monthly Spending Data</h1>
                            {sortedMonthlySpendingData.length > 0 ? (
                                <Table striped bordered hover className="spending-table">
                                    <thead>
                                        <tr>
                                            <th>Month</th>
                                            {Object.keys(monthlySpendingData[Object.keys(monthlySpendingData)[0]]).map((category, index) => (
                                                <th key={index}>{category}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedMonthlySpendingData.map(([month, monthData], index, arr) => {
                                            const previousMonthData = arr[index + 1] ? arr[index + 1][1] : {};
                                            const change = Object.keys(monthData).reduce((acc, category) => {
                                                const current = monthData[category] || 0;
                                                const previous = previousMonthData[category] || 0;
                                                acc[category] = calculateChange(current, previous);
                                                return acc;
                                            }, {});
                                            return (
                                                <tr key={index}>
                                                    <td>{month}</td>
                                                    {Object.keys(monthData).map((category, index) => (
                                                        <td key={index}>
                                                            <div>{monthData[category] !== null ? formatCurrency(monthData[category]) : 'N/A'}</div>
                                                            <OverlayTrigger
                                                                key={index}
                                                                placement="top"
                                                                overlay={<Tooltip id={`tooltip-${index}`}>{`${category}: ${change[category]}%`}</Tooltip>}
                                                            >
                                                                <div className={parseFloat(change[category]) > 0 ? 'text-success' : 'text-danger'}>
                                                                    {parseFloat(change[category]) > 0 ? '↑' : '↓'} {change[category]}%
                                                                </div>
                                                            </OverlayTrigger>
                                                        </td>
                                                    ))}
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </Table>
                            ) : (
                                <p>No monthly spending data available.</p>
                            )}
                        </Col>
                    </Row>
                </Tab>
            </Tabs>
        </Container>
    );
}

export default DataComponent;