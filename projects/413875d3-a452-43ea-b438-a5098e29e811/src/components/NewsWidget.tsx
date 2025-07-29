import React, { useEffect, useState } from 'react';
import axios from 'axios';

const NewsWidget: React.FC = () => {
  const [articles, setArticles] = useState<any[]>([]);

  useEffect(() => {
    axios.get('https://newsapi.org/v2/top-headlines?country=us&apiKey=YOUR_API_KEY')
      .then(response => setArticles(response.data.articles))
      .catch(error => console.error('Error fetching news data:', error));
  }, []);

  return (
    <div>
      <h2>National News</h2>
      {articles.slice(0, 3).map(article => (
        <div key={article.title}>
          <h3>{article.title}</h3>
          <p>{article.description}</p>
        </div>
      ))}
    </div>
  );
};

export default NewsWidget;