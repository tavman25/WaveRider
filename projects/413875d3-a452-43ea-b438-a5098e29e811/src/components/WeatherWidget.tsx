import React, { useEffect, useState } from 'react';
import axios from 'axios';

const WeatherWidget: React.FC = () => {
  const [weather, setWeather] = useState<any>({});

  useEffect(() => {
    axios.get('https://api.openweathermap.org/data/2.5/weather?q=YourCity&appid=YOUR_API_KEY&units=metric')
      .then(response => setWeather(response.data))
      .catch(error => console.error('Error fetching weather data:', error));
  }, []);

  return (
    <div>
      <h2>Local Weather</h2>
      <p>Temperature: {weather.main?.temp}°C</p>
      <p>Condition: {weather.weather?.[0].description}</p>
    </div>
  );
};

export default WeatherWidget;