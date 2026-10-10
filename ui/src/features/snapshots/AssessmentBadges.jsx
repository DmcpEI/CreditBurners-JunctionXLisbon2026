import React from 'react';
import {assessmentFacts} from './presentation';

export default function AssessmentBadges({area,productIssuesOnly=false}) {
  const facts = assessmentFacts(area).filter(fact=>!productIssuesOnly || fact.tone==='mismatch');
  if (!facts.length) return null;
  return <span className="assessment-badges" aria-label="Stock and product assessment">{facts.map(fact => <span key={fact.label} className={`assessment-badge ${fact.tone}`}>{fact.label}</span>)}</span>;
}
