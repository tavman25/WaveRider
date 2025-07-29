import React from 'react';
import './App.css';
import FacebookWidget from './components/FacebookWidget';
import WeatherWidget from './components/WeatherWidget';
import NewsWidget from './components/NewsWidget';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>API Widgets Dashboard</h1>
      </header>
      <main>
        <FacebookWidget />
        <WeatherWidget />
        <NewsWidget />
      </main>
    </div>
  );
}

export default App;