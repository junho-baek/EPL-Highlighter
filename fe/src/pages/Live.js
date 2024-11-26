import React, { useState, useEffect, useRef } from "react";
import tw from "tailwind-styled-components";
import Layout from "../components/Layout";
import { useParams, useLocation, Link } from "react-router-dom";
import { reactions } from "../mockData";
import { SPORTS } from "../constants/sports";
import { io } from "socket.io-client";
import { useTheme } from "../contexts/ThemeContext";

const PageTitle = tw.h1`
  text-4xl font-bold text-blue-600 mb-6
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

const MatchListContainer = tw.div`
  grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4
`;

const ReactionContainer = tw.div`
  flex flex-col gap-6 items-center w-full max-w-7xl mx-auto p-4
  lg:flex-row lg:items-start lg:justify-center
`;

const ReactionList = tw.div`
  w-full max-w-lg rounded-lg shadow-md p-4 border-2
  ${(p) =>
    p.$isDark ? "bg-gray-900 border-gray-600" : "bg-white border-blue-200"}
  lg:flex-1
`;

const ChatMessages = tw.div`
  w-full max-w-lg rounded-lg shadow-md p-4 border-2
  h-64 overflow-y-auto
  ${(p) =>
    p.$isDark ? "bg-gray-900 border-gray-600" : "bg-gray-100 border-blue-200"}
  lg:flex-1 lg:h-[500px]
`;

const ToggleButton = tw.button`
  px-6 py-2 rounded-full font-semibold transition-colors
  ${(p) =>
    p.$isActive
      ? "bg-blue-600 text-white"
      : "bg-gray-200 text-gray-700 hover:bg-gray-300"}
`;

function Live() {
  const { gameId } = useParams();
  const location = useLocation();
  const [filter, setFilter] = useState(SPORTS.EPL.id);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reactionData, setReactionData] = useState(null);
  const [messages, setMessages] = useState([]);
  const socket = useRef(null);
  const { isDark } = useTheme();

  useEffect(() => {
    if (!gameId) {
      const fetchTodayMatches = async () => {
        try {
          setLoading(true);
          const response = await fetch(
            `http://localhost:8000/schedules/${filter.toLowerCase()}`
          );
          if (!response.ok) throw new Error("Failed to fetch schedule");
          const data = await response.json();

          // 오늘 날짜의 경기만 필터링
          const today = new Date().toISOString().split("T")[0];
          const todayMatches = data.matches
            .filter((match) => match.date === today)
            .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

          setMatches(todayMatches);
        } catch (err) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };

      fetchTodayMatches();
    }
  }, [gameId, filter]);

  useEffect(() => {
    if (gameId) {
      const fetchReactionData = async () => {
        try {
          setLoading(true);
          const response = await fetch(
            `http://localhost:8000/reactions/${gameId}`
          );
          if (!response.ok) throw new Error("Failed to fetch reactions");
          const data = await response.json();
          setReactionData(data);
        } catch (err) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };

      fetchReactionData();
    }
  }, [gameId]);

  useEffect(() => {
    if (gameId) {
      console.log("Connecting to socket with gameId:", gameId);
      socket.current = io("http://localhost:8000", {
        transports: ["websocket"],
        upgrade: false,
      });

      socket.current.on("connect", () => {
        console.log("Socket connected");
        socket.current.emit("join", gameId);
      });

      socket.current.on("chat", (message) => {
        console.log("Received chat message:", message);
        setMessages((prev) => [...prev, message]);
      });

      socket.current.on("connect_error", (error) => {
        console.error("Socket connection error:", error);
      });

      return () => {
        console.log("Disconnecting socket");
        socket.current.disconnect();
      };
    }
  }, [gameId]);

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

  // gameId가 있으면 실시간 반응 페이지 표시
  if (gameId) {
    return (
      <Layout>
        <PageTitle>
          실시간 반응 -{" "}
          {location.state?.matchInfo
            ? `${location.state.matchInfo.time} ${location.state.matchInfo.home_team} vs ${location.state.matchInfo.away_team}`
            : "경기 정보 로딩중..."}
        </PageTitle>
        <ReactionContainer>
          <ReactionList $isDark={isDark}>
            <h2 className="text-lg font-semibold mb-3 dark:text-white">
              반응량
            </h2>
            {reactionData?.reactions && reactionData.reactions.length > 0 ? (
              <>
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  {new Date(reactionData.reactions[0].time).toLocaleString(
                    "ko-KR",
                    {
                      month: "numeric",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    }
                  )}
                  부터
                </div>
                {reactionData.reactions.map((reaction, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between mb-2"
                  >
                    <span className="text-sm text-gray-600 dark:text-gray-300">
                      {new Date(reaction.time).toLocaleTimeString("ko-KR", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                    <div className="flex-1 mx-4">
                      <div
                        className="bg-blue-500 dark:bg-blue-400 h-4 rounded"
                        style={{
                          width: `${Math.min(
                            100,
                            (reaction.count /
                              Math.max(
                                ...reactionData.reactions.map((r) => r.count)
                              )) *
                              100
                          )}%`,
                        }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                      {reaction.count}
                    </span>
                  </div>
                ))}
              </>
            ) : (
              <div className="text-center text-gray-500 dark:text-gray-400">
                아직 반응이 없습니다.
              </div>
            )}
          </ReactionList>
          <ChatMessages $isDark={isDark}>
            <h2 className="text-lg font-semibold mb-3 dark:text-white">
              메시지
            </h2>
            {messages.map((message, index) => (
              <p key={index} className="text-gray-700 dark:text-gray-200 mb-2">
                {`[${message.source_type === "naver" ? "네이버" : "유튜브"}] [${
                  message.author
                }] ${message.message}`}
              </p>
            ))}
          </ChatMessages>
        </ReactionContainer>
      </Layout>
    );
  }

  // gameId가 없으면 오늘의 경기 목록 표시
  return (
    <Layout>
      <PageTitle>오늘의 실시간 반응</PageTitle>

      <div className="flex gap-4 mb-6">
        {Object.values(SPORTS).map((sport) => (
          <ToggleButton
            key={sport.id}
            $isActive={filter === sport.id}
            onClick={() => setFilter(sport.id)}
            className={`${sport.color} text-white`}
          >
            {sport.name}
          </ToggleButton>
        ))}
      </div>

      <MatchListContainer>
        {matches.map((match, index) => (
          <Link
            key={index}
            to={`/live/${match.cheer_url
              .split("/")
              .find((part) => /^\d{8}/.test(part))}`}
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
        ))}
      </MatchListContainer>
    </Layout>
  );
}

export default Live;
