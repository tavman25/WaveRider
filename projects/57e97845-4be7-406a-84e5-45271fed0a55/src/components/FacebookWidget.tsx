import React from 'react';
import axios from 'axios';

const FacebookWidget: React.FC = () => {
  const [data, setData] = React.useState<any>(null);

  React.useEffect(() => {
    axios.get('https://graph.facebook.com/v13.0/me?fields=id,name&access_token=YOUR_ACCESS_TOKEN')
      .then(response => setData(response.data))
      .catch(error => console.error('Error fetching data:', error));
  }, []);

  return (
    <div>
      <h2>Facebook</h2>
      {data ? (
        <div>
          <p>ID: {data.id}</p>
          <p>Name: {data.name}</p>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
};

export default FacebookWidget;