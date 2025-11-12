import React, { useEffect, useState } from "react";

function pad2(n: number) { return n.toString().padStart(2, "0"); }

type DigitProps = { value: number };

function FlipDigit({ value }: DigitProps) {
  const [curr, setCurr] = useState(value);
  const [next, setNext] = useState(value);
  const [flip, setFlip] = useState(false);

  useEffect(() => {
    if (value === curr) return;
    setNext(value);
    setFlip(true);
    const id = setTimeout(() => {
      setCurr(value);
      setFlip(false);
    }, 300);
    return () => clearTimeout(id);
  }, [value, curr]);

  return (
    <div className="relative w-[180px] h-[240px] mx-2" style={{ perspective: '1000px' }}>
      {/* Top Half */}
      <div className="absolute top-0 left-0 right-0 h-[calc(50%-1px)] overflow-hidden rounded-t-xl bg-gradient-to-b from-[#1a1a1a] to-[#0a0a0a]" 
           style={{ 
             boxShadow: 'inset 0 -2px 6px rgba(255,255,255,0.08), 0 6px 24px rgba(0,0,0,0.6)',
             borderBottom: '2px solid #000'
           }}>
        <div className="absolute left-0 right-0 flex items-center justify-center" 
             style={{ 
               top: '0',
               height: '240px',
               fontSize: '12rem',
               lineHeight: '240px',
               fontFamily: 'ui-monospace, monospace',
               fontWeight: 900,
               color: '#d9d9d9'
             }}>
          {curr}
        </div>
      </div>

      {/* Hinge Line */}
      <div className="absolute top-1/2 left-0 right-0 h-[2px] -mt-[1px] bg-black/80" 
           style={{ boxShadow: '0 1px 0 rgba(255,255,255,0.05)' }} />

      {/* Bottom Half */}
      <div className="absolute bottom-0 left-0 right-0 h-[calc(50%-1px)] overflow-hidden rounded-b-xl bg-gradient-to-b from-[#1a1a1a] to-[#0a0a0a]"
           style={{ 
             boxShadow: 'inset 0 2px 6px rgba(255,255,255,0.08), 0 6px 24px rgba(0,0,0,0.6)',
             borderTop: '2px solid #000'
           }}>
        <div className="absolute left-0 right-0 flex items-center justify-center" 
             style={{ 
               bottom: '0',
               height: '240px',
               fontSize: '12rem',
               lineHeight: '240px',
               fontFamily: 'ui-monospace, monospace',
               fontWeight: 900,
               color: '#d9d9d9'
             }}>
          {curr}
        </div>
      </div>

      {/* Flipping Top Half */}
      {flip && (
        <div 
          className="absolute top-0 left-0 right-0 h-[calc(50%-1px)] overflow-hidden rounded-t-xl bg-gradient-to-b from-[#1a1a1a] to-[#0a0a0a]"
          style={{ 
            transformOrigin: 'center bottom',
            animation: 'flipDown 0.3s ease-in forwards',
            backfaceVisibility: 'hidden',
            boxShadow: 'inset 0 -2px 6px rgba(255,255,255,0.08), 0 6px 24px rgba(0,0,0,0.6)',
            borderBottom: '2px solid #000'
          }}>
          <div className="absolute left-0 right-0 flex items-center justify-center" 
               style={{ 
                 top: '0',
                 height: '240px',
                 fontSize: '12rem',
                 lineHeight: '240px',
                 fontFamily: 'ui-monospace, monospace',
                 fontWeight: 900,
                 color: '#d9d9d9'
               }}>
            {curr}
          </div>
        </div>
      )}

      {/* Flipping Bottom Half */}
      {flip && (
        <div 
          className="absolute bottom-0 left-0 right-0 h-[calc(50%-1px)] overflow-hidden rounded-b-xl bg-gradient-to-b from-[#1a1a1a] to-[#0a0a0a]"
          style={{ 
            transformOrigin: 'center top',
            animation: 'flipUp 0.3s ease-out 0.3s forwards',
            transform: 'rotateX(90deg)',
            backfaceVisibility: 'hidden',
            boxShadow: 'inset 0 2px 6px rgba(255,255,255,0.08), 0 6px 24px rgba(0,0,0,0.6)',
            borderTop: '2px solid #000'
          }}>
          <div className="absolute left-0 right-0 flex items-center justify-center" 
               style={{ 
                 bottom: '0',
                 height: '240px',
                 fontSize: '12rem',
                 lineHeight: '240px',
                 fontFamily: 'ui-monospace, monospace',
                 fontWeight: 900,
                 color: '#d9d9d9'
               }}>
            {next}
          </div>
        </div>
      )}

      {/* Animations */}
      <style jsx>{`
        @keyframes flipDown {
          0% { transform: rotateX(0deg); }
          100% { transform: rotateX(-90deg); }
        }
        @keyframes flipUp {
          0% { transform: rotateX(90deg); }
          100% { transform: rotateX(0deg); }
        }
      `}</style>
    </div>
  );
}

export function FlipClock({ minutes, seconds }: { minutes: number; seconds: number }) {
  const mm = pad2(minutes);
  const ss = pad2(seconds);
  return (
    <div className="flex items-center justify-center gap-4">
      <FlipDigit value={Number(mm[0])} />
      <FlipDigit value={Number(mm[1])} />
      <div className="text-neutral-500 text-7xl font-black select-none" style={{ fontFamily: 'ui-monospace, monospace' }}>:</div>
      <FlipDigit value={Number(ss[0])} />
      <FlipDigit value={Number(ss[1])} />
    </div>
  );
}

export default FlipClock;





