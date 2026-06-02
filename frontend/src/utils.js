export function parseTimeBlocks(content) {
  const dayRe = /(?:---\s*)?DAY\s+(\d+)[^\n]*\n([\s\S]*?)(?=(?:---\s*)?DAY\s+\d+|$)/gi;
  const timeRe = /\*{0,2}(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*[-–]\s*(\d{1,2}:\d{2}\s*(?:AM|PM)?)\*{0,2}[^|]*\|\s*\*{0,2}([^*\n(]+)\*{0,2}(?:[^\n:]*:?\s*([^\n]*))?/gi;
  const days = [];
  let dm;
  while ((dm = dayRe.exec(content)) !== null) {
    const entries = [];
    let tm;
    while ((tm = timeRe.exec(dm[2])) !== null) {
      entries.push({ 
        start: tm[1].trim(), 
        end: tm[2].trim(), 
        name: tm[3].replace(/\*+/g,"").trim(), 
        note: (tm[4]||"").trim() 
      });
    }
    if (entries.length) days.push({ day: parseInt(dm[1]), entries });
  }
  return days;
}

export function fmtMarkdown(t) {
  return t.replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>")
          .replace(/\*([^*]+)\*/g,"<em>$1</em>")
          .replace(/^#{1,3}\s+(.+)/gm,"<strong>$1</strong>")
          .replace(/\n/g,"<br/>");
}