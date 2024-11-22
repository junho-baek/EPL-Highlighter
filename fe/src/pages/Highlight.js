import React from "react";
import tw from "tailwind-styled-components";
import { highlights } from "../mockData";
import Layout from "../components/Layout";

const PageTitle = tw.h1`
  text-4xl font-bold text-blue-600 mb-6
`;

const HighlightContainer = tw.div`
  flex flex-col gap-6 items-center
`;

const HighlightCard = tw.div`
  w-full max-w-lg bg-white rounded-lg shadow-md p-4 border-2 border-blue-200
`;

function Highlight() {
  return (
    <Layout>
      <PageTitle>하이라이트 분석</PageTitle>
      <HighlightContainer>
        {highlights.map((hl, index) => (
          <HighlightCard key={index}>
            <h2 className="text-lg font-semibold text-gray-800 mb-2">
              {`구간: ${hl.start} ~ ${hl.end}`}
            </h2>
            <p className="text-gray-700 mb-1">요약: {hl.summary}</p>
            <p className="text-gray-700">감정: {hl.sentiment}</p>
          </HighlightCard>
        ))}
      </HighlightContainer>
    </Layout>
  );
}

export default Highlight;
