import React, { useState, useEffect } from 'react';

function App() {
  const [count, setCount] = useState(0);
  const [time, setTime] = useEffect(() => {
    const timer = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="App">
      <h1>Welcome to My React App</h1>
      <p>Current time: {time}</p>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}

export default App;