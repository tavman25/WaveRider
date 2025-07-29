import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Morning Dashboard</h1>
      </header>
      <main>
        <section>
          <h2>Today's Weather</h2>
          <p>Weather details will go here.</p>
        </section>
        <section>
          <h2>News Headlines</h2>
          <ul>
            <li>News item 1</li>
            <li>News item 2</li>
          </ul>
        </section>
      </main>
    </div>
  );
}

export default App;