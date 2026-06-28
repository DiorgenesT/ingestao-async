import { useState } from "react";
import { estaAutenticado } from "./services/api";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { SubmitPage } from "./pages/SubmitPage";

type Tela = "login" | "dashboard" | "submit";

function telaInicial(): Tela {
  return estaAutenticado() ? "dashboard" : "login";
}

export default function App() {
  const [tela, setTela] = useState<Tela>(telaInicial);

  if (tela === "login") {
    return <LoginPage onAutenticado={() => setTela("dashboard")} />;
  }

  if (tela === "submit") {
    return <SubmitPage onConcluido={() => setTela("dashboard")} />;
  }

  return (
    <DashboardPage
      onLogout={() => setTela("login")}
      onNovoJob={() => setTela("submit")}
    />
  );
}
