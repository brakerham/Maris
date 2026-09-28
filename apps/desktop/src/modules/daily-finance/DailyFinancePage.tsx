export default function DailyFinancePage() {
  return (
    <section aria-labelledby="daily-title">
      <span className="demo-badge">演示占位 · 未连接财务数据</span>
      <h1 id="daily-title">日常财务</h1>
      <p>这里将在 P4-C 接入驾驶舱、账本与确认流程。本页面不会生成余额、建议或写入账目。</p>
      <div className="placeholder-grid" aria-label="占位卡片">
        <article><h2>本月概览</h2><p>等待模块数据</p></article>
        <article><h2>近期记录</h2><p>等待模块数据</p></article>
      </div>
    </section>
  );
}
