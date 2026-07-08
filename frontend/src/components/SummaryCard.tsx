import { StructuredSummary } from "../api";

interface SummaryCardProps {
  summary: StructuredSummary;
}

function SummaryCard({ summary }: SummaryCardProps) {
  return (
    <div className="summary-layout">
      <section className="summary-block wide">
        <h3>研究背景与问题</h3>
        <p>{summary.background}</p>
        <p>{summary.problem}</p>
      </section>
      <section className="summary-block">
        <h3>动机</h3>
        <p>{summary.motivation}</p>
      </section>
      <section className="summary-block">
        <h3>方法总览</h3>
        <p>{summary.method_overview}</p>
      </section>
      <section className="summary-block">
        <h3>实验概览</h3>
        <p>{summary.experiment_overview}</p>
      </section>
      <section className="summary-block">
        <h3>结论与局限</h3>
        <p>{summary.conclusion}</p>
        <p>{summary.limitations}</p>
      </section>
      <section className="summary-block wide">
        <h3>主要贡献</h3>
        <ul className="clean-list">
          {summary.contribution.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
      <section className="summary-block wide">
        <h3>建议阅读顺序</h3>
        <div className="reading-order">
          {summary.suggested_reading_order.map((item, index) => (
            <span key={`${item}-${index}`}>{item}</span>
          ))}
        </div>
      </section>
    </div>
  );
}

export default SummaryCard;

