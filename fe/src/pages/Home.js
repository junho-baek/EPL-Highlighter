import React, { useState, useEffect } from "react";
import tw from "tailwind-styled-components";
import Layout from "../components/Layout";
import { Link } from "react-router-dom";

const PageTitle = tw.h1`
  text-4xl font-bold text-blue-600 mb-6
`;

const ToggleButton = tw.button`
  px-6 py-2 rounded-full font-semibold transition-colors
  ${(p) =>
    p.$isActive
      ? "bg-blue-600 text-white"
      : "bg-gray-200 text-gray-700 hover:bg-gray-300"}
`;

const MatchListContainer = tw.div`
  grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4
  auto-rows-fr
`;

const MatchCard = ({ match }) => {
  const gameId =
    match.cheer_url.split("/").find((part) => /^\d{8}/.test(part)) ||
    match.cheer_url.split("/")[4];

  return (
    <Link
      to={`/live/${gameId}`}
      state={{ matchInfo: match }}
      className={`
        rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow
        border-2 cursor-pointer min-w-[280px] w-full
        ${
          match.status === "종료"
            ? "dark:bg-gray-800 dark:border-gray-700 bg-gray-50 border-gray-200"
            : "dark:bg-gray-800 dark:border-blue-900 bg-white border-blue-100"
        }
        hover:scale-105 transition-transform duration-200
      `}
    >
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {match.time}
        </span>
        <StatusBadge $status={match.status}>{match.status}</StatusBadge>
      </div>
      <div className="flex justify-between items-center">
        <TeamName>{match.home_team}</TeamName>
        <span className="text-gray-500 dark:text-gray-400 mx-2">VS</span>
        <TeamName>{match.away_team}</TeamName>
      </div>
    </Link>
  );
};

const PaginationButton = tw.button`
  px-4 py-2 rounded-md font-semibold transition-colors
  ${(p) =>
    p.$isDisabled
      ? "bg-gray-200 text-gray-400 cursor-not-allowed"
      : "bg-blue-600 text-white hover:bg-blue-700"}
`;

const DateSection = tw.div`
  mb-8 last:mb-0
`;

const DateTitle = tw.h2`
  text-xl font-semibold text-gray-700 mb-4
`;

const TeamName = tw.span`
  font-medium truncate max-w-[100px]
  dark:text-gray-200
`;

const StatusBadge = tw.span`
  text-sm px-2 py-1 rounded
  ${(p) =>
    p.$status === "종료"
      ? "bg-gray-200 dark:bg-gray-700"
      : "bg-green-200 dark:bg-green-800"}
`;

function Home() {
  const [filter, setFilter] = useState("EPL");
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const MATCHES_PER_PAGE = 3; // 페이지당 날짜 수

  useEffect(() => {
    const fetchSchedule = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `http://localhost:8000/schedules/${filter.toLowerCase()}`
        );
        if (!response.ok) throw new Error("Failed to fetch schedule");
        const data = await response.json();

        // 날짜별로 경기 그룹화
        const groupedMatches = groupMatchesByDate(data.matches);
        setMatches(groupedMatches);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSchedule();
  }, [filter]);

  // 날짜별로 경기 그룹화하는 함수
  const groupMatchesByDate = (matches) => {
    // 현재 날짜 기준으로 2일 전부터의 범위 계산
    const today = new Date();
    const twoDaysAgo = new Date(today);
    twoDaysAgo.setDate(today.getDate() - 2);

    // 2일 전부터의 모든 경기 필터링 (상태 구분 없이)
    const recentMatches = matches
      .filter((match) => {
        const matchDate = new Date(match.date);
        return matchDate >= twoDaysAgo;
      })
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    // 날짜별로 그룹화
    const grouped = recentMatches.reduce((acc, match) => {
      const matchDate = new Date(match.date);
      const formattedDate = `${
        matchDate.getMonth() + 1
      }월 ${matchDate.getDate()}일 (${getDayOfWeek(matchDate)})`;

      if (!acc[formattedDate]) {
        acc[formattedDate] = [];
      }
      acc[formattedDate].push(match);
      return acc;
    }, {});

    return grouped;
  };

  // 요일 변환 함수
  const getDayOfWeek = (date) => {
    const days = ["일", "월", "화", "수", "목", "금", "토"];
    return days[date.getDay()];
  };

  // 현재 페이지에 표시할 날짜들 가져오기
  const getCurrentPageDates = () => {
    const dates = Object.keys(matches).sort((a, b) => {
      const dateA = new Date(a.replace(/[월일()]/g, "").trim());
      const dateB = new Date(b.replace(/[월일()]/g, "").trim());
      return dateA - dateB;
    });

    const startIdx = currentPage * MATCHES_PER_PAGE;
    return dates.slice(startIdx, startIdx + MATCHES_PER_PAGE);
  };

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
    } catch (error) {
      console.error("Error searching YouTube:", error);
    }
  };

  if (loading)
    return (
      <Layout>
        <div className="text-center">Loading...</div>
      </Layout>
    );

  if (error)
    return (
      <Layout>
        <div className="text-center text-red-600">Error: {error}</div>
      </Layout>
    );

  const currentDates = getCurrentPageDates();
  const totalPages = Math.ceil(Object.keys(matches).length / MATCHES_PER_PAGE);

  return (
    <Layout>
      <PageTitle>경기 탐색</PageTitle>

      <div className="flex gap-4 mb-6">
        <ToggleButton
          $isActive={filter === "EPL"}
          onClick={() => {
            setFilter("EPL");
            setCurrentPage(0);
          }}
        >
          EPL
        </ToggleButton>
        <ToggleButton
          $isActive={filter === "NBA"}
          onClick={() => {
            setFilter("NBA");
            setCurrentPage(0);
          }}
        >
          NBA
        </ToggleButton>
      </div>

      {currentDates.map((date) => (
        <DateSection key={date}>
          <DateTitle>{date}</DateTitle>
          <MatchListContainer>
            {matches[date].map((match, index) => (
              <MatchCard key={index} match={match} />
            ))}
          </MatchListContainer>
        </DateSection>
      ))}

      {/* 페이지네이션 컨트롤 */}
      <div className="flex justify-center gap-4 mt-6">
        <PaginationButton
          onClick={() => setCurrentPage((prev) => prev - 1)}
          $isDisabled={currentPage === 0}
          disabled={currentPage === 0}
        >
          이전
        </PaginationButton>
        <span className="flex items-center">
          {currentPage + 1} / {totalPages}
        </span>
        <PaginationButton
          onClick={() => setCurrentPage((prev) => prev + 1)}
          $isDisabled={currentPage === totalPages - 1}
          disabled={currentPage === totalPages - 1}
        >
          다음
        </PaginationButton>
      </div>
    </Layout>
  );
}

export default Home;
