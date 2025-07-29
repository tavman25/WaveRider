import React, { useState, useEffect } from 'react';
import axios from 'axios';

const FacebookFeed: React.FC = () => {
  const [posts, setPosts] = useState<any[]>([]);

  useEffect(() => {
    axios.get('https://graph.facebook.com/v13.0/me/feed?access_token=YOUR_ACCESS_TOKEN')
      .then(response => setPosts(response.data.data))
      .catch(error => console.error('Error fetching Facebook feed:', error));
  }, []);

  return (
    <div>
      <h2>Facebook Feed</h2>
      {posts.slice(0, 3).map((post, index) => (
        <div key={index}>
          <p>{post.message}</p>
        </div>
      ))}
    </div>
  );
};

export default FacebookFeed;