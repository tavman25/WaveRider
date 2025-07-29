import React from 'react';
import Weather from './components/Weather';
import News from './components/News';
import FacebookFeed from './components/FacebookFeed';

function App() {
  return (
    <div className="App">
      <h1>Test Dashboard</h1>
      <Weather />
      <News />
      <FacebookFeed />
    </div>
  );
}

export default App;