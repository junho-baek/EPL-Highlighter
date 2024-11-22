import React from "react";
import tw from "tailwind-styled-components";
import { reactions } from "../mockData";
import Layout from "../components/Layout";

const PageTitle = tw.h1`
  text-4xl font-bold text-blue-600 mb-6
`;

const ReactionContainer = tw.div`
  flex flex-col gap-6 items-center w-full max-w-7xl mx-auto p-4
  lg:flex-row lg:items-start lg:justify-center
`;

const ReactionList = tw.ul`
  w-full max-w-lg rounded-lg shadow-md p-4 border-2
  ${(p) =>
    p.$isDark ? "bg-gray-800 border-gray-700" : "bg-white border-blue-200"}
  lg:flex-1
`;

const ChatMessages = tw.div`
  w-full max-w-lg rounded-lg shadow-md p-4 border-2
  h-64 overflow-y-auto
  ${(p) =>
    p.$isDark ? "bg-gray-800 border-gray-700" : "bg-gray-100 border-blue-200"}
  lg:flex-1 lg:h-[500px]
`;

function Live() {
  return (
    <Layout>
      <PageTitle>실시간 반응</PageTitle>
      <ReactionContainer>
        <ReactionList>
          <h2 className="text-lg font-semibold mb-3">반응량</h2>
          {reactions.reactions.map((reaction, index) => (
            <li key={index} className="text-gray-700">
              Time {index + 1}: {reaction} reactions
            </li>
          ))}
        </ReactionList>
        <ChatMessages>
          <h2 className="text-lg font-semibold mb-3">메시지</h2>
          {reactions.messages.map((message, index) => (
            <p key={index} className="text-gray-700 mb-2">
              {message}
            </p>
          ))}
        </ChatMessages>
      </ReactionContainer>
    </Layout>
  );
}

export default Live;
