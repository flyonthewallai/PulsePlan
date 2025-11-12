type Props = { active: boolean; width?: number; height?: number };

export default function PulseTrace({ active, width = 32, height = 32 }: Props) {
  // ECG-like path; tweak points to match your logo silhouette
  const d = `
    M 4 ${height * 0.5}
    L 8 ${height * 0.5}
    L 10 ${height * 0.5 - 4}
    L 12 ${height * 0.5 + 4}
    L 14 ${height * 0.5 - 6}
    L 18 ${height * 0.5 + 6}
    L 22 ${height * 0.5 - 3}
    L 24 ${height * 0.5 - 3}
    L 26 ${height * 0.5 + 4}
    L 28 ${height * 0.5 - 8}
    L 30 ${height * 0.5 + 6}
    L 32 ${height * 0.5}
    L ${width - 4} ${height * 0.5}
  `;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      style={{ display: "block" }}
    >
      <defs>
        {/* Blue gradient for the core stroke */}
        <linearGradient id="pulseGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#6bb6ff" />
          <stop offset="60%" stopColor="#3a8fff" />
          <stop offset="100%" stopColor="#1778ff" />
        </linearGradient>

        {/* A mask that reveals only the marching "head" for extra sparkle */}
        {active && (
          <linearGradient id="headMask" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="white" stopOpacity="0" />
            <stop offset="50%" stopColor="white" stopOpacity="1" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>
        )}
      </defs>

      {/* Core line */}
      <path
        d={d}
        stroke="url(#pulseGradient)"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{
          strokeDasharray: active ? 200 : "none",
          strokeDashoffset: active ? 0 : "none",
          transition: active ? "none" : "stroke-dashoffset 400ms ease",
          animation: active ? "trace 1.8s linear infinite" : "none",
        }}
      />

      {/* Bright traveling head - only when active */}
      {active && (
        <g mask="url(#maskHead)">
          <path
            d={d}
            stroke="#cfe5ff"
            strokeWidth="3"
            fill="none"
            style={{
              strokeDasharray: 20,
              strokeDashoffset: 0,
              animation: "spark 0.9s linear infinite",
              mixBlendMode: "screen",
            }}
          />
        </g>
      )}

      {/* Inline keyframes for portability */}
      <style>{`
        @keyframes trace {
          0%   { stroke-dashoffset: 200; }
          100% { stroke-dashoffset: 0; }
        }
        @keyframes spark {
          0%   { stroke-dashoffset: 40; }
          100% { stroke-dashoffset: -20; }
        }
      `}</style>

      {/* Mask definition (placed after <style> for clarity) - only when active */}
      {active && (
        <mask id="maskHead">
          <rect width={width} height={height} fill="black" />
          <rect width={width} height={height} fill="url(#headMask)">
            <animate attributeName="x" from={`-${width}`} to={`${width}`} dur="1.2s" repeatCount="indefinite" />
          </rect>
        </mask>
      )}
    </svg>
  );
}
