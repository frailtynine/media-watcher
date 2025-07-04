import React, { createContext, useContext, useState, ReactNode, ReactElement } from 'react';

interface ComponentContextProps {
  currentComponent: ReactElement | null;
  setCurrentComponent: (component: ReactElement | null) => void;
}

const ComponentContext = createContext<ComponentContextProps | undefined>(undefined);

export const ComponentProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentComponent, setCurrentComponent] = useState<ReactElement | null>(null);

  return (
    <ComponentContext.Provider value={{ currentComponent, setCurrentComponent }}>
      {children}
    </ComponentContext.Provider>
  );
};

export const useComponent = () => {
  const context = useContext(ComponentContext);
  if (!context) {
    throw new Error('useComponent must be used within a ComponentProvider');
  }
  return context;
};