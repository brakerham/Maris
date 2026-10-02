import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { dailyFinanceContribution } from "../modules/daily-finance/contribution";
import { compileRegistry } from "../modules/registry";
import { DesktopApp, rendererRootOptions } from "./module-routes";
import "./styles.css";

const compiled = compileRegistry([dailyFinanceContribution]);
export const desktopRoot = createRoot(document.getElementById("root")!, rendererRootOptions);
desktopRoot.render(<StrictMode><DesktopApp registry={compiled} /></StrictMode>);
