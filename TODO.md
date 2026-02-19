# Professional UI Upgrade — antd + TailwindCSS + Recharts

## Steps

- [x] Read and understand all existing files
- [x] Create plan and get user approval

### Installation & Config

- [ ] Update `frontend/package.json` — add antd, @ant-design/icons, recharts, tailwindcss, autoprefixer, postcss; remove chart.js, react-chartjs-2
- [ ] Create `frontend/tailwind.config.js`
- [ ] Create `frontend/postcss.config.js`
- [ ] Run `pnpm install` in `frontend/`

### Source Files

- [ ] Rewrite `frontend/src/index.css` — Tailwind directives + keep JSON highlight classes
- [ ] Rewrite `frontend/src/main.tsx` — remove Chart.js registrations
- [ ] Rewrite `frontend/src/utils/chartConfig.ts` — Recharts data format
- [ ] Rewrite `frontend/src/components/ChartCard.tsx` — Recharts + antd Card
- [ ] Rewrite `frontend/src/components/DataTable.tsx` — antd Table with Tags, Tooltip, pagination
- [ ] Rewrite `frontend/src/components/AIAnalysisCard.tsx` — antd Card + Tabs (Prompt / Response)
- [ ] Rewrite `frontend/src/App.tsx` — antd Layout, ConfigProvider dark/light toggle, stat cards, chart grid

### Verification

- [ ] Run `pnpm dev` and verify in browser
