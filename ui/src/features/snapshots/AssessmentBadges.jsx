import React from 'react';
import {assessmentFacts} from './presentation';

export default function AssessmentBadges({area}) {
  const facts = assessmentFacts(area);
  if (!facts.length) return null;
  return <span className="assessment-badges" aria-label="Stock and product assessment">{facts.map(fact => <span key={fact.label} className={`assessment-badge ${fact.tone}`}>{fact.label}</span>)}</span>;
}
