import React from 'react';
import { Text, View, StyleSheet } from 'react-native';

interface MarkdownTextProps {
  children: string;
  style?: any;
}

interface TextSegment {
  text: string;
  bold?: boolean;
  italic?: boolean;
  code?: boolean;
}

const parseMarkdown = (text: string): TextSegment[] => {
  const segments: TextSegment[] = [];
  
  // Process text sequentially to handle overlapping patterns correctly
  let remainingText = text;
  
  while (remainingText.length > 0) {
    // Check for bold first (highest priority)
    const boldMatch = remainingText.match(/\*\*(.+?)\*\*/);
    if (boldMatch && boldMatch.index !== undefined) {
      // Add text before the match
      if (boldMatch.index > 0) {
        segments.push({ text: remainingText.slice(0, boldMatch.index) });
      }
      // Add the bold text
      segments.push({ text: boldMatch[1], bold: true });
      // Continue with remaining text
      remainingText = remainingText.slice(boldMatch.index + boldMatch[0].length);
      continue;
    }
    
    // Check for code blocks
    const codeMatch = remainingText.match(/`(.+?)`/);
    if (codeMatch && codeMatch.index !== undefined) {
      // Add text before the match
      if (codeMatch.index > 0) {
        segments.push({ text: remainingText.slice(0, codeMatch.index) });
      }
      // Add the code text
      segments.push({ text: codeMatch[1], code: true });
      // Continue with remaining text
      remainingText = remainingText.slice(codeMatch.index + codeMatch[0].length);
      continue;
    }
    
    // Check for italic (lowest priority to avoid conflicts with bold)
    const italicMatch = remainingText.match(/\*(.+?)\*/);
    if (italicMatch && italicMatch.index !== undefined) {
      // Add text before the match
      if (italicMatch.index > 0) {
        segments.push({ text: remainingText.slice(0, italicMatch.index) });
      }
      // Add the italic text
      segments.push({ text: italicMatch[1], italic: true });
      // Continue with remaining text
      remainingText = remainingText.slice(italicMatch.index + italicMatch[0].length);
      continue;
    }
    
    // No more matches, add remaining text
    segments.push({ text: remainingText });
    break;
  }
  
  // Filter out empty segments
  return segments.filter(segment => segment.text.length > 0);
};

export const MarkdownText: React.FC<MarkdownTextProps> = ({ children, style }) => {
  const segments = parseMarkdown(children);
  
  return (
    <Text style={style}>
      {segments.map((segment, index) => (
        <Text
          key={index}
          style={[
            segment.bold && styles.bold,
            segment.italic && styles.italic,
            segment.code && styles.code,
          ]}
        >
          {segment.text}
        </Text>
      ))}
    </Text>
  );
};

const styles = StyleSheet.create({
  bold: {
    fontWeight: 'bold',
  },
  italic: {
    fontStyle: 'italic',
  },
  code: {
    fontFamily: 'monospace',
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderRadius: 3,
  },
}); 