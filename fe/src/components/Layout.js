import React from "react";
import { NavLink } from "react-router-dom";
import tw from "tailwind-styled-components";
import { useTheme } from "../contexts/ThemeContext";

const ThemeToggle = tw.button`
  fixed top-4 right-4 p-3 rounded-full 
  transition-colors duration-300
  dark:bg-gray-700 dark:text-yellow-300 
  bg-gray-200 text-gray-700
  hover:scale-110
`;

const LayoutContainer = tw.div`
  flex flex-col justify-between items-center min-h-screen
  transition-colors duration-300
  dark:bg-gray-900 dark:text-white
  bg-gray-50 text-gray-900
`;

const ContentContainer = tw.div`
  flex-grow flex flex-col justify-center items-center w-full
  pt-16 pb-20
`;

const NavigationBar = tw.nav`
  fixed bottom-0 left-0 w-full 
  dark:bg-gray-800 dark:border-gray-700
  bg-gray-100 border-t shadow-md
`;

const NavItem = tw(NavLink)`
  flex-1 text-center py-4 text-lg font-semibold
  dark:text-gray-300 dark:hover:bg-gray-700
  text-gray-700 hover:bg-blue-200 
  transition duration-300
  [&.active]:text-blue-600 [&.active]:font-bold
`;

export default function Layout({ children }) {
  const { isDark, setIsDark } = useTheme();

  return (
    <LayoutContainer>
      <ThemeToggle onClick={() => setIsDark(!isDark)} aria-label="테마 변경">
        {isDark ? "🌙" : "☀️"}
      </ThemeToggle>
      <ContentContainer>{children}</ContentContainer>
      <NavigationBar>
        <div className="flex justify-around">
          <NavItem to="/" end>
            탐색
          </NavItem>
          <NavItem to="/live">반응</NavItem>
          <NavItem to="/highlight">분석</NavItem>
        </div>
      </NavigationBar>
    </LayoutContainer>
  );
}
