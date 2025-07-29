import React from 'react';
import axios from 'axios';

const WeatherWidget: React.FC = () => {
  const [weather, setWeather] = React.useState<any>(null);

  React.useEffect(() => {
    axios.get('https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_API_KEY&units=metric')
      .then(response => setWeather(response.data))
      .catch(error => console.error('Error fetching weather data:', error));
  }, []);

  return (
    <div>
      <h2>Local Weather</h2>
      {weather ? (
        <div>
          <p>Temperature: {weather.main.temp}°C</p>
          <p>Condition: {weather.weather[0].description}</p>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
};

export default WeatherWidget;