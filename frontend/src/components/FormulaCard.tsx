import { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { FormulaExplanation } from "../api";

interface FormulaCardProps {
  formulas: FormulaExplanation[];
}

function FormulaCard({ formulas }: FormulaCardProps) {
  if (!formulas.length) {
    return <div className="empty-state">论文中暂未识别到关键公式。</div>;
  }

  return (
    <div className="formula-list">
      {formulas.map((formula) => (
        <article className="formula-item" key={`${formula.formula}-${formula.location_hint}`}>
          <RenderedFormula value={formula.formula} />
          <span className="location">{formula.location_hint}</span>
          <MathText as="p" value={formula.plain_explanation} />
          <MathText as="p" className="muted" value={formula.role_in_method} />
          <div className="variable-grid">
            {Object.entries(formula.variables).map(([name, explanation]) => (
              <div key={name}>
                <RenderedFormula value={name} displayMode={false} compact />
                <MathText as="span" value={explanation} />
              </div>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

function RenderedFormula({
  value,
  displayMode = true,
  compact = false
}: {
  value: string;
  displayMode?: boolean;
  compact?: boolean;
}) {
  const rendered = useMemo(() => renderFormula(value, displayMode), [displayMode, value]);

  return (
    <div className={compact ? "formula-display compact" : "formula-display"}>
      {rendered.html ? (
        <div
          className={displayMode ? "formula-render" : "formula-inline-render"}
          dangerouslySetInnerHTML={{ __html: rendered.html }}
        />
      ) : (
        <code className="formula-source fallback">{rendered.source || value}</code>
      )}
    </div>
  );
}

function MathText({
  value,
  as = "span",
  className
}: {
  value: string;
  as?: "p" | "span";
  className?: string;
}) {
  const parts = useMemo(() => splitMathText(value), [value]);
  const Tag = as;

  return (
    <Tag className={className}>
      {parts.map((part, index) =>
        part.kind === "math" ? (
          <RenderedInlineMath value={part.value} key={`${part.value}-${index}`} />
        ) : (
          <span key={`${part.value}-${index}`}>{part.value}</span>
        )
      )}
    </Tag>
  );
}

function RenderedInlineMath({ value }: { value: string }) {
  const rendered = useMemo(() => renderFormula(value, false), [value]);
  if (!rendered.html) {
    return <code className="inline-formula-fallback">{rendered.source || value}</code>;
  }
  return <span className="inline-math" dangerouslySetInnerHTML={{ __html: rendered.html }} />;
}

function renderFormula(value: string, displayMode: boolean): { html: string; source: string } {
  const source = normalizeLatex(value);
  if (!source) return { html: "", source };

  try {
    return {
      html: katex.renderToString(source, {
        displayMode,
        throwOnError: false,
        strict: "ignore",
        trust: false
      }),
      source
    };
  } catch {
    return { html: "", source };
  }
}

function normalizeLatex(value: string): string {
  let source = value.trim();
  source = source.replace(/^```(?:latex|tex|math)?/i, "").replace(/```$/, "").trim();
  source = source.replace(/\\label\{[^{}]*\}/g, "");
  source = source.replace(/^\\begin\{equation\*?\}/, "").replace(/\\end\{equation\*?\}$/, "");
  source = source.replace(/^\\begin\{align\*?\}/, "\\begin{aligned}").replace(/\\end\{align\*?\}$/, "\\end{aligned}");
  source = source.replace(/^\\begin\{gather\*?\}/, "\\begin{aligned}").replace(/\\end\{gather\*?\}$/, "\\end{aligned}");
  source = source.replace(/^\\begin\{split\*?\}/, "\\begin{aligned}").replace(/\\end\{split\*?\}$/, "\\end{aligned}");
  if (source.startsWith("$$") && source.endsWith("$$")) {
    source = source.slice(2, -2);
  } else if (source.startsWith("\\[") && source.endsWith("\\]")) {
    source = source.slice(2, -2);
  } else if (source.startsWith("\\(") && source.endsWith("\\)")) {
    source = source.slice(2, -2);
  } else if (source.startsWith("$") && source.endsWith("$")) {
    source = source.slice(1, -1);
  }
  return source.trim();
}

function splitMathText(value: string): Array<{ kind: "text" | "math"; value: string }> {
  const parts: Array<{ kind: "text" | "math"; value: string }> = [];
  const pattern = /(\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|\$\$[\s\S]+?\$\$|\$[^$\n]+\$)/g;
  let lastIndex = 0;
  for (const match of value.matchAll(pattern)) {
    const matchText = match[0];
    const index = match.index ?? 0;
    if (index > lastIndex) {
      parts.push({ kind: "text", value: value.slice(lastIndex, index) });
    }
    parts.push({ kind: "math", value: unwrapInlineMath(matchText) });
    lastIndex = index + matchText.length;
  }
  if (lastIndex < value.length) {
    parts.push({ kind: "text", value: value.slice(lastIndex) });
  }
  return parts.length ? parts : [{ kind: "text", value }];
}

function unwrapInlineMath(value: string): string {
  const source = value.trim();
  if (source.startsWith("$$") && source.endsWith("$$")) return source.slice(2, -2);
  if (source.startsWith("$") && source.endsWith("$")) return source.slice(1, -1);
  if (source.startsWith("\\[") && source.endsWith("\\]")) return source.slice(2, -2);
  if (source.startsWith("\\(") && source.endsWith("\\)")) return source.slice(2, -2);
  return source;
}

export default FormulaCard;
