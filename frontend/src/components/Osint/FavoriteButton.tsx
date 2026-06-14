import { useState, useEffect } from 'react';
import { Star } from 'lucide-react';
import { toggleFavorite, fetchFavorites } from '../Desktop/lib/api';

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://127.0.0.1:8000';

interface FavoriteButtonProps {
  toolName: string;
}

export function FavoriteButton({ toolName }: FavoriteButtonProps) {
  const [favorited, setFavorited] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchFavorites(API_URL)
      .then((res) => setFavorited(res.favorites.includes(toolName)))
      .catch(() => setFavorited(false));
  }, [toolName]);

  const handleToggle = async () => {
    setLoading(true);
    try {
      const res = await toggleFavorite(API_URL, toolName);
      setFavorited(res.favorited);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className="p-1.5 rounded-md transition-colors cursor-pointer disabled:opacity-50"
      style={{
        color: favorited ? 'var(--color-accent)' : 'var(--color-text-tertiary)',
      }}
      title={favorited ? 'Remove from favorites' : 'Add to favorites'}
    >
      <Star size={14} fill={favorited ? 'currentColor' : 'none'} />
    </button>
  );
}
