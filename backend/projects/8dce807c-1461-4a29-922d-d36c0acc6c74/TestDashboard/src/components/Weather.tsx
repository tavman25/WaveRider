import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Weather: React.FC = () => {
  const [weather, setWeather] = useState<any>(null);

  useEffect(() => {
    axios.get('https://api.openweathermap.org/data/2.5/weather?q=NewYork&appid=YOUR_API_KEY')
      .then(response => setWeather(response.data))
      .catch(error => console.error('Error fetching weather data:', error));
  }, []);

  if (!weather) return <div>Loading...</div>;

  return (
    <div>
      <h2>Local Weather</h2>
      <p>Temperature: {weather.main.temp}°C</p>
      <p>Condition: {weather.weather[0].description}</p>
    </div>
  );
};

export default Weather;