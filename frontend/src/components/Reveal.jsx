import { useEffect, useRef, useState } from 'react';
import { Box } from '@mui/material';

// Respect the user's OS-level reduced-motion preference — skip the animation
// and just show content immediately.
const prefersReducedMotion =
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

/**
 * Fades + slides content in the first time it scrolls into view. Also fires
 * naturally on mount for anything already in the viewport (e.g. the hero),
 * giving a page-load entrance animation for free.
 */
export default function Reveal({ children, delay = 0, y = 20, duration = 0.6, sx = {}, component = Box }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(prefersReducedMotion);
  const Component = component;

  useEffect(() => {
    if (prefersReducedMotion) return;
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <Component
      ref={ref}
      sx={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : `translateY(${y}px)`,
        transition: `opacity ${duration}s ease ${delay}s, transform ${duration}s ease ${delay}s`,
        willChange: 'opacity, transform',
        ...sx,
      }}
    >
      {children}
    </Component>
  );
}
