import React from "react";
import { NavLink } from "react-router-dom";
import tw from "tailwind-styled-components";

const LayoutContainer = tw.div`
  flex flex-col justify-between items-center min-h-screen bg-gray-50
`;

const ContentContainer = tw.div`
  flex-grow flex flex-col justify-center items-center w-full
`;

const NavigationBar = tw.nav`
  fixed bottom-0 left-0 w-full bg-gray-100 shadow-md border-t
`;

const NavItem = tw(NavLink)`
  flex-1 text-center py-4 text-lg font-semibold text-gray-700
  hover:bg-teal-200 hover:text-gray-900 transition duration-300
  active:bg-teal-300
  [&.active]:text-teal-600 [&.active]:font-bold
`;

export default function Layout({ children }) {
  return (
    <LayoutContainer>
      <ContentContainer>{children}</ContentContainer>
      <NavigationBar>
        <div className="flex justify-around">
          <NavItem to="/" exact>
            탐색
          </NavItem>
          <NavItem to="/live">반응</NavItem>
          <NavItem to="/highlight">분석</NavItem>
        </div>
      </NavigationBar>
    </LayoutContainer>
  );
}
