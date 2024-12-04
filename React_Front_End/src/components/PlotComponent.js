import React, { useEffect, useState } from 'react';
import axios from 'axios';

function DataComponent() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios.get('http://127.0.0.1:5000/api/data')
            .then(response => setData(response.data))
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
            <h1>Data Summary</h1>
            <p>{data.summary}</p>
            {/* Render other data here */}
        </div>
    );
}

export default DataComponent;