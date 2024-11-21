import React, { useState } from "react";
import tw from "tailwind-styled-components";
import { matches } from "../mockData";
import Layout from "../components/Layout";

const PageTitle = tw.h1`
  text-4xl font-bold text-teal-600 mb-6
`;

const MatchListContainer = tw.div`
  flex flex-col gap-4 items-center
`;

const MatchButton = tw.button`
  w-full max-w-xl p-4 bg-teal-200 rounded-lg shadow-md text-lg font-semibold
  border-2 border-teal-400 transition duration-300 ease-in-out
  hover:bg-teal-300 hover:scale-105
  disabled:bg-gray-200 disabled:cursor-not-allowed disabled:border-gray-300
`;

const ToggleButton = tw.button`
  px-4 py-2 rounded-lg shadow-md font-semibold
  transition duration-300 ease-in-out
  ${(props) =>
    props.$isActive
      ? "bg-teal-500 text-white"
      : "bg-gray-200 text-gray-800 hover:bg-gray-300"}
`;

function Home() {
  const [filter, setFilter] = useState("EPL"); // 기본 필터는 "EPL"

  // 선택된 리그에 따라 경기 필터링
  const filteredMatches = matches.filter((match) => match.league === filter);

  const handleSearch = async (match) => {
    try {
      const response = await fetch(`http://localhost:8000/search_youtube`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          match_name: `${match.home_team} vs ${match.away_team}`,
        }),
      });
      const data = await response.json();
      console.log("Search Results:", data);
      // 검색 결과를 확인하거나 다른 페이지로 이동 가능
    } catch (error) {
      console.error("Error searching YouTube:", error);
    }
  };

  return (
    <Layout>
      <PageTitle>경기 탐색</PageTitle>

      {/* 토글 버튼 */}
      <div className="flex gap-4 mb-6">
        <ToggleButton
          $isActive={filter === "EPL"}
          onClick={() => setFilter("EPL")}
        >
          EPL
        </ToggleButton>
        <ToggleButton
          $isActive={filter === "NBA"}
          onClick={() => setFilter("NBA")}
        >
          NBA
        </ToggleButton>
      </div>

      {/* 필터링된 경기 목록 */}
      <MatchListContainer>
        {filteredMatches.map((match) => (
          <MatchButton key={match.id} onClick={() => handleSearch(match)}>
            {match.league}: {match.home_team} vs {match.away_team}
            <br />
            <span className="text-sm text-gray-600">
              {new Date(match.match_time).toLocaleString()}
            </span>
          </MatchButton>
        ))}
      </MatchListContainer>
    </Layout>
  );
}

export default Home;
