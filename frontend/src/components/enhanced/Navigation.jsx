import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navigation = ({ links = [] }) => {
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const defaultLinks = links.length > 0 ? links : [
    { path: '/', label: 'Discover' },
    { path: '/search', label: 'Search' },
    { path: '/protocols', label: 'Protocols' },
    { path: '/analytics', label: 'Analytics' },
    { path: '/about', label: 'About' }
  ];

  return (
    <nav className={`colossal-nav ${scrolled ? 'backdrop-blur-xl' : ''}`}>
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-colossal-electric-blue to-colossal-plasma-cyan flex items-center justify-center">
              <span className="text-white font-bold text-xl">R</span>
            </div>
            <span className="text-xl font-bold text-white">
              RNA Lab Navigator
            </span>
          </Link>

          <div className="flex items-center space-x-1">
            {defaultLinks.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`
                    nav-link
                    ${isActive ? 'text-white' : ''}
                  `}
                >
                  {link.label}
                  {isActive && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-colossal-electric-blue to-colossal-plasma-cyan" />
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;