import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import FacebookFeed from './components/FacebookFeed';
import WeatherFeed from './components/WeatherFeed';

const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <h1>devDashboard</h1>
        <Switch>
          <Route path="/facebook" component={FacebookFeed} />
          <Route path="/weather" component={WeatherFeed} />
          <Route path="/" exact render={() => <h2>Welcome to your dashboard</h2>} />
        </Switch>
      </div>
    </Router>
  );
};

export default App;