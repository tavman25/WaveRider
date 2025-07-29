import React, { useState, useEffect } from 'react';
import axios from 'axios';

const News: React.FC = () => {
  const [news, setNews] = useState<any[]>([]);

  useEffect(() => {
    axios.get('https://newsapi.org/v2/top-headlines?country=us&apiKey=YOUR_API_KEY')
      .then(response => setNews(response.data.articles))
      .catch(error => console.error('Error fetching news data:', error));
  }, []);

  return (
    <div>
      <h2>Local News</h2>
      {news.slice(0, 3).map((article, index) => (
        <div key={index}>
          <h3>{article.title}</h3>
          <p>{article.description}</p>
        </div>
      ))}
    </div>
  );
};

export default News;