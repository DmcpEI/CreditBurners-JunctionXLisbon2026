import React, {useState} from 'react';

export default function Evidence({url, alt, className = '', thumbnail = false}) {
  const [loadedUrl, setLoadedUrl] = useState(null);
  const [failedUrl, setFailedUrl] = useState(null);
  if (!url || failedUrl === url) return <div className={`image-missing ${className}`} role="status">Image unavailable</div>;
  return <img className={`${className} evidence-image ${loadedUrl === url ? 'is-loaded' : ''}`} onLoad={() => setLoadedUrl(url)} src={url} alt={alt} width={thumbnail ? 96 : 640}
    height={thumbnail ? 72 : 400} loading={thumbnail ? 'lazy' : 'eager'}
    onError={() => setFailedUrl(url)}/>;
}
