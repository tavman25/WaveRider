import React from 'react';
import './App.css';
import FacebookFeed from './components/FacebookFeed';
import LocalNewsFeed from './components/LocalNewsFeed';
import LocalWeatherFeed from './components/LocalWeatherFeed';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Feed Widgets</h1>
      </header>
      <main>
        <div className="widget-container">
          <FacebookFeed />
          <LocalNewsFeed />
          <LocalWeatherFeed />
        </div>
      </main>
    </div>
  );
}

export default App;