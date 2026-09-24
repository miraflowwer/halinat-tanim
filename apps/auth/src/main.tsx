import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AuthApp } from "./App";
import "@tanim/ui/style.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("The application root element is missing.");
}

createRoot(root).render(
  <StrictMode>
    <AuthApp />
  </StrictMode>,
);
