import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { PlatformApp } from "./App";
import "@tanim/ui/style.css";
import "./platform.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("The application root element is missing.");
}

createRoot(root).render(
  <StrictMode>
    <PlatformApp />
  </StrictMode>,
);
