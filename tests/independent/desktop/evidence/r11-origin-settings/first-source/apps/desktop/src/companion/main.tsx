import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

function Companion() {
  const [state, setState] = useState("offline");
  const [appearance, setAppearance] = useState("daily_finance");
  useEffect(() => { void window.companion.getState().then((value) => { setState(value.state); setAppearance(value.appearanceId); }); }, []);
  return <button type="button" data-appearance={appearance} aria-label={`毛毛，状态 ${state}，打开 Maris 主窗口`} onClick={() => void window.companion.openMain()}>毛毛<br /><small>{state}</small></button>;
}
createRoot(document.getElementById("root")!).render(<Companion />);
