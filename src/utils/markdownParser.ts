// Utility for parsing and cleaning AI markdown responses

export const cleanMarkdownText = (text: string): string => {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1') // Remove bold
    .replace(/\*(.+?)\*/g, '$1') // Remove italic
    .replace(/`(.+?)`/g, '$1') // Remove code blocks
    .replace(/^\d+\.\s*/, '') // Remove leading numbers
    .replace(/^[-*•]\s*/, '') // Remove bullet points
    .replace(/^#+\s*/, '') // Remove headers
    .replace(/\s+/g, ' ') // Normalize whitespace
    .trim();
};

export const parseMarkdownResponse = (response: string): string => {
  // Split response into lines and clean them
  const lines = response
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0);
  
  const cleanedLines: string[] = [];
  
  for (const line of lines) {
    // Skip markdown headers and separators
    if (line.startsWith('#') || line.startsWith('---') || line.startsWith('===')) {
      continue;
    }
    
    // Clean the line and add if substantial
    const cleanedLine = cleanMarkdownText(line);
    if (cleanedLine.length > 10) {
      cleanedLines.push(cleanedLine);
    }
  }
  
  // Join lines with proper spacing
  return cleanedLines.join('\n\n');
};

// Function to format AI response for better readability
export const formatAIResponse = (response: string): string => {
  // First clean the markdown
  let formatted = parseMarkdownResponse(response);
  
  // If the response is too short or formatting failed, return cleaned original
  if (formatted.length < 50) {
    return cleanMarkdownText(response);
  }
  
  return formatted;
}; 