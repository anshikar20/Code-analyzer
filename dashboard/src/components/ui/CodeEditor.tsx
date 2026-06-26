import React from 'react';
import Editor from '@monaco-editor/react';

interface CodeEditorProps {
  value: string;
  onChange: (value: string | undefined) => void;
  language?: string;
  readOnly?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({ 
  value, 
  onChange, 
  language = 'python',
  readOnly = false 
}) => {
  const isDark = document.documentElement.classList.contains('dark');

  return (
    <div className="border border-[var(--border-color)] rounded-xl overflow-hidden h-[400px]">
      <Editor
        height="100%"
        language={language}
        theme={isDark ? 'vs-dark' : 'light'}
        value={value}
        onChange={onChange}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 14,
          padding: { top: 16, bottom: 16 },
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          cursorBlinking: 'smooth',
          fontFamily: 'ui-monospace, Consolas, "Liberation Mono", Menlo, monospace',
        }}
      />
    </div>
  );
};
