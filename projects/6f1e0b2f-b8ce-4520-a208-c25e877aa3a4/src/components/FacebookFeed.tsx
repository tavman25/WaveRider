import React, { useEffect, useState } from 'react';
import axios from 'axios';

const FacebookFeed: React.FC = () => {
  const [posts, setPosts] = useState<any[]>([]);

  useEffect(() => {
    axios.get('https://graph.facebook.com/v13.0/me/feed?access_token=YOUR_ACCESS_TOKEN')
      .then(response => setPosts(response.data.data))
      .catch(error => console.error('Error fetching Facebook feed:', error));
  }, []);

  return (
    <div className="widget">
      <h2>Facebook Feed</h2>
      {posts.map(post => (
        <div key={post.id}>
          <p>{post.message}</p>
        </div>
      ))}
    </div>
  );
};

export default FacebookFeed;