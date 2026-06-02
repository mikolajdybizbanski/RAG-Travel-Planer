import React from "react";
import { parseTimeBlocks, fmtMarkdown } from "../utils";
import ItineraryCards from "./ItineraryCards";

export default function AiMessage({ content, loading }) {
  const days = loading ? [] : parseTimeBlocks(content);
  
  // Find the intro text before the first "DAY X" marker to prevent doubling
  const firstDayMatch = /(?:---\s*)?DAY\s+\d+/i.exec(content);
  const introText = firstDayMatch ? content.slice(0, firstDayMatch.index).trim() : content;

  return (
    <div className="ai-msg-container">
      <div className="ai-msg-avatar">✦</div>
      <div className="ai-msg-bubble">
        {loading ? (
          <div className="loading-dots">
            <div className="loading-dot" />
            <div className="loading-dot" />
            <div className="loading-dot" />
          </div>
        ) : days.length > 0 ? (
          <>
            {introText && (
              <div 
                dangerouslySetInnerHTML={{__html: fmtMarkdown(introText)}} 
                style={{marginBottom: 4}}
              />
            )}
            <ItineraryCards days={days} />
          </>
        ) : (
          <div dangerouslySetInnerHTML={{__html: fmtMarkdown(content)}} />
        )}
      </div>
    </div>
  );
}