import type { ForgeConfig } from "@electron-forge/shared-types";
import { FusesPlugin } from "@electron-forge/plugin-fuses";
import { VitePlugin } from "@electron-forge/plugin-vite";
import { FuseV1Options, FuseVersion } from "@electron/fuses";

const config: ForgeConfig = {
  packagerConfig: {
    asar: true,
    name: "Maris",
    executableName: "Maris",
    extraResource: [
      ".maris-staging/python-runtime/alembic.ini",
      ".maris-staging/python-runtime/migrations",
      ".maris-staging/python-runtime/src"
    ],
    ...(process.env.MARIS_ELECTRON_CACHE ? { download: { cacheRoot: process.env.MARIS_ELECTRON_CACHE } } : {})
  },
  makers: [],
  plugins: [
    new VitePlugin({
      build: [
        { entry: "electron/main/main.ts", config: "vite.main.config.ts", target: "main" },
        { entry: "electron/preload/preload.ts", config: "vite.preload.config.ts", target: "preload" },
        { entry: "electron/preload/companion.ts", config: "vite.preload.config.ts", target: "preload" }
      ],
      renderer: [
        { name: "main_window", config: "vite.renderer.config.ts" },
        { name: "companion_window", config: "vite.companion.config.ts" }
      ]
    }),
    new FusesPlugin({
      version: FuseVersion.V1,
      [FuseV1Options.RunAsNode]: false,
      [FuseV1Options.EnableCookieEncryption]: true,
      [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,
      [FuseV1Options.EnableNodeCliInspectArguments]: false,
      [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: true,
      [FuseV1Options.OnlyLoadAppFromAsar]: true
    })
  ]
};

export default config;
