import React, { useState, useEffect } from 'react';
import axios from 'axios';

const FacebookFeed: React.FC = () => {
  const [posts, setPosts] = useState<any[]>([]);

  useEffect(() => {
    axios.get('https://graph.facebook.com/v13.0/me/feed?access_token=YOUR_FB_ACCESS_TOKEN')
      .then(response => setPosts(response.data.data))
      .catch(error => console.error('Error fetching posts:', error));
  }, []);

  return (
    <div>
      <h2>Facebook Feed</h2>
      {posts.map(post => (
        <div key={post.id}>
          <h3>{post.message}</h3>
          <p>Posted on: {new Date(post.created_time).toLocaleString()}</p>
        </div>
      ))}
    </div>
  );
};

export default FacebookFeed;