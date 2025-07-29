import React, { useState, useEffect } from 'react';
import axios from 'axios';

const WeatherFeed: React.FC = () => {
  const [weather, setWeather] = useState<any>(null);

  useEffect(() => {
    axios.get('https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_API_KEY&units=metric')
      .then(response => setWeather(response.data))
      .catch(error => console.error('Error fetching weather:', error));
  }, []);

  if (!weather) return <div>Loading...</div>;

  return (
    <div>
      <h2>Weather in {weather.name}</h2>
      <p>Temperature: {weather.main.temp}°C</p>
      <p>Condition: {weather.weather[0].description}</p>
    </div>
  );
};

export default WeatherFeed;