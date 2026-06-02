import React from "react";

export default function UserMessage({ content }) {
  return (
    <div className="user-msg-container">
      <div className="user-msg-bubble">
        {content}
      </div>
    </div>
  );
}