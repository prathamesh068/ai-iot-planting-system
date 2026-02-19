/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SHEET_ID: string;
  readonly VITE_SHEET_NAME: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
