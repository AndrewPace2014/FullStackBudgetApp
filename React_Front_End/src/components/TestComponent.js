import React, { useEffect, useState } from 'react';
import axios from 'axios';

function TestComponent() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios.get('http://127.0.0.1:5000/api/test')
            .then(response => {
                if (response.status !== 200) {
                    throw new Error('Network response was not ok');
                }
                setData(response.data);
            })
            .catch(error => setError(error));
    }, []);

    if (error) {
        return <div>API Error: {error.message}</div>;
    }

    if (!data) {
        return <div>Loading...</div>;
    }

    return (
        <div>
            <h1>Test Message</h1>
            <p>{data.message}</p>
        </div>
    );
}

export default TestComponent;