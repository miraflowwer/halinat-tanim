import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { PlaceholderPage } from "@tanim/ui";
import "@tanim/ui/style.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("The application root element is missing.");
}

createRoot(root).render(
  <StrictMode>
    <PlaceholderPage surface="auth" />
  </StrictMode>,
);
