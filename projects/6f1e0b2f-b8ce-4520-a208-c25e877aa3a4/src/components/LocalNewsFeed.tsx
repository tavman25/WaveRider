import React, { useEffect, useState } from 'react';
import axios from 'axios';

const LocalNewsFeed: React.FC = () => {
  const [articles, setArticles] = useState<any[]>([]);

  useEffect(() => {
    axios.get('https://newsapi.org/v2/top-headlines?country=us&apiKey=YOUR_API_KEY')
      .then(response => setArticles(response.data.articles))
      .catch(error => console.error('Error fetching local news:', error));
  }, []);

  return (
    <div className="widget">
      <h2>Local News</h2>
      {articles.map(article => (
        <div key={article.title}>
          <h3>{article.title}</h3>
          <p>{article.description}</p>
        </div>
      ))}
    </div>
  );
};

export default LocalNewsFeed;