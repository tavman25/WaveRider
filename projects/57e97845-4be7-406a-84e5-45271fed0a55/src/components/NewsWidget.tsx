import React from 'react';
import axios from 'axios';

const NewsWidget: React.FC = () => {
  const [news, setNews] = React.useState<any[]>([]);

  React.useEffect(() => {
    axios.get('https://newsapi.org/v2/top-headlines?country=us&apiKey=YOUR_API_KEY')
      .then(response => setNews(response.data.articles))
      .catch(error => console.error('Error fetching news data:', error));
  }, []);

  return (
    <div>
      <h2>National News</h2>
      {news.length > 0 ? (
        <ul>
          {news.slice(0, 3).map((article, index) => (
            <li key={index}>
              <a href={article.url} target="_blank" rel="noopener noreferrer">{article.title}</a>
            </li>
          ))}
        </ul>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
};

export default NewsWidget;