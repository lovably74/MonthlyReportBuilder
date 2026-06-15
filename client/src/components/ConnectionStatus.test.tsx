import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConnectionStatus, useIsDisconnected } from "./ConnectionStatus";
import { DisconnectedBanner } from "./DisconnectedBanner";
import { useConnectionStore } from "@/stores/connectionStore";
import React from "react";

// Helper to set store state directly
function setConnectionStatus(status: "connected" | "disconnected" | "connecting") {
  useConnectionStore.setState({ status });
}

describe("ConnectionStatus", () => {
  beforeEach(() => {
    // Reset to default state
    useConnectionStore.setState({ status: "disconnected" });
  });

  it('connected 상태일 때 "서버 연결됨"을 표시한다', () => {
    setConnectionStatus("connected");
    render(<ConnectionStatus />);
    expect(screen.getByText("서버 연결됨")).toBeInTheDocument();
  });

  it('connecting 상태일 때 "연결 중..."을 표시한다', () => {
    setConnectionStatus("connecting");
    render(<ConnectionStatus />);
    expect(screen.getByText("연결 중...")).toBeInTheDocument();
  });

  it('disconnected 상태일 때 "서버 연결 끊김"을 표시한다', () => {
    setConnectionStatus("disconnected");
    render(<ConnectionStatus />);
    expect(screen.getByText("서버 연결 끊김")).toBeInTheDocument();
  });

  it("접근성 라벨을 포함한다", () => {
    setConnectionStatus("connected");
    render(<ConnectionStatus />);
    expect(screen.getByLabelText("서버 연결 상태: 서버 연결됨")).toBeInTheDocument();
  });
});

describe("DisconnectedBanner", () => {
  beforeEach(() => {
    useConnectionStore.setState({ status: "disconnected" });
  });

  it("disconnected 상태일 때 경고 메시지를 표시한다", () => {
    setConnectionStatus("disconnected");
    render(<DisconnectedBanner />);
    expect(
      screen.getByText("서버와 연결이 끊어졌습니다. 읽기 전용 모드로 동작합니다.")
    ).toBeInTheDocument();
  });

  it('role="alert"을 가진다', () => {
    setConnectionStatus("disconnected");
    render(<DisconnectedBanner />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("connected 상태일 때 렌더링하지 않는다", () => {
    setConnectionStatus("connected");
    render(<DisconnectedBanner />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("connecting 상태일 때 렌더링하지 않는다", () => {
    setConnectionStatus("connecting");
    render(<DisconnectedBanner />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("useIsDisconnected", () => {
  function TestComponent() {
    const isDisconnected = useIsDisconnected();
    return <div data-testid="result">{isDisconnected ? "true" : "false"}</div>;
  }

  it("disconnected 상태일 때 true를 반환한다", () => {
    setConnectionStatus("disconnected");
    render(<TestComponent />);
    expect(screen.getByTestId("result").textContent).toBe("true");
  });

  it("connected 상태일 때 false를 반환한다", () => {
    setConnectionStatus("connected");
    render(<TestComponent />);
    expect(screen.getByTestId("result").textContent).toBe("false");
  });
});
