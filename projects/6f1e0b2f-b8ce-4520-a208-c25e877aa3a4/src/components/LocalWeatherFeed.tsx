import React, { useEffect, useState } from 'react';
import axios from 'axios';

const LocalWeatherFeed: React.FC = () => {
  const [weather, setWeather] = useState<any>({});

  useEffect(() => {
    axios.get('https://api.openweathermap.org/data/2.5/weather?q=NewYork&appid=YOUR_API_KEY&units=imperial')
      .then(response => setWeather(response.data))
      .catch(error => console.error('Error fetching weather:', error));
  }, []);

  return (
    <div className="widget">
      <h2>Local Weather</h2>
      {weather.main && (
        <div>
          <p>Temperature: {weather.main.temp}°F</p>
          <p>Humidity: {weather.main.humidity}%</p>
        </div>
      )}
    </div>
  );
};

export default LocalWeatherFeed;