import { FormulaExplanation } from "../api";

interface FormulaCardProps {
  formulas: FormulaExplanation[];
}

function FormulaCard({ formulas }: FormulaCardProps) {
  return (
    <div className="formula-list">
      {formulas.map((formula) => (
        <article className="formula-item" key={`${formula.formula}-${formula.location_hint}`}>
          <code>{formula.formula}</code>
          <span className="location">{formula.location_hint}</span>
          <p>{formula.plain_explanation}</p>
          <p className="muted">{formula.role_in_method}</p>
          <div className="variable-grid">
            {Object.entries(formula.variables).map(([name, explanation]) => (
              <div key={name}>
                <strong>{name}</strong>
                <span>{explanation}</span>
              </div>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

export default FormulaCard;

