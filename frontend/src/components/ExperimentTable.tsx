import { DocumentAnalysisMeta, EntityTables, ExperimentSettings } from "../api";

interface ExperimentTableProps {
  settings: ExperimentSettings;
  tables: EntityTables;
  view: "settings" | "tables";
  metadata?: DocumentAnalysisMeta;
}

function ExperimentTable({ settings, tables, view, metadata }: ExperimentTableProps) {
  const labels = labelsForDomain(metadata?.domain);

  if (view === "settings") {
    return (
      <div className="experiment-grid">
        <InfoBlock title={labels.datasets} values={settings.datasets} />
        <InfoBlock title={labels.models} values={settings.models} />
        <InfoBlock title={labels.baselines} values={settings.baselines} />
        <InfoBlock title={labels.metrics} values={settings.metrics} />
        <section className="summary-block wide">
          <h3>{labels.trainingDetails}</h3>
          <p>{settings.training_details}</p>
        </section>
        <section className="summary-block">
          <h3>{labels.hardware}</h3>
          <p>{settings.hardware}</p>
        </section>
        <section className="summary-block">
          <h3>{labels.evaluationProtocol}</h3>
          <p>{settings.evaluation_protocol}</p>
        </section>
        <section className="summary-block wide">
          <h3>{labels.parameters}</h3>
          <div className="kv-grid">
            {(Object.entries(settings.hyperparameters).length
              ? Object.entries(settings.hyperparameters)
              : [["未识别", "不适用"]]
            ).map(([key, value]) => (
              <div key={key}>
                <span>{key}</span>
                <strong>{String(value)}</strong>
              </div>
            ))}
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="table-stack">
      <DataTable
        title={labels.datasets}
        headers={["名称", "用途", "组织方式"]}
        rows={tables.datasets.map((item) => [item.name, item.usage, item.split])}
      />
      <DataTable
        title={labels.models}
        headers={["名称", "角色", "说明"]}
        rows={tables.models.map((item) => [item.name, item.role, item.description])}
      />
      <DataTable
        title={labels.baselines}
        headers={["名称", "比较理由"]}
        rows={tables.baselines.map((item) => [item.name, item.reason])}
      />
    </div>
  );
}

function InfoBlock({ title, values }: { title: string; values: string[] }) {
  return (
    <section className="summary-block">
      <h3>{title}</h3>
      <div className="tag-list">
        {(values.length ? values : ["未识别"]).map((value) => (
          <span key={value}>{value}</span>
        ))}
      </div>
    </section>
  );
}

function DataTable({ title, headers, rows }: { title: string; headers: string[]; rows: string[][] }) {
  const renderedRows = rows.length ? rows : [headers.map((_, index) => (index === 0 ? "未识别" : "不适用"))];

  return (
    <section className="table-wrap">
      <h3>{title}</h3>
      <table>
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {renderedRows.map((row, rowIndex) => (
            <tr key={`${title}-${rowIndex}`}>
              {row.map((cell, cellIndex) => (
                <td key={`${title}-${rowIndex}-${cellIndex}`}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function labelsForDomain(domain?: string) {
  if (domain === "physics") {
    return {
      datasets: "样品 / 观测数据",
      models: "理论 / 拟合模型",
      baselines: "对照 / 先前测量",
      metrics: "观测量 / 不确定度",
      trainingDetails: "实验 / 仿真流程",
      hardware: "仪器 / 设施",
      evaluationProtocol: "验证协议",
      parameters: "物理参数"
    };
  }

  if (domain === "mathematics") {
    return {
      datasets: "例子 / 构造",
      models: "定义 / 定理",
      baselines: "已有结果",
      metrics: "验证标准",
      trainingDetails: "证明流程",
      hardware: "工具",
      evaluationProtocol: "核查路径",
      parameters: "假设 / 条件"
    };
  }

  if (domain === "non_academic") {
    return {
      datasets: "可用材料",
      models: "识别对象",
      baselines: "比较项",
      metrics: "检查项",
      trainingDetails: "诊断说明",
      hardware: "文件状态",
      evaluationProtocol: "下一步",
      parameters: "提取信息"
    };
  }

  return {
    datasets: "数据 / 材料",
    models: "模型 / 方法",
    baselines: "对照 / 比较对象",
    metrics: "指标 / 证据",
    trainingDetails: "流程细节",
    hardware: "环境 / 仪器",
    evaluationProtocol: "验证协议",
    parameters: "参数"
  };
}

export default ExperimentTable;
