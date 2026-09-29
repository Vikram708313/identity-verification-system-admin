import { useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import People from "./pages/People";
import Documents from "./pages/Documents";
import Verification from "./pages/Verification";
import Profile from "./pages/Profile";

import ProtectedRoute from "./components/ProtectedRoute";


function App() {
  useEffect(() => {
    const appearance =
      localStorage.getItem("appearance") || "light";

    const root = document.documentElement;

    if (appearance === "dark") {
      root.setAttribute("data-theme", "dark");
    } else if (appearance === "system") {
      const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)"
      ).matches;

      root.setAttribute(
        "data-theme",
        prefersDark ? "dark" : "light"
      );
    } else {
      root.setAttribute("data-theme", "light");
    }
  }, []);

  return (
    <BrowserRouter>
      <Routes>

        <Route
          path="/"
          element={<Login />}
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/people"
          element={
            <ProtectedRoute>
              <People />
            </ProtectedRoute>
          }
        />

        <Route
          path="/documents"
          element={
            <ProtectedRoute>
              <Documents />
            </ProtectedRoute>
          }
        />

        <Route
          path="/verification"
          element={
            <ProtectedRoute>
              <Verification />
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;