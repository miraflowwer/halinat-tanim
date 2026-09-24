import type { SessionResponse } from "@tanim/types";

export function navigate(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export type RouteDecision =
  | { kind: "render" }
  | { kind: "auth" }
  | { kind: "redirect"; path: string };

export function resolveProtectedRoute(
  path: string,
  session: SessionResponse,
  replayDemo: boolean,
): RouteDecision {
  if (!session.authenticated) return { kind: "auth" };
  if (!session.user.has_completed_demo && path !== "/demo") {
    return { kind: "redirect", path: "/demo" };
  }
  if (path === "/demo" && session.user.has_completed_demo && !replayDemo) {
    return { kind: "redirect", path: "/dashboard" };
  }
  if (path === "/cooperative" && session.user.role !== "cooperative") {
    return { kind: "redirect", path: "/dashboard" };
  }
  const knownPath = path === "/demo"
    || path === "/dashboard"
    || path === "/cooperative"
    || path === "/plans"
    || path === "/plans/new"
    || path === "/settings"
    || path === "/explore"
    || /^\/plans\/\d+(\/edit)?$/.test(path);
  return knownPath ? { kind: "render" } : { kind: "redirect", path: "/dashboard" };
}
