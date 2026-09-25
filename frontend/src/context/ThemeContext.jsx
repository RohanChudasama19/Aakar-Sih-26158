import React, { createContext, useState, useEffect, useContext } from 'react';

const ThemeContext = createContext();

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('aerorecon-theme');
    return savedTheme || 'dark'; // Default is dark
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('aerorecon-theme', theme);
  }, [theme]);

  const availableThemes = [
    { id: 'dark', label: 'Dark Aerospace (Default)' },
    { id: 'light', label: 'Light Professional' },
    { id: 'solarized-dark', label: 'Solarized Dark' },
    { id: 'high-contrast', label: 'High Contrast' },
    { id: 'glassmorphic', label: 'Neumorphic / Glassmorphic' },
    { id: 'poppy', label: 'Poppy Theme' },
    { id: 'cartoonic', label: 'Cartoonic Theme' },
    { id: 'turquoise', label: 'Solid Turquoise' },
    { id: 'light-turquoise', label: 'Light Turquoise' },
    { id: 'saffron', label: 'Solid Saffron' },
    { id: 'light-saffron', label: 'Light Saffron' },
    { id: 'amethyst', label: 'Solid Amethyst' },
    { id: 'light-amethyst', label: 'Light Amethyst' },
    { id: 'emerald', label: 'Solid Emerald' },
    { id: 'light-emerald', label: 'Light Emerald' },
    { id: 'ruby', label: 'Solid Ruby' },
    { id: 'light-ruby', label: 'Light Ruby' }
  ];

  return (
    <ThemeContext.Provider value={{ theme, setTheme, availableThemes }}>
      {children}
    </ThemeContext.Provider>
  );
};
